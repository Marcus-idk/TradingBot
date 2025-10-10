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
- **Prices/Market Data** — Stock prices and trading data.

---

## Provider: Finnhub
**Auth & Base**: API key (query/header) · Base: `https://finnhub.io/api/v1`

**What they provide**
- Macro News — ✅
- Company News — ✅
- Prices/Market Data — ✅

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

## Provider: Polygon.io
**Auth & Base**: API key (query param `apiKey`) · Base: `https://api.polygon.io`

**What they provide**
- Macro News — ✅
- Company News — ✅
- Prices/Market Data — ✅

**Endpoints**
- Company News — `GET /v2/reference/news`
  - Params: `ticker` (required for company news), `published_utc` (RFC3339), `published_utc.gte`, `published_utc.gt`, `published_utc.lte`, `published_utc.lt`, `sort` (default `published_utc`), `order` (asc/desc), `limit` (default 10, max 1000), `cursor` (pagination), `apiKey`
  - Returns:
    ```json
    {
      "count": 1,
      "next_url": "https://api.polygon.io/v2/reference/news?cursor=...",
      "results": [
        {
          "id": "8ec638777ca03b553ae516761c2a22ba2fdd2f37befae3ab6fdab74e9e5193eb",
          "title": "Markets are underestimating Fed cuts: UBS",
          "published_utc": "2024-06-24T18:33:53Z",
          "article_url": "https://uk.investing.com/news/...",
          "tickers": ["UBS"],
          "description": "UBS analysts warn that markets are underestimating...",
          "publisher": {
            "name": "Investing.com",
            "homepage_url": "https://www.investing.com/",
            "logo_url": "https://s3.polygon.io/public/assets/news/logos/investing.png"
          }
        }
      ]
    }
    ```
  - **Note**: Timestamps in RFC3339 format. Use `published_utc.gt` for incremental fetching. Follow `next_url` for pagination.

- Macro News — `GET /v2/reference/news`
  - Params: `published_utc` (RFC3339), `published_utc.gte`, `published_utc.gt`, `published_utc.lte`, `published_utc.lt`, `sort` (default `published_utc`), `order` (asc/desc), `limit` (default 10, max 1000), `cursor` (pagination), `apiKey`
  - Returns:
    ```json
    {
      "count": 1,
      "next_url": "https://api.polygon.io/v2/reference/news?cursor=...",
      "results": [
        {
          "id": "8ec638777ca03b553ae516761c2a22ba2fdd2f37befae3ab6fdab74e9e5193eb",
          "title": "Markets are underestimating Fed cuts: UBS",
          "published_utc": "2024-06-24T18:33:53Z",
          "article_url": "https://uk.investing.com/news/...",
          "tickers": ["UBS"],
          "description": "UBS analysts warn that markets are underestimating...",
          "publisher": {
            "name": "Investing.com",
            "homepage_url": "https://www.investing.com/",
            "logo_url": "https://s3.polygon.io/public/assets/news/logos/investing.png"
          }
        }
      ]
    }
    ```
  - **Note**: Omit `ticker` parameter to get general market news. Filter results using `tickers` array to match watchlist symbols; articles with no matches map to 'ALL'.

- Prices/Market Data — `GET /v2/snapshot/locale/us/markets/stocks/tickers/{symbol}`
  - Path: `symbol` (ticker, case-sensitive)
  - Params: `apiKey`
  - Returns:
    ```json
    {
      "status": "OK",
      "ticker": {
        "ticker": "AAPL",
        "updated": 1699891198523000000,
        "lastTrade": {
          "p": 150.26,
          "s": 100,
          "t": 1699891198523000000,
          "x": 4
        },
        "lastQuote": {
          "P": 150.27,
          "p": 150.25,
          "S": 10,
          "s": 5,
          "t": 1699891198507251700
        },
        "day": {
          "c": 150.26,
          "h": 151.20,
          "l": 149.50,
          "o": 150.00,
          "v": 28727868,
          "vw": 150.12
        }
      }
    }
    ```
  - **Note**: Timestamps are in nanoseconds. We prefer `lastTrade.p` (actual execution) over quote midpoint.

- Connection Validation — `GET /v1/marketstatus/now`
  - Params: `apiKey`
  - Used for validating API connectivity (cheap endpoint, doesn't count against rate limits)

**Rate Limits**
- Free tier: ~5 calls/min (shared across all endpoints)
- Company news: 1 call per symbol per poll (+ pagination)
- Macro news: 1 call per poll (+ pagination)
- Prices: 1 call per symbol per poll
- Caution: Combined news + price fetching with large watchlists may exceed free tier limits

---

## Notes
- Keep this file concise and **contract-only**.
