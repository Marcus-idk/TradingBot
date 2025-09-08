# Reviewing Code Guidelines

Purpose: Ensure every change is correct, safe, and consistent.

Scope: Applies to all PRs/commits. Reviewers must read changed code line‑by‑line and verify logic, not just style. Take the time needed; do not rush.

## Review Best Practices (Must)
- Read every line. Do not skim. Assume nothing; verify everything.
- Validate logic and intent: restate what each function/class promises and check it holds.
- Check boundaries: inputs, outputs, errors, time/number handling, and resource cleanup.
- Prefer simpler designs; ask for simplification when complexity adds no value.
- Do not ignore errors: exceptions must be raised or handled; avoid broad/silent catches.
- Reuse centralized helpers for cross‑cutting concerns (HTTP, retries/backoff, time zones, validation).

## Deep Review Plan (Must)
1) Context pass
   - Read the PR description and related docs. Note any new/changed public APIs, data models, storage, or env vars.
   - Skim surrounding modules to understand boundaries (configuration, API clients, data access, services, utilities).
2) API surface map
   - List new/changed functions/classes, parameters, return types, and possible exceptions.
   - Verify names, visibility, and placement follow existing patterns and conventions.
3) Line‑by‑line pass (core)
   - Types: explicit types; correct units; consistent time handling (e.g., UTC); precise numeric types for money.
   - Control flow: exhaustive conditions; early returns clear; no dead/unreachable code; no hidden mutable defaults.
   - Errors: classify retryable vs terminal; avoid swallowing; propagate with context.
   - Resources: async/await correct (no blocking in async); files/sockets/clients closed; cancellation safe.
   - Logging/observability: actionable messages; no secrets; appropriate levels; metrics/traces when applicable.
4) Function semantics
   - Restate preconditions, postconditions, invariants; ensure docstrings and names match behavior.
   - Validate edge cases (empty inputs, None, time boundaries, API quirks, duplicates, idempotency).
5) Cross‑module invariants
   - Data representation: stable enums/identifiers; normalized inputs (e.g., URLs, IDs); consistent encodings.
   - Persistence: column/field names match code; keys and constraints enforced; precise types preserved.
   - State/watermarks: state keys are explicit, documented, and updated only on successful operations.
6) Concurrency/async
   - Parallel work uses safe patterns (e.g., gather with error handling); shared state protected; shutdown is graceful.
7) External boundaries
   - Retries/backoff centralized; timeouts configured; rate limits respected; exponential backoff and jitter where appropriate.
   - Configuration via env/flags only at boundaries; no secrets hardcoded or logged.
8) Tests & docs alignment
   - Tests cover success/edge/error paths; fast unit tests vs slower integration clarified.
   - Documentation and examples reflect real names, fields, and behavior; links valid and case‑correct.

## Consistency (Must)
- Mirror existing layout, naming, and style (see docs/Writing_Code.md).
- Keep diffs minimal and focused; request refactors only when they reduce complexity or fix correctness.
- Reuse existing patterns, enums, and data types; avoid parallel abstractions.

## Tests & Docs (Must)
- Block behavioral changes without corresponding tests.
- Require documentation updates for public API or data model changes.
- Ensure examples are runnable or trivially adaptable.

## What to Block (Must)
- Incorrect or inconsistent time/number handling; imprecise types for money.
- Swallowed exceptions; ad‑hoc retry logic; missing timeouts.
- Schema/contract mismatches; unchecked input; missing normalization for external identifiers.
- New dependencies without justification or violating established patterns.
- Case‑sensitive path/link issues that break on different filesystems.

## Area‑Specific Checklists (General)

### Public APIs & Modules
- Clear boundaries; stable contracts; backward‑compat behavior documented.
- Input validation; precise types; helpful errors.

### Background Jobs/Services
- Scheduling/interval math correct; state updated only on success; idempotency considered.
- Graceful shutdown; retries with backoff; partial failure handling.

### Data Access & Storage
- Column/field names and constraints match code; parameters bound; indexes/PKs correct.
- Normalization performed before write; consistent encodings; migrations/versioning noted.

### External API Clients
- Correct parameter mapping; field conversions explicit; robust to partial/empty responses.
- Connection/timeout settings; retryable vs terminal error classification.

### CLI/Entry Points
- Configuration loading isolated; secrets not logged; helpful startup errors.
- Exit codes meaningful; signals/cancellation handled.

### Libraries/SDK Wrappers
- Error mapping to domain exceptions; retries centralized; extensible configuration.

## Evidence & Tools (Should)
- Use fast search tools (e.g., `rg`) to trace symbols and contracts.
- Provide precise code suggestions; keep review comments focused on “why”, with minimal examples.

## Ready‑to‑Merge Quick Checklist
- Correctness: data/time handling, constraints, and contracts respected.
- Errors/Retry: explicit exceptions, centralized backoff/timeout usage.
- Consistency: naming, layout, logging levels, and helper reuse match the codebase.
- Tests: added/updated; clear separation of unit vs integration.
- Docs: updated where needed; examples and links accurate.

