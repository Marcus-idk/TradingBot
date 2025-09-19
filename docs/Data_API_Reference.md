# Data_API_References

## What this file is
A **contract-only reference** for external data providers we call. It explains **what data** we use them for and **how to call** them (auth, base URLs, routes, params) with brief response semantics. Implementation details live elsewhere.

## Data domains we ingest
- **Macro News** — Major market-moving events.
- **Company News** — News about specific companies.
- **People News** — News about key people (executives, insiders).
- **Filings** — Official company filings and disclosures.
- **Social/Sentiment** — Online crowd sentiment.
- **Financials** — Company financial reports.
- **Prices/Market Data** — Stock prices and trading data.

---

## Provider: Finnhub — Company News · Prices
**Auth & Base**: API key (query/header) · Base: `https://finnhub.io/api/v1`

**What they provide**
- Macro News — ❌
- Company News — ✅
- People News (tag) — ✅
- Filings — ❌
- Social/Sentiment — ❌
- Financials — ❌
- Prices/Market Data — ✅

**Endpoints (current usage)**
- Company news — `GET /company-news`
  - Params: `symbol`, `from` (`YYYY-MM-DD`), `to` (`YYYY-MM-DD`), `token`
  - Notes: We fetch recent ranges and filter by UTC publish time.
- Quote — `GET /quote`
  - Params: `symbol`, `token`
  - Returns: `c` (current price), `h`, `l`, `o`, `pc` (prev close), `t` (epoch UTC)

---

## Other providers (coverage only for now)
- Polygon — Covers: ✅ Prices (backup) · ✅ Company News *(plan-dependent)*
- SEC EDGAR — Covers: ✅ Filings (10‑K, 10‑Q, 8‑K, insider)
- Reddit — Covers: ✅ Social/Sentiment (subreddits, posts, comments)
- RSS / Publisher Feeds — Covers: ✅ Macro News · ✅ Company News · ✅ People *(tagged)*

---

## Notes
- Keep this file concise and **contract-only**.
