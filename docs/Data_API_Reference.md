# Data_API_Reference

## What this file is
A **contract-only reference** for external data providers we call. It explains **what data** we use them for and **how to call** them (auth, base URLs, routes, params) with brief response semantics. Implementation details live elsewhere.

## Symbol Guide
For each provider's **"What they provide"** section:
- **List items** = data domains AVAILABLE from that provider's API
- **✅** = Available AND currently USED/IMPLEMENTED in our project
- **❌** = Available from the API but NOT USED YET in our project
- **Not listed** = Not available from that provider at all

The **"Endpoints"** section shows only what we actually call/use (matching the ✅ items above).

## Data domains we ingest
- **Macro News** — Major market-moving events.
- **Company News** — News about specific companies.
- **People News** — News about key people (executives, insiders).
- **Filings** — Official company filings and disclosures.
- **Social/Sentiment** — Online crowd sentiment.
- **Prices/Market Data** — Stock prices and market data.

---

## Provider: Finnhub
**Auth & Base**: API key (query/header) · Base: `https://finnhub.io/api/v1`

**What they provide**
- Macro News — ✅
- Company News — ✅
- Prices/Market Data — ✅

**Rate Limits**
- Global throttle: 30 API calls/second (hard cap across all endpoints).
- Free tier: around 60 calls/minute.
- Paid tiers: higher minute limits (roughly 300–900 calls/minute depending on plan).
- Exceeding limits returns HTTP 429; 1 API key → 1 websocket connection.

**Recommended Connectivity / Health Check**
- Endpoint: `GET /stock/market-status`.
- Why: Lightweight way to verify connectivity + key validity without heavy data.

**Usage Notes (News & Prices)**
- Macro news pagination: use `minId` with the last seen ID to fetch only newer items.
- Company news: time‑window based, no built‑in pagination; we control date range.
- Prices: `/quote` is fine for snapshots, but constant real‑time polling should use websockets instead.

**Endpoints**
- Macro News — `GET /news`
  - Params: `category` (`general` | `forex` | `crypto` | `merger`), `minId` (optional), `token`
  - Returns:
    ```json
    [
      {
        "category": "general",
        "datetime": 1727865600,
        "headline": "Stocks rise as investors digest inflation data",
        "id": 123456789,
        "image": "https://example.com/image.jpg",
        "related": "",
        "source": "Reuters",
        "summary": "U.S. stocks climbed after new CPI figures...",
        "url": "https://www.reuters.com/markets/us/..."
      }
    ]
    ```

- Company News — `GET /company-news`
  - Params: `symbol`, `from` (`YYYY-MM-DD`), `to` (`YYYY-MM-DD`), `token`
  - Returns:
    ```json
    [
      {
        "category": "company",
        "datetime": 1696012800,
        "headline": "Apple launches new product line",
        "id": 987654321,
        "image": "https://example.com/aapl.jpg",
        "related": "AAPL",
        "source": "Reuters",
        "summary": "Apple unveiled its latest devices at an event...",
        "url": "https://www.reuters.com/technology/..."
      }
    ]
    ```

- Prices/Market Data — `GET /quote`
  - Params: `symbol`, `token`
  - Returns:
    ```json
    {
      "c": 261.74,
      "h": 263.31,
      "l": 260.68,
      "o": 261.07,
      "pc": 259.45,
      "t": 1582641000
    }
    ```

---

## Provider: Reddit
**Auth & Base**: OAuth2 (client_id + client_secret + user_agent) · Base: `https://oauth.reddit.com`

**What they provide**
- Social/Sentiment — ✅ (posts + top comments)

**Rate Limits**
- OAuth: ~100 requests/minute.
- Use `+` syntax to combine subreddits in one request (e.g., `stocks+investing+wallstreetbets`).
- Batch fetch with `/api/info` when you have multiple IDs.

**Recommended Connectivity / Health Check**
- Endpoint: `GET /api/v1/me`.
- Why: Verifies OAuth token validity and returns authenticated user info.

**Usage Notes (Social/Sentiment)**
- Time filters: Only `hour`, `day`, `week`, `month`, `year`, `all` available. No "last 5 minutes" option.
- Incremental fetching: Use `time_filter=hour` and filter locally by watermark timestamp.
- Bootstrap: Use `time_filter=week` for first run / new symbols.
- Target subreddits: `stocks`, `investing`, `wallstreetbets`.
- Response model: All endpoints return "things" wrapped in `kind` + `data` envelope.

**Endpoints**
- Search Posts — `GET /r/{subreddit}/search`
  - Params: `q` (query, e.g., "AAPL"), `restrict_sr` (boolean, restrict to subreddit), `sort` (`relevance` | `hot` | `top` | `new` | `comments`), `t` (`hour` | `day` | `week` | `month` | `year` | `all`), `limit` (max 100), `after` (fullname for pagination)
  - Returns:
    ```json
    {
      "kind": "Listing",
      "data": {
        "after": "t3_abc123",
        "children": [
          {
            "kind": "t3",
            "data": {
              "id": "xyz789",
              "name": "t3_xyz789",
              "title": "AAPL earnings discussion",
              "selftext": "What do you think about...",
              "author": "user123",
              "subreddit": "stocks",
              "created_utc": 1732900800.0,
              "permalink": "/r/stocks/comments/xyz789/aapl_earnings_discussion/",
              "url": "https://www.reddit.com/r/stocks/comments/xyz789/aapl_earnings_discussion/"
            }
          }
        ]
      }
    }
    ```
  - **Note**: Use `sort=new` and `t=hour` for incremental polling. Use `+` syntax for multi-subreddit search (e.g., `/r/stocks+investing/search`).

- Get Post Comments — `GET /r/{subreddit}/comments/{article}`
  - Path: `subreddit` (subreddit name), `article` (post ID36, e.g., "xyz789")
  - Params: `sort` (`confidence` | `top` | `new` | `controversial` | `old`), `limit` (max comments), `depth` (max reply depth)
  - Returns:
    ```json
    [
      {
        "kind": "Listing",
        "data": {
          "children": [
            {
              "kind": "t3",
              "data": { "...post data..." }
            }
          ]
        }
      },
      {
        "kind": "Listing",
        "data": {
          "children": [
            {
              "kind": "t1",
              "data": {
                "id": "abc123",
                "name": "t1_abc123",
                "body": "I think AAPL is undervalued...",
                "author": "investor99",
                "score": 45,
                "created_utc": 1732901400.0,
                "is_submitter": false
              }
            }
          ]
        }
      }
    ]
    ```
  - **Note**: Returns array of two Listings: first is the post (t3), second is the comment tree (t1). Use `sort=top` and `limit=20` to get highest-signal comments.

---

## Notes
- Keep this file concise and **contract-only**.
