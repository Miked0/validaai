# Arquitetura do Sistema ValidaAI

**Versão:** 2.1.0  
**Data:** 2026-06-21  
**Pacote:** validaai-core (pacote Python instalável via `pip install -e .`)

---

## 1. Visão Arquitetural

O **ValidaAI** é uma ferramenta de automação de testes para homologação de PDV (Ponto de Venda) junto à API 3.0 da **Scanntech/ScannTech**. O sistema valida roteiros de teste em planilhas Excel contra JSONs reais de auditoria e exportação de movimentos, garantindo conformidade com a especificação da API 3.0.

### Estrutura Geral (Clean Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                      INTERFACE LAYER                            │
│  ┌──────────────────┐  ┌────────────────────────────────────┐  │
│  │ GUI (Tkinter)    │  │ Headless CLI (run_full_validation) │  │
│  │ gui_app_standalone.py    │  run_teste2_validation.py      │  │
│  └──────────────────┘  └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Pipeline de Validação (5 Estágios SDD)                   │  │
│  │ TestValidator.validate() → Etapa1→Etapa2→Etapa3→Etapa4→5 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Reader       │ │ Parser Items │ │ Payments     │            │
│  │ (reader.py)  │ │ (parser_     │ │ (payments.   │            │
│  │              │ │  items.py)   │ │  py)         │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Validators   │ │ API Sales    │ │ Exporters    │            │
│  │ (validators. │ │ (api_sales.  │ │ (exporters.  │            │
│  │  py)         │ │  py)         │ │  py)         │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Excel I/O    │ │ JSON Parse   │ │ Logger       │            │
│  │ (openpyxl/   │ │ (stdlib)     │ │ (logger.py)  │            │
│  │  pandas)     │ │              │ │              │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Padrões Utilizados

| Padrão | Aplicação | Arquivo/Classe |
|--------|-----------|----------------|
| **Pipeline/Chain of Responsibility** | Validação em 5 estágios sequenciais | `TestValidator.validate()` |
| **Strategy** | Parsing de diferentes formatos (Excel/CSV) | `TestScriptReader._read_excel()` vs `_read_csv()` |
| **Factory** | Criação de objetos de pagamento normalizados | `PaymentNormalizer._normalize_payment_string()` |
| **Builder** | Construção de JSON API 3.0 | `APISalesBuilder.build_sale_json()` |
| **Template Method** | Validação legada vs nova SDD | `TestValidator.validate()` vs `validate_legacy()` |
| **Observer** | Logging estruturado | `ValidationLogger.log_test_result()` |
| **Decorator** | Prioridade de status (Observação Parceiro > REVISAO > ERRO > OK) | `TestValidator.validate()` linhas 176-195 |
| **Adapter** | Formato wrapped (`movimiento`) vs flat | `APISalesBuilder.validate_sale_json()` |
| **Singleton-like** | Mapeamentos de códigos de pagamento | `PaymentNormalizer.PAYMENT_MAPPING` (class attribute) |

---

## 3. Regras Arquiteturais

### 3.1 Separação de Responsabilidades (SoC)

| Camada | Responsabilidade | Não Deve |
|--------|------------------|----------|
| **Reader** | Leitura/parsing de planilhas, extração de catálogo de produtos | Conhecer regras de negócio, validar dados |
| **Parser Items** | Transformar string de itens → estruturas tipadas, lookup de preços | Validar pagamentos, construir JSON API |
| **Payments** | Normalizar strings de pagamento → códigos API, detectar POS/canal | Ler planilhas, validar itens |
| **Validators** | Aplicar regras de negócio (5 estágios), logging | Construir JSON API, exportar resultados |
| **API Sales** | Construir/validar JSON conforme API 3.0 Scanntech | Ler planilhas, aplicar regras de negócio complexas |
| **Exporters** | Serializar resultados para Excel/CSV | Validar, processar |

### 3.2 Princípios de Design

1. **Imutabilidade de Entrada**: Todos os módulos recebem `test_dict` e retornam **cópia** com campos adicionados (nunca modificam o original)
2. **Fail-Soft**: Validações retornam estruturas `{status, motivo, alertas}` em vez de lançar exceções
3. **Configuração Explícita**: Tolerâncias, mapeamentos e limites são constantes de classe, não hardcoded
4. **Logging Estruturado**: `ValidationLogger` captura etapa-a-etapa para auditoria completa
5. **Compatibilidade Dual**: Pipeline SDD (novo) + Legacy (headless/exe) coexistem

---

## 4. Convenções Técnicas

| Aspecto | Convenção |
|---------|-----------|
| **Nomenclatura Python** | `snake_case` para variáveis/funções, `PascalCase` para classes |
| **Constantes de Classe** | `UPPER_SNAKE_CASE` (ex: `PAYMENT_MAPPING`, `CODIGO_MOEDA = "986"`) |
| **Tipagem** | Type hints obrigatórios em assinaturas públicas (`Dict[str, Any]`, `Optional[List]`) |
| **Tratamento de Decimal** | `Decimal` para cálculos financeiros, `float` apenas para output/serialização |
| **Tolerância Financeira** | `effective_tolerance = max(tolerance, 0.011)` (handle 0.010000001) |
| **Strings de Pagamento** | Sempre `lower().strip()` antes de lookup em mapeamentos |
| **Colunas Excel** | Case-insensitive, primeiro match vence, fallback para índices posicionais |
| **Encoding** | UTF-8 com fallback para latin-1/cp1252 em CSV |
| **Logs** | Estruturados: `test_num, status, motivo, resumo_etapas, detalhes_etapas` |

---

## 5. Separação de Responsabilidades (Detalhada)

### 5.1 Módulos do Core (`src/validaai/`)

| Módulo | Responsabilidade Principal | Entrada | Saída |
|--------|---------------------------|---------|-------|
| `reader.py` | Leitura de roteiros Excel/CSV, extração catálogo produtos | Caminho arquivo + `etapa_filter` | `List[Dict]` com campos padronizados + `product_catalog` |
| `parser_items.py` | Parse string itens → EANs, quantidades, pesáveis, preços catálogo | `test_dict['itens_da_venda']` + `product_catalog` | `itens_parseados`, `pesaveis_esperados` |
| `payments.py` | Normalização pagamentos → códigos API, detecção POS/canal/múltiplo | `test_dict['pagamento']` + `observacoes` | `pagamento_normalizado`, `codigo_tipo_pago`, `pagamentos[]`, `tem_pos`, `canal_venda` |
| `validators.py` | Pipeline 5 estágios SDD + Legacy, prioridade de status, logging | Test dict completo (pós reader/parser/payments) | `status_final`, `motivo_status`, `etapa1-4`, `alertas` |
| `api_sales.py` | Builder/Validator JSON API 3.0 Scanntech | Dados normalizados + `product_catalog` | `{'movimiento': {...}}` ou erro detalhado |
| `exporters.py` | Export Excel/CSV resultados | Lista de test dicts validados | Arquivo `.xlsx`/`.csv` |
| `logger.py` | Logging estruturado para auditoria | Eventos de validação | Arquivo/console estruturado |
| `payment_codes.py` | Mapeamento código → label humano | Código int | Label string |

---

## 6. Fluxo de Comunicação Entre Módulos

```
┌──────────────────┐
│  TEST SCRIPT     │  (Excel/CSV)
│  (Roteiro)       │
└────────┬─────────┘
         ▼
┌──────────────────┐     ┌──────────────────────────┐
│ TestScriptReader │────▶│ product_catalog (Dict)   │
│ read_tests()     │     │ {EAN: {preco, desc}}     │
└────────┬─────────┘     └──────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE DE PROCESSAMENTO                │
│  (cada etapa recebe test_dict, retorna cópia enriquecida)  │
├──────────────────┬──────────────────┬──────────────────────┤
│ ItemParser       │ PaymentNormalizer│  (ordem independ.)   │
│ parse_items()    │ normalize_payment()                       │
│ + itens_parseados│ + codigo_tipo_pago                        │
│ + pesaveis_esp.  │ + pagamentos[]                             │
│                  │ + tem_pos, canal_venda                     │
└────────┬─────────┴────────┬────────────┴─────────────────────┘
         ▼                  ▼
┌──────────────────────────────────────────┐
│          TestValidator (5 estágios)      │
│  Etapa1: Itens (EAN, qtd, pesável)       │
│  Etapa2: Pagamento (códigos, POS, BIN)   │
│  Etapa3: Valores (subtotal, desc, total) │
│  Etapa4: Obs especiais (cancel, acresc)  │
│  Etapa5: Consolidação (prioridade)       │
└────────────┬─────────────────────────────┘
             ▼
┌──────────────────────────────────────────┐
│         APISales Builder/Validator JSON API 3.0           │
│ APISalesBuilder.build_sale_json()        │
│ + validação estrutura API                │
└────────────┬─────────────────────────────┘
             ▼
┌──────────────────────────────────────────┐
│         ResultExporter                   │
│ export() → Excel/CSV resultado final     │
└──────────────────────────────────────────┘
```

---

## 7. Dependências Críticas

### 7.1 Externas (pyproject.toml)

| Dependência | Versão | Uso |
|-------------|--------|-----|
| `pandas` | >=2.0 | Leitura Excel auditoria, export DataFrame |
| `openpyxl` | >=3.1 | Leitura/escrita `.xlsx` (reader, auditoria, export) |
| `pytest` | >=7.4 | Testes (dev) |
| `pytest-snapshot` | >=0.9.0 | Testes de snapshot (dev) |

### 7.2 Internas (Coupling)

```
reader.py
    └─▶ parser_items.py (via product_catalog no test_dict)
    └─▶ payments.py (via observacoes, pagamento no test_dict)
    └─▶ validators.py (fornece test_dict padronizado)

parser_items.py
    └─▶ api_sales.py (itens_parseados usados no build_sale_json)

payments.py
    └─▶ api_sales.py (pagamentos[], tem_pos, canal_venda)
    └─▶ validators.py (pagamento_normalizado, codigo_tipo_pago)

validators.py
    └─▶ logger.py (logging estruturado)
    └─▶ api_sales.py (validação JSON partner via partner_jsons)

api_sales.py
    └─▶ validators.py (partner_jsons para validação cruzada)
    └─▶ reader.py (product_catalog para preços reais)

exporters.py
    └─▶ validators.py (consome resultados finais)
```

### 7.3 Acoplamentos Excessivos Identificados ⚠️

| Acoplamento | Local | Risco | Mitigação Sugerida |
|-------------|-------|-------|---------------------|
| `validators.py` → `api_sales.py` + `partner_jsons` | Linha 35, 463 | Validador conhece builder API | Injetar interface `IPartnerJSONLoader` |
| `api_sales.py` → `reader.py` (product_catalog) | Linha 259-262 | Builder depende de formato do reader | Aceitar `product_catalog` como parâmetro genérico (já feito ✅) |
| `validators.py` (legacy) → 10 métodos privados | Linhas 269-272 | Cadeia rígida, difícil testar | Extrair `LegacyValidationChain` class |
| `gui_app_standalone.py` → todos os módulos core | Linhas 28-49 | GUI acoplada a implementação | Usar facade `ValidaAIService` |

---

## 8. Riscos Técnicos e Acoplamentos Importantes

### 8.1 Riscos Críticos

| Risco | Descrição | Impacto | Probabilidade |
|-------|-----------|---------|---------------|
| **Bundled Source Trap** | Mudanças em `src/validaai/` não refletem no `.exe` sem rebuild | `.exe` desatualizado | **ALTO** - Documentado no `CHECKPOINT.md` |
| **Coupling GUI↔Core** | `gui_app_standalone.py` importa e usa classes core diretamente | Mudança core quebra GUI | **ALTO** |
| **Legacy Validation Chain** | 10 métodos encadeados com side-effects | Difícil testar/debugar | **MÉDIO** |
| **Hardcoded Mappings** | `PAYMENT_MAPPING`, `CODIGO_INTERNO_POR_EAN` em classes | Mudança Scanntech requer deploy | **MÉDIO** |
| **Single-threaded GUI** | Processamento bloqueia UI | UX ruim em validações longas | **BAIXO** |

### 8.2 Violações Arquiteturais Identificadas

| Violação | Local | Descrição |
|----------|-------|-----------|
| **God Class** | `TestValidator` (1295 linhas) | Validação + logging + legacy + consolidação |
| **Feature Envy** | `validators.py` usa `api_sales.py` internamente | Validador conhece detalhes do builder |
| **Circular Dependency Risk** | `validators` ↔ `api_sales` via `partner_jsons` | Ambos se referenciam |
| **Mixed Responsibilities** | `gui_app_standalone.py` contém validação inline (linhas 950-1100) | GUI executa lógica de negócio |

---

## 9. Diretrizes para Futuras Implementações

### 9.1 Princípios Obrigatórios

1. **Não quebrar a imutabilidade**: Sempre `result = test_dict.copy()` antes de modificar
2. **Extender, não modificar**: Novas validações → novo método `_validate_etapaX()`, não editar existentes
3. **Configuração > Hardcode**: Novos mapeamentos → constantes de classe ou config YAML
4. **Testes de Snapshot**: Toda mudança em output JSON/Excel → atualizar snapshots
5. **Logging First**: Nova validação → `self.logger.log_test_result()` obrigatório

### 9.2 Roadmap de Refatoração (Prioridade)

| Prioridade | Ação | Esforço | Benefício |
|------------|------|---------|-----------|
| **P0** | Extrair `ValidaAIService` facade para desacoplar GUI | 2 dias | GUI testável, core reutilizável |
| **P0** | Mover `partner_jsons` loading para loader dedicado | 1 dia | Quebrar circular dependency |
| **P1** | Split `TestValidator` em `Stage1-5Validator` + `Consolidator` | 3 dias | Testável, extensível |
| **P1** | Mover validação inline da GUI para `TestValidator` | 2 dias | Single source of truth |
| **P2** | Externalizar mapeamentos para `config/mappings.yaml` | 1 dia | Deploy-free updates |
| **P2** | Async processing na GUI (thread pool) | 2 dias | UX não-bloqueante |

### 9.3 Padrões para Novos Módulos

```python
# Template para novo processador no pipeline
class NovoProcessador:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def processar(self, test_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Sempre retorna cópia enriquecida, nunca modifica original."""
        result = test_dict.copy()
        # ... lógica ...
        result['novo_campo'] = valor_calculado
        return result
```

### 9.4 Convenções de Versionamento

| Tipo | Exemplo | Quando |
|------|---------|--------|
| **Patch** | 2.1.0 → 2.1.1 | Bugfix, typo, ajustes de tolerância |
| **Minor** | 2.1.0 → 2.2.0 | Nova validação, novo campo export, melhoria UX |
| **Major** | 2.1.0 → 3.0.0 | Breaking API (ex: mudança estrutura JSON, remoção campos) |

---

## Apêndice: Mapa de Arquivos Principais

```
/home/ubuntu/validaai/automacaoScann/
├── src/validaai/                 # CORE PACKAGE (instalável)
│   ├── __init__.py               # Exports públicos + versão
│   ├── reader.py                 # Leitura roteiros + catálogo
│   ├── parser_items.py           # Parse itens + preços catálogo
│   ├── payments.py               # Normalização pagamentos
│   ├── validators.py             # Pipeline 5 estágios SDD + Legacy
│   ├── api_sales.py              # Builder/Validator JSON API 3.0
│   ├── exporters.py              # Export Excel/CSV
│   ├── logger.py                 # Logging estruturado
│   ├── payment_codes.py          # Código → label humano
│   └── reader_fixed.py           # Versão alternativa (WIP)
├── gui_app_standalone.py         # GUI Tkinter (entry point .exe)
├── run_full_validation.py        # Headless validation entry
├── run_teste2_validation.py      # Validação ETAPA 2 específica
├── test_etapa2_movimentos.py     # Teste integração auditoria+movimentos
├── tests/                        # Testes pytest + snapshots
├── config/export.json            # Configuração export
├── design/tokens.json            # Design system tokens
├── specs/                        # Especificações features (SDD)
├── pyproject.toml                # Config package + deps
└── CHECKPOINT.md                 # Estado atual + Known issues
```

---

**Fim do Documento - Arquitetura do Sistema ValidaAI**  
*Gerado automaticamente baseado em análise de código real (SDD v1.0)*