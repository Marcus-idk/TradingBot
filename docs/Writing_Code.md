# Writing Code Guidelines - LLM-Optimized

## 📝 HOW TO EXTEND THIS DOCUMENT
- Add rules under appropriate section (MUST/SHOULD)
- Format: `### RULE_NAME` → description → example
- Keep examples minimal but demonstrative
- Test that examples work before adding

---

## PROJECT CONTEXT
- **Python Version**: 3.13.4 (target 3.13+)
- **Principle**: Follow existing patterns. Propose improvements only when they clearly reduce complexity.
- **Scope**: All new/changed code

---

# MUST-FOLLOW RULES

### PYTHON_VERSION
Use Python 3.13+ modern syntax.
```python
# ✅ list[str], dict[str, int | None], match statements, built-in generics
# ❌ typing.List, typing.Optional, typing.Union
```

### SIMPLICITY_KISS
One clear responsibility per module/function.
```python
# ✅ calculate_session(timestamp) - single purpose
# ❌ process_and_store_and_notify_and_log(data) - too many responsibilities
```

### DRY_PRINCIPLE
Avoid duplication when abstraction is real. Avoid premature abstraction.
```python
# ✅ _datetime_to_iso() used 10+ times - good abstraction
# ❌ extract_number() used once - premature
```

### VALIDATE_INPUTS
Validate at boundaries, fail fast on invalid state, make types explicit.
```python
def store_price(symbol: str, price: Decimal) -> None:
    if price <= 0:
        raise ValueError(f"Invalid price {price} for {symbol}")
    # Use dataclasses/enums where helpful
```

### ERROR_HANDLING
Handle errors explicitly. Never swallow. Raise domain-specific exceptions.
```python
try:
    response = api_call(symbol)
except RequestException as e:
    logger.exception(f"Failed to fetch {symbol}")
    raise DataFetchError(f"Cannot retrieve {symbol}: {e}") from e
```

### CENTRALIZE_CONCERNS
Centralize I/O, HTTP, retries/backoff, timezones, data normalization, logging.
```python
# Reuse helpers instead of reimplementing
from utils.http import get_json_with_retry  # Don't reimplement retry logic
from data.models import _normalize_to_utc  # Don't reimplement TZ handling
```

### BOUNDARIES_CLEAN
Keep layers clean. Avoid circular dependencies.
```
Configuration → Adapters/Clients → Models/Storage → Services/Workflows
```

### EXTENSION_POINTS
Add only when 2+ real uses exist.
```python
# ✅ Add interface when FinnhubProvider AND AlphaVantageProvider need it
# ❌ Don't add "just in case"
```

### IMPORTS_ABSOLUTE
Always absolute. Default to package facades for public APIs.
```python
# ✅ from data.storage import commit_llm_batch  # Public via facade
# ✅ from data.storage.db_context import _cursor_context  # Private from source
# ✅ from data.providers.finnhub import FinnhubNewsProvider  # Specific provider
# ❌ from .storage import anything  # Never relative
```

### IMPORT_PLACEMENT
All imports at module level (top of file). Function-level imports allowed ONLY for:
- Optional dependencies (with try/except)
- Breaking circular dependencies (document why inline)
```python
# DEFAULT: Everything at module level
import json
from data.storage import commit_llm_batch
from utils.http import get_json_with_retry
from data.models import NewsItem  # Even if used in one function

def process():
    # RARE EXCEPTION: Only if circular dependency
    # from data.models import NewsItem  # Document why!
    return NewsItem(...)
```

### FACADES_THIN
Keep `__init__.py` thin, side-effect free, explicit `__all__`.
```python
"""Data providers package."""
from data.providers.finnhub import FinnhubNewsProvider

__all__ = ["FinnhubNewsProvider"]  # Only public names

# Add new providers here so IDEs see full surface area
```

### NAMING_CONVENTIONS
- Modules/functions: `snake_case`
- Classes: `PascalCase`  
- Constants: `UPPER_SNAKE`
- Private: `_leading_underscore`

### TYPE_ANNOTATIONS
Use built-in generics. Preserve type parameters when converting.
```python
def process(items: list[str]) -> dict[str, int | None]:
    ...
# Keep from typing: Mapping, Any, Callable, Awaitable, Iterator, TypeVar
```

### KEYWORD_ONLY_ARGS
Use `*` for clarity when needed.
```python
# Use when: 4+ optional params, similar types, boolean flags, multiple cursors
def fetch(url, *, timeout=30, max_retries=3, validate=True):
    ...
# Don't use for: simple 1-3 params, obvious order, dataclasses
```

### DATETIME_HANDLING
Always UTC timezone-aware. Never format timestamps by hand.
```python
# Flow: API input → normalize_to_utc() → _datetime_to_iso() → SQLite ISO+Z
from data.models import _normalize_to_utc

class NewsItem:
    def __init__(self, published: datetime | str):
        self.published = _normalize_to_utc(published)  # Always normalize
```

### MARKET_SESSIONS
Use standard classifier for US sessions.
```python
from utils.market_sessions import classify_us_session
session = classify_us_session(timestamp)  # Returns PRE/REG/POST/CLOSED
# Handles NYSE holidays, early closes, UTC→ET conversion
```

### MONEY_PRECISION
Use Decimal for money. Avoid binary floats.
```python
from decimal import Decimal
price = Decimal("150.25")  # Never float for money
```

### PERSISTENCE
Validate at write boundaries. Choose stable representations. Version schemas clearly.

### DATABASE_SQLITE
Always use `_cursor_context` for all operations.
```python
from data.storage.db_context import _cursor_context

with _cursor_context(db_path) as cursor:
    cursor.execute("INSERT INTO items VALUES (?)", (data,))
# Auto-commit, foreign keys, row factory, cleanup

# Exceptions: Only direct connect() for:
# - init_database() / finalize_database()
# - Connection-level PRAGMAs (document why)
```

### ASYNC_PATTERNS
Use async for I/O. Never block in async paths.
```python
async def fetch_all(symbols):
    loop = asyncio.get_running_loop()  # NOT get_event_loop()
    tasks = [fetch_one(s) for s in symbols]
    return await asyncio.gather(*tasks)
```

### LOGGING_LAYERED
Module-level loggers with appropriate levels. Use f-strings.
```python
logger = logging.getLogger(__name__)

# Provider layer:
logger.debug(f"Skipping item for {symbol}: {reason}")  # Expected drops
logger.warning(f"Failed to fetch {symbol}")  # Request failures
# Let exceptions propagate to orchestrators

# Orchestrator layer:
logger.info(f"Processed {count} items")  # Success summaries  
logger.exception("Workflow failed")  # In except blocks for stack trace
```

### TESTING_REQUIRED
Add/adjust tests for every change.
- Prefer explicit clock helpers over monkeypatching time/datetime
- Follow project testing conventions
- Mark slower integration/network tests
- Monkeypatch where symbol is looked up (module under test), not facades

### DOCUMENTATION
Update docs when public APIs, schemas, or test structure change.
- Brief comments explain "why" not "what"
- Keep README links valid
- Prefer small, focused tests with clear names

---

# SHOULD-FOLLOW RULES

### REUSE_FIRST
Will this be reused soon? If yes, follow existing interfaces. If no, keep local and simple.

### COMMENTS_BRIEF
```python
# Batch size of 100 to stay under API rate limits
BATCH_SIZE = 100

# Import here to avoid circular dependency with models
from data.models import NewsItem
```

---

# CODE REVIEW CHECKLIST

### Correctness
- [ ] Timezones UTC-aware with proper units?
- [ ] Money using Decimal not float?
- [ ] Error paths covered with explicit handling?
- [ ] Retries/backoff where needed?

### Consistency
- [ ] Absolute imports following patterns?
- [ ] Using `_cursor_context` for SQLite?
- [ ] Following naming conventions?
- [ ] Matches surrounding style?

### Design
- [ ] Right abstraction level?
- [ ] Clean boundaries, no circular deps?
- [ ] No premature generalization?

### Security/Performance
- [ ] No secrets in code/logs?
- [ ] Input validation at boundaries?
- [ ] Batch external calls?
- [ ] Respect rate limits/timeouts?
- [ ] Avoid unnecessary allocations?

---

# QUICK REFERENCE

## Import Decision Tree
```
Public API? → facade import
Private (_)? → import from source module
Circular dep? → function-level with comment
Optional dep? → function-level with try/except
```

## Type Conversion Table
| Old typing | New built-in |
|------------|--------------|
| List[str] | list[str] |
| Dict[str, Any] | dict[str, Any] |
| Optional[int] | int \| None |
| Union[str, int] | str \| int |
| Tuple[...] | tuple[...] |

## Datetime Flow
```
Input → _normalize_to_utc() → _datetime_to_iso() → SQLite ISO+Z
```

## Logging Levels
```
DEBUG: Expected failures (invalid data)
WARNING: Partial failures (request failed)
ERROR: Workflow failures  
EXCEPTION: Bugs (auto stack trace)
```