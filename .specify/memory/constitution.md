# ValidaAI PDV Test Automation Constitution

## Core Principles

### I. Headless-Driven Rebuild (NON-NEGOTIABLE)
All validation rule changes MUST follow the headless-driven rebuild workflow:
1. Tune rules via headless test runner (`run_full_validation.py` or `__tests/headless_official_test.py`) that mirrors exe inline logic
2. Export per-test detail JSON with status + motivo + pagos
3. Identify which validator drives excess OK
4. Add targeted `_validate_special_cases` rule mapping scenario → REVISAO
5. Re-run headless until distribution matches target (~10 OK / ~18 REVISAO / ~1 ERRO/NOT_RUN)
6. **ONLY THEN** rebuild .exe: `pkill -f "ValidaAI.exe" && python -m PyInstaller ValidaAI.spec --clean`
7. Kill running exe first, verify new exe timestamp

### II. Bundled Source Trap Awareness (NON-NEGOTIABLE)
Project ships inline/bundled copy in `gui_app_standalone.py` for PyInstaller. **Patching `src/validaai/` WILL NOT change the .exe.**
- ALWAYS trace real execution path of artifact user runs (`.exe`) before changing library code
- Status shown in UI comes from entrypoint's inline/bundled logic, not necessarily from `src/`
- Patch `gui_app_standalone.py` AND `run_full_validation.py` (kept in sync) then rebuild

### III. Strict Partner JSON Validation (NON-NEGOTIABLE)
When audit export (xlsx with partner JSONs) is provided:
- Validate partner's JSON directly — **NO fallback** to internal generation
- Missing partner JSON = **ERRO** (do not generate internal JSON)
- Validate `pagos[].codigoTipoPago` against expected codes from parsed payments
- Validate `pagos[].detalleFinalizadora` matches payment type
- Cross-reference cupom across 3 sources: roteiro (Cupom/SAT/ECF/NFCE) + JSON (`movimiento.numero`)
- Handle **TWO JSON formats**: wrapped in `movimiento` OR flat at root
- Use helpers `_extrair_cupom_json()` and `_extrair_pagos_json()` for both formats

### IV. Validator Chain Priority — NO Early Returns (NON-NEGOTIABLE)
Collect ALL validation results first, then apply priority at end:
1. **Partner observation (col U / Observacoes.1)** → REVISAO (overrides ALL)
2. **Special cases** (multi-tender, acréscimo, desconto, cancelar item, pesável, troco) → REVISAO
3. **NOT_RUN** (teste 26)
4. **Hard errors** → ERRO/ERRO_PAGAMENTO/ERRO_VALOR/ERRO_ITENS/ERRO_CONSISTENCIA
5. **OK** → OK

Early returns in validator chain skip later validation logic and priority logic — PROHIBITED.

### V. Test-Driven Development (NON-NEGOTIABLE)
- **NO production code without failing test first** — Red-Green-Refactor cycle mandatory
- Write test → Watch it fail → Write minimal code to pass → Refactor
- Test-first forces edge case discovery before implementing
- Tests use real code, not mocks (unless truly unavoidable)
- If test passes immediately, you're testing existing behavior — fix the test

### VI. Systematic Debugging (NON-NEGOTIABLE)
Every bug goes through 4 phases — skipping produces unreliable fixes:
1. **Root Cause Investigation**: Read errors, reproduce, check recent changes, gather evidence, trace data flow
2. **Pattern Analysis**: Find working examples, compare, identify differences, understand dependencies
3. **Hypothesis & Testing**: Form single hypothesis, test minimally, verify before continuing
4. **Implementation**: Create regression test, fix root cause, verify fix

**Rule of Three**: If 3+ fixes fail → STOP and question architecture (discuss with user)

### VII. No Fix Without User Approval (NON-NEGOTIABLE)
Mandatory flow: **Debug → Inform → Wait for approval → Apply fix**
Prevents wasted rebuilds and ensures user controls direction.

### VIII. Excel & Data Integrity
- **Duplicate columns**: Use `_first_nonempty(vals, header, key)` — Observacoes appears twice, pick last non-empty (col 20 has actual notes)
- **Deduplication**: Track `seen_tests` set; skip duplicate test IDs (template has 10, 11 twice)
- **Official source**: `TEMPLATE_COM_BIN_NOVO.xlsx` aba `ETAPA 1` (27 tests) — NOT `roteiro_testes.csv`
- **Brazilian decimals**: Comma as decimal separator (R$ 149,065 => 149.065)

### IX. Regex Bug Fix (CRITICAL - Already Applied)
Multiple payment detection broken by double-backslash:
```python
# BROKEN: matches literal \s
parts = re.split(r'\\s*\\+\\s*|\\s+e\\s+', low)
# FIXED: matches whitespace
parts = re.split(r'\s*\+\s*|\s+e\s+', low)
# Files: run_full_validation.py:370, gui_app_standalone.py:624
```

---

## Technology Stack Constraints

- **Python 3.10+** (package requires-python >=3.10)
- **pandas >=2.0, openpyxl >=3.1** for Excel handling
- **tkinter/ttk** for GUI (standard library)
- **PyInstaller** for single-file .exe builds
- **pytest, pytest-cov, pytest-snapshot** for testing
- **black, ruff** for formatting/linting

---

## Development Workflow

### Standard Feature/Bug Cycle
1. **Issue**: User reports bug or requests feature
2. **Reproduce**: Run headless test to see current distribution
3. **Debug**: Systematic debugging (4 phases) to find root cause
4. **Propose**: Present findings + proposed fix to user
5. **Approve**: Wait for explicit user approval
6. **Implement**: Apply fix to `gui_app_standalone.py` + `run_full_validation.py` + `src/validaai/validators.py` (if needed)
7. **Verify**: Re-run headless, confirm distribution matches target
8. **Rebuild**: Kill exe, `pyinstaller --clean`, verify timestamp
9. **Test**: Run full test suite (`pytest tests/`)

### Adding New Validation Rules
1. Add rule to `_validate_special_cases` in BOTH `gui_app_standalone.py` and `run_full_validation.py`
2. Add corresponding test to `tests/test_etapa1_roteiro.py` (TDD)
3. Run headless to verify distribution impact
4. Rebuild exe only after headless matches target

---

## Quality Gates

| Gate | Command | Must Pass |
|------|---------|-----------|
| Unit tests | `pytest tests/test_etapa1_roteiro.py -v` | 27/27 pass |
| Snapshot tests | `pytest tests/test_snapshots.py -v` | 15/15 pass |
| Payment labels | `pytest tests/test_payment_labels.py -v` | 4/4 pass |
| Partner JSON | `pytest tests/test_partner_json_loader.py -v` | 3/3 pass |
| Linting | `ruff check src/` | 0 errors |
| Formatting | `black src/ --check` | 0 diffs |
| Type check | `mypy src/` | 0 errors |

---

## Governance

- **This Constitution supersedes all other practices**
- **Amendments require**: Documentation of change, user approval, migration plan for existing code
- **All PRs/reviews must verify compliance** with Core Principles I-VI
- **Complexity must be justified** — YAGNI, start simple
- Use this Constitution as runtime development guidance

**Version**: 1.0.0 | **Ratified**: 2026-06-19 | **Last Amended**: 2026-06-19