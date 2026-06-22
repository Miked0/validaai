# Feature Specification: Item Parser Enhancement

**Feature Branch**: `001-item-parser-enhancement`

**Created**: 2026-06-19

**Status**: Draft

**Input**: User description: "O parser de itens é o componente mais crítico do MVP. Precisa parsear corretamente: '3 x 7894904500383', '7894904500383 + 7894904500383', '3.579 x PESABLE', cancelamentos de item e unidade. Deve retornar lista estruturada com codigo, quantidade, tipo (ean/pesavel/outro), quantidade_esperada para pesáveis e flag cancelar_item."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Parse Multiplication Format (Priority: P1)
Parse strings like "3 x 7894904500383" into structured items with codigo, quantidade, tipo.

**Why this priority**: Core functionality - majority of test cases use this format. All 27 ETAPA 1 tests need item parsing.

**Independent Test**: Can be fully tested by calling `ItemParser().parse_items()` with various multiplication strings and verifying output structure.

**Acceptance Scenarios**:
1. **Given** item string "3 x 7894904500383", **When** parsed, **Then** returns `[{"codigo": "7894904500383", "quantidade": 3.0, "tipo": "ean"}]`
2. **Given** item string "2 x 7891000010860 + 3.579 x PESABLE", **When** parsed, **Then** returns two items: EAN with qty 2.0 and PESAVEL with qty 3.579
3. **Given** item string "5 x 7894904500383 + 4 x 7894904578207", **When** parsed, **Then** returns two EAN items with correct quantities

### User Story 2 - Parse Addition Format (Priority: P1)
Parse strings like "7894904500383 + 7894904500383" (repeated items without explicit multiplier).

**Why this priority**: Used in tests 2, 3, 5, 8 - multiple repeated items.

**Independent Test**: Can be tested independently by passing addition-format strings to parser.

**Acceptance Scenarios**:
1. **Given** "7894904500383 + 7894904500383", **When** parsed, **Then** returns two items each with qty 1.0
2. **Given** "1 x 7894904003495 + 4 x 7894904003495 + 4 x 7894904003495", **When** parsed, **Then** returns three items (1 + 4 + 4 = 9 total qty for same EAN)

### User Story 3 - Parse Pesável Items (Priority: P1)
Parse "3.579 x PESABLE" or "3,579 * PESABLE" with decimal quantities.

**Why this priority**: Critical for tests 1, 16, 25 - pesável items have special validation rules (REVISAO status). Must correctly identify tipo='pesavel' and store quantidade_esperada.

**Independent Test**: Test parser output for pesável strings, verify tipo and quantidade_esperada fields.

**Acceptance Scenarios**:
1. **Given** "3.579 x PESABLE", **When** parsed, **Then** returns item with tipo="pesavel", quantidade=3.579, quantidade_esperada=3.579
2. **Given** "357.9 x PESABLE", **When** parsed, **Then** returns item with quantidade=357.9 (test 25 - incorrect format triggers ERRO in validator)
3. **Given** "3,579 * PESABLE", **When** parsed, **Then** handles comma decimal separator correctly

### User Story 4 - Parse Cancelamento Item (Priority: P2)
Parse cancelamento patterns: "7891000029329 (Cancelar este ultimo item)" and "6 x 7896079500175(Cancelar 1 unidade)".

**Why this priority**: Tests 23, 24 - cancelamento de item triggers REVISAO status. Must set cancelar_item flag.

**Independent Test**: Pass cancelamento strings, verify cancelar_item=True in output.

**Acceptance Scenarios**:
1. **Given** "2 x 7891000010860 + 1 x 7891000029329 (Cancelar este ultimo item)", **When** parsed, **Then** second item has cancelar_item=True
2. **Given** "6 x 7896079500175(Cancelar 1 unidade)", **When** parsed, **Then** item has cancelar_item=True

### User Story 5 - Handle Annotations in Items (Priority: P2)
Ignore annotations like "$5 de acrescimo na linha 1" within item strings.

**Why this priority**: Test templates include these annotations that should not break parsing.

**Independent Test**: Pass strings with annotations, verify they don't affect parsed items.

**Acceptance Scenarios**:
1. **Given** "4 x 7894904573394 + 1 x 7891149103119 $5 de acrescimo na linha 1", **When** parsed, **Then** returns two items, annotation ignored

### User Story 6 - Parse Invalid EAN (Priority: P2)
Handle 19-digit EAN in test 26: "2 x 1003607622300391065" → tipo="ean_invalido"

**Why this priority**: Test 26 validates invalid EAN handling.

**Independent Test**: Pass 19-digit EAN string, verify tipo="ean_invalido".

**Acceptance Scenarios**:
1. **Given** "2 x 1003607622300391065", **When** parsed, **Then** returns item with tipo="ean_invalido", codigo="1003607622300391065"

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST parse multiplication format "N x CODIGO" where N is integer or decimal (comma or dot)
- **FR-002**: System MUST parse addition format "CODIGO + CODIGO" as qty 1 each
- **FR-003**: System MUST parse mixed format "N x CODIGO + M x CODIGO"
- **FR-004**: System MUST identify pesável items by "PESABLE"/"PESAVEL" keyword → tipo="pesavel"
- **FR-005**: System MUST identify regular EAN (8-13 digits) → tipo="ean"
- **FR-006**: System MUST identify 19-digit EAN → tipo="ean_invalido"
- **FR-007**: System MUST detect "(Cancelar ...)" pattern and set cancelar_item=True
- **FR-008**: System MUST detect "(Cancelar N unidade)" pattern and set cancelar_item=True
- **FR-009**: System MUST strip annotations like "$5 de acrescimo na linha 1" from item strings
- **FR-010**: System MUST support both "x" and "*" as multiplication operators
- **FR-011**: System MUST support comma and dot as decimal separators for quantities
- **FR-012**: System MUST return structured list with fields: codigo, quantidade, tipo, quantidade_esperada (pesável), cancelar_item
- **FR-013**: System MUST handle empty/None input gracefully → empty list

### Key Entities

- **ParsedItem**: Represents one parsed item with attributes:
  - codigo: str (EAN or "PESABLE")
  - quantidade: float (parsed quantity)
  - tipo: str (enum: "ean" | "pesavel" | "ean_invalido" | "outro")
  - quantidade_esperada: float (for pesável, same as quantidade)
  - cancelar_item: bool (True if cancelamento pattern detected)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 27 ETAPA 1 test cases parse items correctly (validated by `tests/test_etapa1_roteiro.py`)
- **SC-002**: Pesável items in tests 1, 16, 25 have correct quantidade_esperada (3.579, 3.579, 357.9)
- **SC-003**: Cancelamento items in tests 23, 24 have cancelar_item=True
- **SC-004**: Invalid EAN in test 26 has tipo="ean_invalido"
- **SC-005**: Parser handles all item string variations in TEMPLATE_COM_BIN_NOVO.xlsx ETAPA 1

---

## Assumptions

- Input strings come from Excel column "Itens da venda" / "ARTICULOS MOVIMIENTO" / "Itens"
- Brazilian decimal format uses comma (3,579) but parser must also handle dot (3.579)
- "PESABLE" and "PESAVEL" are interchangeable keywords for pesável items
- Annotations starting with "$" are metadata, not part of item specification
- Cancelamento patterns only appear at end of item part (after "+")
- No nested parentheses in cancelamento patterns
- Parser does NOT validate business rules (that's validator's job) — only structural parsing

---

## Clarifications Needed

- **FR-014**: Should parser consolidate repeated EANs (e.g., "1 x EAN + 4 x EAN" → single item qty 5)? Currently returns separate items. [NEEDS CLARIFICATION: consolidation is done at validator/business level, not parser]