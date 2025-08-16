# Trading Bot Development Plan

## Project Goal
Build an automated trading bot that leverages LLMs for fundamental analysis to gain an edge over retail traders. The bot will monitor existing holdings and provide hold/sell recommendations every 30 minutes.

## Core Strategy
- **Target Competition**: Retail traders (not institutional HFT firms)
- **Edge**: LLM analyzing hundreds of sources 24/7 vs manual traders reading 2-3 sources
- **Final Scope**: Monitor existing positions only (no new trade discovery)

---

## v0.1 - LLM Foundation ✅ **COMPLETED**

### What's Built
- **LLM Provider Module**: Abstract base class with clean provider pattern
- **OpenAI Provider**: GPT-5 with reasoning, tools, function calling
- **Gemini Provider**: Gemini 2.5 Flash with code execution, thinking config
- **Comprehensive Testing**: SHA-256 validation tests for both providers
- **Async Implementation**: Production-ready async/await pattern

### LLM Selection Strategy
- **Gemini 2.5 Flash**: Cost-effective for specialist analyst roles
- **GPT-5**: Premium model for final trading decisions

### Status: ✅ **Production Ready**

---

## v0.2 - Data Source Integrations 🔄 **NEXT PHASE**

### Target Data Sources (5 APIs)

#### Price and News Data
- **Finnhub** (Primary): Stock/crypto prices + financial news
  - Free: 60 calls/min → Paid: $50/month unlimited
- **Polygon.io** (Backup): Price data + news when Finnhub fails  
  - Free: 5 calls/min (useless) → Paid: $99/month minimum
- **RSS Feeds** (Always-on): Unlimited news backup source
  - Cost: **FREE** from major financial outlets

#### Crowd Sentiment Analysis
- **Reddit API** (via PRAW): Retail trader sentiment and discussions
  - Free: 100 queries/min (non-commercial) → Paid: Contact for pricing

#### Official Company Data  
- **SEC EDGAR**: Earnings reports, insider trading, official filings
  - Cost: **FREE** (10 requests/sec limit)
  - Note: Stocks only, crypto doesn't have SEC filings

### Implementation Plan
1. **Abstract DataSource Interface**: Clean provider pattern like LLMs
2. **Data Models**: Standardized DTOs for all data types  
3. **Configuration Management**: API keys and provider settings
4. **Concrete Implementations**: One file per data source
5. **Aggregation Service**: Coordinate multiple data sources

### File Structure
```
data/
├── __init__.py          # Clean exports
├── base.py              # Abstract DataSource interface  
├── models.py            # Data models/DTOs
├── config.py            # Configuration management
├── aggregator.py        # Simple data combination
└── providers/
    ├── __init__.py
    ├── finnhub.py       # Stock data
    ├── polygon.py       # Market data
    ├── rss.py           # News feeds
    ├── reddit.py        # Social sentiment
    └── sec_edgar.py     # SEC filings
```

### Cost Estimate for v0.2
- **Minimal**: $0/month (use all free tiers)
- **Recommended**: $50/month (Finnhub paid tier)
- **Premium**: $150/month (Finnhub + Polygon.io)

---

## v0.3+ - Trading Intelligence Layer 📋 **FUTURE PHASES**

### Multi-Agent Architecture
```
Raw Data → Specialized LLM Agents → Final Decision Agent → User
```

#### Agent Roles
1. **News Analyst LLM**: Processes Finnhub + RSS financial news
2. **Sentiment Analyst LLM**: Analyzes Reddit social sentiment  
3. **SEC Filings Analyst LLM**: Reviews EDGAR official company data
4. **Head Trader LLM**: Synthesizes all data + current holdings for final decision

### Core Trading Logic
- **Portfolio Management**: Current holdings tracking
- **Signal Generation**: Trading signals and recommendations
- **Decision Engine**: HOLD/SELL recommendation logic

### Orchestration & Infrastructure
- **Scheduling**: GitHub Actions every 30 minutes during market hours
- **Storage**: Results append to file in GitHub repo
- **Output Format**: Holdings analysis + summaries + recommendations

### Technical Implementation
- **File Structure**: Enterprise-grade Clean Architecture
- **Configuration**: Environment-based API key management
- **Logging**: Structured logging for debugging and monitoring
- **Testing**: Integration tests for end-to-end workflows

---

## v1.0 - Complete Trading Bot 🎯 **FINAL TARGET**

### Full Feature Set
- ✅ **LLM Providers** (v0.1)
- 🔄 **Data Sources** (v0.2)  
- 📋 **Trading Agents** (v0.3+)
- 📋 **Orchestration** (v0.3+)
- 📋 **Scheduling** (v0.3+)
- 📋 **Production Infrastructure** (v1.0)

### Production Infrastructure Additions
- **Rate Limiting**: Per-provider API throttling to prevent bans
- **Caching Layer**: TTL-based caching to reduce API calls and costs
- **Data Validation**: Financial data accuracy and freshness checks
- **Error Handling**: Circuit breaker patterns and graceful degradation
- **Monitoring**: Comprehensive logging and health checks

### Success Metrics
- **Performance**: Beat buy-and-hold strategy
- **Reliability**: 99%+ uptime for data collection
- **Cost Efficiency**: Stay within $10-50/month budget
- **Risk Management**: Recommendations only, no actual trade execution

### Final Technical Stack
- **Python**: Financial libraries, all APIs have Python SDKs
- **GitHub Actions**: Free scheduling and execution
- **Clean Architecture**: Scalable, maintainable codebase
- **Async/Await**: High-performance concurrent API calls