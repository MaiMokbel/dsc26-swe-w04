# Nour stock transfers: test suite (dsc26-swe-w04)

We write the TESTS for a service someone else wrote. The grader swaps in its own
`nour_transfers/` and runs our suite against 13 broken versions (mutants).

## Commands
- Setup (Windows): `uv venv --python 3.12` then `.venv\Scripts\activate`,
  then `uv pip install -r requirements.txt`
- Run tests: `python -m pytest -q -p no:cacheprovider tests/` from the repo root
- Never change versions in requirements.txt. Python 3.12 only. No network in tests.

## Do not touch
- `nour_transfers/` and `contracts/` are replaced by the grader. Never edit them,
  even to "fix" a bug. If code and SPEC.md disagree, tell me; do not change code.
- Do not add a root `conftest.py`, `pytest.ini` or pytest settings in pyproject.
  The grader deletes or ignores them. Shared fixtures go in `tests/conftest.py`.

## Source of truth
- Behaviour: SPEC.md (read it before writing any test). The README is about grading.
- Card shape: contracts/transfer_card.schema.json

## How tests must be written
- Public interface only: `days_of_cover`, `priority`, `can_transfer`, `create_app`,
  and the HTTP API. Never import anything else (e.g. ALLOWED_ORIGINS, ApiError,
  CamelModel), never monkeypatch internals, never read source files.
  The grader runs us against a rewrite with different private names, as bytecode.
- Check results through the API: stock via `GET /v1/branches/{b}/stock/{item}`,
  not by peeking at dicts passed to create_app.
- For errors, assert status AND `type` (e.g. `/problems/not-pending`) AND
  content-type `application/problem+json`. Status alone does not kill mutants.
- Test boundaries exactly: reserve left == reserve (allowed), cover == 3 and == 7.
- `days_of_cover` with zero sales is `None`, not 0. Assert `is None`.
- `requestedAt` must end in `Z`. Use a fixed `now` (see FIXED_NOW in conftest).
- Need different data? Build a new app with `create_app(...)` + TestClient in
  the test. Do not change the shared `client` fixture's data.
- No `skip`, `skipif` or `xfail`. Every test must pass on the real code.

## Layout
- `tests/unit/` rules functions, `tests/api/` HTTP, `tests/contract/` schema.
- Every folder needs `__init__.py`. Test file names must be unique across folders.
- Helpers already exist in tests/api/test_transfer_flow.py (`post`, `units`,
  `assert_problem`). Copy the pattern; do not import between test files.

## Known traps
- Approve re-checks the reserve against CURRENT stock; a refused approval
  must change nothing on either branch.
- Priority uses the DESTINATION branch's stock and sales, not the source's.
- Inbox order: urgent, high, normal, then request order (tr_1, tr_2...).

## Before saying a task is done
- Full suite green in under 60 s, and you ran it, not just the new file.
- AI_USAGE.md keeps its three headings exactly.
