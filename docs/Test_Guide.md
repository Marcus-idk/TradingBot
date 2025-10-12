# Test Organization Guide - LLM-Optimized

## 📝 HOW TO EXTEND THIS DOCUMENT
- Add patterns to appropriate section
- Format: `### PATTERN_NAME` → when to use → example
- Keep decision trees updated
- Reference actual test files that demonstrate pattern

---

## LIMITS & FRAMEWORK
- **Max file size**: 600 lines (target: ~400)
- **Max test class**: ~200-250 lines
- **Framework**: pytest
- **Principle**: Make it obvious where to find/add tests

---

# WHERE TO PUT YOUR TEST - PRIMARY DECISION

```
Is it unit or integration test?
├── UNIT TEST → tests/unit/ (mirrors source structure exactly)
│   └── Continue to "Unit Test Organization Rules"
└── INTEGRATION TEST → tests/integration/ (organized by feature)
    ├── Mark with @pytest.mark.integration
    ├── Name as test_<workflow>.py
    └── STOP - you're done
```

---

# UNIT TEST ORGANIZATION RULES

## Decision Tree for Unit Tests
```
What's in your source file?
├── CLASSES ONLY → Rule 1: Test<ClassName> for each class
├── FUNCTIONS ONLY → Rule 2: Split by feature into test_<module>_<feature>.py
├── BOTH → Rule 3: Test<ClassName> + test_<module>_functions.py
├── ABSTRACT BASE CLASSES → Rule 4: Test<ClassName>Contract
└── ENUMS → Rule 5: test_enum_values_unchanged()
```

## Rule 1: Classes Get 1:1 Mapping
```python
# Source: data/providers/finnhub/client.py
class FinnhubClient:
    ...
class FinnhubNewsProvider:
    ...

# Test: tests/unit/data/providers/test_finnhub.py
class TestFinnhubClient:
    ...
class TestFinnhubNewsProvider:
    ...
```
✅ Easy to find: "Where's test for FinnhubClient?" → TestFinnhubClient  
❌ Bad: TestFinnhubStuff, TestNewsFeatures

## Rule 2: Functions Get Feature Groups
```python
# Source: data/storage/storage_crud.py (25+ functions)
def store_news_items(): ...
def get_news_since(): ...
def store_price_data(): ...
def get_price_data_since(): ...
# ... 20+ more functions

# Tests: Split by feature
# tests/unit/data/storage/test_storage_news.py
class TestNewsStorage:
    def test_store_news_items_valid(): ...
    def test_get_news_since_returns_sorted(): ...

# tests/unit/data/storage/test_storage_prices.py
class TestPriceStorage:
    def test_store_price_data_valid(): ...
```
✅ Files stay under 400 lines, organized by function  
❌ Bad: One giant 1200-line file

## Rule 3: Mixed Files Get Both
```python
# Source: utils/helpers.py
class CacheManager: ...
def normalize_string(): ...
def validate_input(): ...

# Tests:
# tests/unit/utils/test_helpers.py
class TestCacheManager:  # 1:1 for class
    ...

# tests/unit/utils/test_helpers_functions.py
class TestStringHelpers:  # Or plain functions
    def test_normalize_string(): ...
```

## Rule 4: ABCs Get Contract Tests
```python
# Source: data/base.py
class DataSource(ABC):
    @abstractmethod
    def fetch(): ...

# Test: tests/unit/data/test_base.py (or test_base_contracts.py)
class TestDataSourceContract:
    def test_all_implementations_have_fetch(): ...
    def test_fetch_returns_expected_type(): ...
```
✅ Tests the contract, not forcing 1:1  
❌ Bad: TestDataSource (meaningless for ABCs)

## Rule 5: Enums Need Value Lock Tests
```python
# Source: data/models.py
class Session(Enum):
    REG = "REG"
    PRE = "PRE"
    POST = "POST"
    CLOSED = "CLOSED"

# Test: tests/unit/data/test_models.py
def test_enum_values_unchanged():
    """These values are in database - MUST NOT CHANGE."""
    assert Session.REG.value == "REG"
    assert Session.PRE.value == "PRE"
    assert Session.POST.value == "POST"
    assert Session.CLOSED.value == "CLOSED"
```
✅ Prevents someone changing "REG" to "REGULAR" and breaking DB

---

# INTEGRATION TEST ORGANIZATION

## Structure by Feature/Workflow
```
tests/integration/
├── data/
│   ├── providers/              # live/data-source workflows
│   ├── test_<workflow>.py      # e.g., test_roundtrip_e2e.py
│   └── ...
└── llm/
    ├── helpers.py
    └── test_<provider>_provider.py
```
*Illustrative structure - use as pattern, not exact inventory*

## Integration Test Rules
- Organize by FEATURE/WORKFLOW, not source structure
- Always mark with `@pytest.mark.integration`
- Live/network tests also use `@pytest.mark.network`
- Can use real databases, APIs (in integration only!)
- Test complete workflows, not individual functions

## Networked Live Tests
```python
# Required environment variables
FINNHUB_API_KEY     # Finnhub live checks
OPENAI_API_KEY      # OpenAI provider tests
GEMINI_API_KEY      # Gemini provider tests

# Skip gracefully when missing
@pytest.mark.skipif(
    not os.getenv("FINNHUB_API_KEY"),
    reason="FINNHUB_API_KEY not set"
)
def test_finnhub_live():
    ...
```

---

# TEST PATTERNS

## FOLLOW_SIMILAR_TESTS → Study existing tests before writing new ones
When writing tests for similar functionality, find and study the existing test implementation. Follow its structure, patterns, and conventions—including test naming, mock setup, assertion style, and organization—but don't blindly copy tests that don't apply to your use case.

**Pattern:**
1. Find similar test file (e.g., testing PolygonClient? → look at test_finnhub_client.py)
2. Study its structure: class names, test method names, mock patterns, assertions
3. Copy what applies: naming conventions, mock setup patterns, assertion patterns
4. Adapt what doesn't: API differences, different behaviors, different error types

**Example:**
```python
# SCENARIO: Writing tests for PolygonNewsProvider
# STEP 1: Find similar tests → test_finnhub_news.py exists

# STEP 2: Study test structure
# From test_finnhub_news.py:
class TestFinnhubNewsProvider:
    async def test_parses_valid_article(self):
        news_fixture = [{
            'headline': 'Tesla Stock Rises',
            'url': 'https://example.com/tesla-news',
            'datetime': 1705320000,  # Epoch
            'source': 'Reuters',
            'summary': 'Tesla stock rose 5% today.'
        }]
        # ... rest of test

# STEP 3: Copy structure and naming for Polygon tests
# ✅ Copy: test class name pattern (TestPolygonNewsProvider)
# ✅ Copy: test method name pattern (test_parses_valid_article)
# ✅ Copy: mock setup pattern (provider.client.get = AsyncMock(...))
# ✅ Copy: assertion style (assert result.symbol == 'AAPL')
# ❌ Don't copy: Field names (Polygon uses 'title' not 'headline')
# ❌ Don't copy: Timestamp format (Polygon uses RFC3339 not epoch)

class TestPolygonNewsProvider:
    async def test_parse_article_valid(self):  # Same naming pattern
        article = {
            'title': 'Apple Announces iPhone',      # Polygon field name
            'article_url': 'https://example.com/1', # Polygon field name
            'published_utc': '2024-01-15T12:00:00Z', # RFC3339, not epoch
            'publisher': {'name': 'TechCrunch'},
            'description': 'Apple unveils...'
        }
        # Same assertion pattern as Finnhub tests
        assert result.symbol == 'AAPL'
        assert result.headline == 'Apple Announces iPhone'
```

**Key Benefits:**
- Consistent test style across similar modules
- Faster test development (copy proven patterns)
- Easier code review (reviewers recognize patterns)
- Reduced bugs (proven test patterns work)

**When to Study Similar Tests:**
- ✅ Writing provider tests → Study other provider tests
- ✅ Writing storage tests → Study other storage tests
- ✅ Writing LLM tests → Study existing LLM tests
- ✅ Adding new test to existing file → Match that file's style

**References:**
- Provider tests: `test_finnhub_client.py`, `test_finnhub_news.py`, `test_finnhub_macro.py`
- Storage tests: `test_storage_news.py`, `test_storage_prices.py`
- LLM tests: `test_openai_provider.py`, `test_gemini_provider.py`

---

## Testing Retry Logic
Mock HTTP client with response sequences, not the retry wrapper.
```python
# ✅ CORRECT: Mock HTTP responses, verify retry behavior
responses = [
    Mock(status_code=429),
    Mock(status_code=429),
    Mock(status_code=200, json=lambda: {"data": "success"})
]
mock_http_client(mock_get_function)
assert call_count == 3  # Verify retries happened

# ❌ WRONG: Mock retry wrapper only tests delegation
monkeypatch.setattr('get_json_with_retry', mock_success)
assert call_count == 1  # Doesn't test retries!
```
Reference: `tests/unit/utils/test_http.py::test_429_numeric_retry_after`

## SQLite Helper Usage
Prefer `_cursor_context` for all operations.
```python
from data.storage.db_context import _cursor_context

# ✅ Good for reads
with _cursor_context(db_path, commit=False) as cursor:
    cursor.execute("SELECT * FROM items")
    
# ✅ Good for writes (default commit=True)
with _cursor_context(db_path) as cursor:
    cursor.execute("INSERT INTO items VALUES (?)", (data,))

# ❌ Avoid direct connect() unless:
# - init_database() / finalize_database()
# - Connection-level PRAGMAs (e.g., WAL checkpoint)
```

## Monkeypatching
Patch where symbol is looked up (module under test), not facades.
```python
# Source: data/providers/finnhub.py
import requests

class FinnhubProvider:
    def fetch_quote(self, symbol):
        response = requests.get(...)

# ✅ CORRECT: Patch in module that uses it
monkeypatch.setattr("data.providers.finnhub.requests.get", mock_get)

# ❌ WRONG: Won't work through facades
monkeypatch.setattr("data.providers.requests.get", mock_get)
```

## Testing Best Practices
- Prefer explicit clock helpers/fixture defaults over monkeypatching time/datetime
- Unnecessary patches add global side effects without increasing coverage
- Follow project testing conventions
- Mark slower integration/network tests
- Avoid duplicate assertions across layers (e.g., DB defaults live in schema tests only)
- Prefer small, focused tests with minimal examples and clear names

### No Forced Passes
- Tests must fail on real regressions; do not hide failures.
- Do not catch broad exceptions in tests; assert specific errors with `pytest.raises`.
- Do not use `@pytest.mark.skip`/`xfail` without a concrete, documented reason.
- Avoid trivial assertions (e.g., `assert True`); validate outputs and side effects.
- Don’t over-mock to bypass code-under-test logic; mock at boundaries only.

Example:
```python
# ✅ GOOD: Fails if validation regresses
with pytest.raises(ValueError):
    store_price("AAPL", Decimal("-1"))

# ❌ BAD: Swallows real failures
try:
    store_price("AAPL", Decimal("-1"))
except Exception:
    pass
```

---

# FILE SIZE & NAMING

## When to Split
- File exceeds 600 lines → MUST split
- Scrolling too much → split
- Can't remember what's in file → split

## Naming Conventions

### Test Files
```python
# Unit tests
test_<module>.py                # Single module
test_<module>_<feature>.py      # Feature within module

# Integration tests
test_<workflow>.py               # Complete workflow
```

### Test Classes
```python
TestClassName        # For 1:1 mapping
TestFeatureName      # For features
TestModuleErrors     # For errors
```

### Test Methods
```python
# ✅ GOOD: Descriptive
def test_store_news_with_duplicate_url_skips():
def test_price_validation_rejects_negative_values():

# ❌ BAD: Vague
def test_1():
def test_stuff():
```

---

# WHAT NOT TO DO

### ❌ DON'T: Create one giant test file
If exceeds 600 lines, split by feature/responsibility.

### ❌ DON'T: Forget to test enums
Enum values stored in DB - changing breaks existing data.

### ❌ DON'T: Mix patterns randomly
Classes get 1:1, functions get feature grouping.

### ❌ DON'T: Use vague test names
`test_1()` → `test_store_news_with_duplicate_url_skips()`

---

# QUICK CHECKLIST

## Is it in the right location?
- [ ] Unit test? → Mirror source in tests/unit/
- [ ] Integration? → Workflow in tests/integration/
- [ ] Marked correctly? → @pytest.mark.integration, @pytest.mark.network

## Does it follow the pattern?
- [ ] Classes? → 1:1 with TestClassName
- [ ] Functions? → Split by feature
- [ ] Mixed? → Both patterns
- [ ] ABC? → Contract tests
- [ ] Enum? → Value lock tests

## Quality checks
- [ ] Test file < 600 lines? (split if not)
- [ ] Test names descriptive?
- [ ] Using _cursor_context for SQLite?
- [ ] Mocking at correct level (not facades)?
- [ ] Integration tests marked correctly?
- [ ] Following similar test patterns? (studied existing tests first?)

## When in Doubt
1. **Make it obvious** where to find/add tests
2. **Keep files small** enough to understand quickly
3. **Follow the pattern** for that type of module
4. **Ask yourself:** "Will someone new understand this in 6 months?"

---

# EXAMPLE PATTERNS REFERENCE

**Use these as templates when writing similar tests (see FOLLOW_SIMILAR_TESTS above)**

- **1:1 Class Mapping**: Source `data/providers/finnhub/client.py` → Test `tests/unit/data/providers/test_finnhub.py` has `TestFinnhubClient`
  - Copy for: Polygon providers, new data providers

- **Feature-Based Functions**: Source `data/storage/storage_crud.py` → Tests split into `test_storage_news.py`, `test_storage_prices.py`
  - Copy for: New storage operations, utility modules

- **Integration Test**: `tests/integration/data/test_dedup_news.py`, `test_roundtrip_e2e.py`, `test_timezone_pipeline.py`
  - Copy for: New workflows, E2E validation

- **Retry Logic**: `tests/unit/utils/test_http.py::test_429_numeric_retry_after`
  - Copy for: HTTP clients, retry wrappers
