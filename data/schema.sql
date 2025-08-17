-- SQLite Database Schema for Trading Bot v0.2
-- Architecture: Temporary raw data + Persistent LLM analysis results

-- Critical settings to prevent failures
PRAGMA journal_mode = WAL;        -- Allows reading while writing (no "database locked" errors)
PRAGMA busy_timeout = 5000;       -- Wait 5 seconds instead of failing instantly when busy
PRAGMA synchronous = NORMAL;      -- Fast writes for GitHub Actions (vs painfully slow default)

-- ===============================
-- RAW DATA TABLES (TEMPORARY)
-- ===============================
-- These tables store 30-minute batches of data
-- DELETED after successful LLM processing
-- PRESERVED if any LLM fails (for retry)

-- News Items (30-minute staging)
-- IMPORTANT: URLs must be normalized before storage to enable cross-provider deduplication
-- Strip tracking parameters: ?utm_source=, ?ref=, ?fbclid=, etc.
-- Example: "https://reuters.com/article/123?utm_source=finnhub" → "https://reuters.com/article/123"
CREATE TABLE news_items (
    symbol TEXT NOT NULL,
    url TEXT NOT NULL,                  -- NORMALIZED URL (tracking params stripped)
    headline TEXT NOT NULL,
    content TEXT,                       -- Full article body (short retention)
    published_iso TEXT NOT NULL,        -- ISO format: "2024-01-15T10:30:00Z"
    published_unix INTEGER NOT NULL,    -- Unix timestamp for fast queries
    source TEXT NOT NULL,               -- finnhub, polygon, rss, etc.
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    PRIMARY KEY (symbol, url)
) WITHOUT ROWID;

-- Price Data (30-minute staging)
CREATE TABLE price_data (
    symbol TEXT NOT NULL,
    timestamp_unix INTEGER NOT NULL,    -- When the bar closed (UTC, seconds)
    timestamp_iso TEXT,                 -- Same time but human-readable (optional)
    price_micros INTEGER NOT NULL,      -- Close price × 1,000,000 for exact precision
    volume INTEGER,                     -- Traded amount (whole shares for stocks)
    is_extended INTEGER DEFAULT 0,      -- 0=regular hours, 1=pre/post-market
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    PRIMARY KEY (symbol, timestamp_unix)
) WITHOUT ROWID;

-- ===============================
-- ANALYSIS RESULTS (PERSISTENT)
-- ===============================
-- LLM analysis results - NEVER deleted, only updated
-- Each specialist LLM has one current view per symbol

CREATE TABLE analysis_results (
    symbol TEXT NOT NULL,
    analysis_type TEXT NOT NULL,        -- "news_analysis", "sentiment_analysis", "sec_filings", "head_trader_decision"
    model_name TEXT NOT NULL,           -- "gpt-5", "gemini-2.5-flash"
    stance TEXT NOT NULL,               -- "bullish" | "neutral" | "bearish" (quick filter)
    confidence_score REAL,              -- 0.0 to 1.0
    last_updated_unix INTEGER NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    
    -- LLM analysis in JSON format
    result_json TEXT NOT NULL,          -- Structure: summary, key_points[{title, details, price_impact}], thoughts
    
    PRIMARY KEY (symbol, analysis_type)
) WITHOUT ROWID;

-- ===============================
-- HOLDINGS (PERSISTENT)
-- ===============================
-- Portfolio tracking with break-even calculations

CREATE TABLE holdings (
    symbol TEXT NOT NULL,
    quantity REAL NOT NULL,             -- Shares/units owned (can be fractional for crypto)
    average_cost_per_unit INTEGER NOT NULL,  -- Average cost × 1,000,000 (micros for precision)
    break_even_price INTEGER NOT NULL, -- Price needed to break even after fees × 1,000,000
    total_cost_basis INTEGER NOT NULL, -- Total amount invested × 1,000,000
    first_purchase_unix INTEGER NOT NULL,    -- When first bought this symbol
    last_purchase_unix INTEGER NOT NULL,     -- Most recent purchase
    notes TEXT,                        -- Optional notes about position
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    
    PRIMARY KEY (symbol)
) WITHOUT ROWID;

-- ===============================
-- PERFORMANCE INDEXES
-- ===============================
-- Indexes will be added later when implementing LLM query patterns