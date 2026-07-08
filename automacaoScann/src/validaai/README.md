# Módulo: Reader (`src/validaai/reader.py`)

**Versão:** 2.1.0  
**Responsável:** ValidaAI Team  
**Status:** Produção

---

## 1. Objetivo do Módulo

Leitura e parsing de **roteiros de teste em Excel/CSV**, extração do **catálogo de produtos** ("Produtos a cadastrar") e conversão para estrutura padronizada de dicionários Python para consumo downstream.

---

## 2. Responsabilidade Principal

| Responsabilidade | Detalhe |
|------------------|---------|
| **Leitura Multi-formato** | Excel (.xlsx) com múltiplas abas ETAPA + CSV fallback |
| **Filtro por ETAPA** | `set_etapa('ETAPA 2')` processa apenas a aba desejada |
| **Extração Catálogo** | Aba "Produtos a cadastrar" → `{EAN: {preco, descricao}}` |
| **Normalização de Colunas** | Case-insensitive, aliases (ex: "Itens da venda" ≡ "Articulos movimiento") |
| **Deduplicação Inteligente** | Mesmo nº teste em múltiplas linhas → mantém a com cupom válido (NFCE > SAT > ECF > Cupom) |
| **Filtro Linhas Instrucionais** | Ignora cabeçalhos, blocos, status "(Status)", "(Pendente)" |

---

## 3. Funcionalidades Existentes

| Funcionalidade | Método | Descrição |
|----------------|--------|-----------|
| `read_tests()` | Público | Entry point - retorna `List[Dict]` padronizado |
| `set_etapa()` | Público | Filtra aba ETAPA (ex: 'ETAPA 2') |
| `_load_product_catalog()` | Privado | Lê aba "Produtos a cadastrar" → `self.product_catalog` |
| `_read_excel_openpyxl()` | Privado | Parser principal Excel (data_only=True para fórmulas) |
| `_read_csv()` | Privado | Fallback CSV (UTF-8, latin-1, cp1252) |
| `_is_instructional_row()` | Privado | Detecta linhas de cabeçalho/bloco/instrução |
| `_get_current_block()` | Privado | Identifica "BLOCO DE TESTE: X" para contexto |

---

## 4. Dependências

### Internas
- Nenhuma (módulo base, não depende de outros do `validaai`)

### Externas
| Dependência | Obrigatória? | Uso |
|-------------|--------------|-----|
| `openpyxl` | **Sim** | Leitura/escrita `.xlsx` |
| `pandas` | Opcional | Apenas para CSV complexo (fallback stdlib `csv`) |
| `csv`, `re`, `pathlib`, `typing` | Stdlib | Parsing, regex, paths, type hints |

---

## 5. Módulos Relacionados

| Módulo | Relação | Dados Trocados |
|--------|---------|----------------|
| `parser_items.py` | **Consumidor** | Recebe `product_catalog` via `test_dict['product_catalog']` para lookup de preços |
| `payments.py` | **Consumidor** | Recebe `observacoes`, `pagamento` padronizados |
| `validators.py` | **Consumidor** | Recebe test cases já estruturados com `product_catalog` embutido |
| `api_sales.py` | **Consumidor indireto** | Usa `product_catalog` para preços reais no `build_sale_json` |

---

## 6. Pontos de Entrada

```python
# Uso básico
from validaai import TestScriptReader

reader = TestScriptReader('roteiro.xlsx')
reader.set_etapa('ETAPA 2')
tests = reader.read_tests()  # List[Dict] com 60+ testes

# Cada test_dict contém:
{
    'teste': 1,
    'tipo_promo': 'PRECIO_FIJO',
    'itens_da_venda': '4 x 7894904573387',
    'pagamento': 'Dinheiro',
    'nfce': '399',
    'product_catalog': {'7894904573387': {'preco': 2.85, 'descricao': '...'}},
    ...
}
```

---

## 7. Fluxos Importantes

### 7.1 Leitura Excel (Caminho Principal)
```
read_tests() 
    → _load_product_catalog()  # Aba "Produtos a cadastrar"
    → _read_excel_openpyxl()   # Itera abas ETAPA*
        → Detecta header (TESTE + ITENS DA VENDA)
        → Mapeia colunas por índice (case-insensitive)
        → Itera linhas, filtra instrucionais
        → Deduplica por nº teste (prioriza NFCE)
        → Extrai campos via _get_val() (ignora placeholders)
        → Injeta product_catalog em cada test_dict
```

### 7.2 Prioridade de Cupom Fiscal
```
NFCE (coluna "Numero de cupom") > SAT > ECF > Cupom explícito
Ignora: "(Status)", "None", "null", "pendente", "aguardando"
```

---

## 8. Arquivos Críticos

| Arquivo | Função |
|---------|--------|
| `src/validaai/reader.py` | **Único arquivo do módulo** (787 linhas) |
| `config/export.json` | Configuração colunas export (não usado diretamente aqui) |

---

## 9. Observações Técnicas e Débitos

### 🟢 Pontos Fortes
- **Parser robusto**: Lida com fórmulas Excel (`=A8+1`), mesclagem de colunas duplicadas, placeholders
- **Catálogo automático**: Detecta aba "Produtos a cadastrar" por palavras-chave (PRODUTO + CADASTRAR)
- **Deduplicação por teste**: Resolve problema de linhas duplicadas no template (testes 6, 7, 10, 24)

### 🟡 Débitos Técnicos
| Débitos | Descrição | Prioridade |
|---------|-----------|------------|
| **God Function** | `_read_excel_openpyxl()` tem 200+ linhas | P1 - Split em helpers |
| **Hardcoded Column Aliases** | Mapeamento de colunas espalhado em `get_col_idx()` | P2 - Externalizar para config |
| **Duplicação `_read_excel()`** | Dois métodos similares (pandas vs openpyxl) | P2 - Unificar |
| **CSV Fallback Frágil** | Detecção de delimitador básica | P3 - Melhorar sniffing |

### 🔴 Riscos
- **Bundled Source Trap**: Mudanças aqui **não atualizam o `.exe`** sem rebuild PyInstaller
- **Coupling com `product_catalog`**: Consumidores assumem estrutura `{ean: {preco, descricao}}` - mudar requer coordenação

---

## 9.1 Hipóteses de Melhoria (Não Implementadas)

| Hipótese | Impacto Estimado |
|----------|------------------|
| Extrair `ColumnMapper` class para mapeamento declarativo | Reduz 50+ linhas de `get_col_idx()` |
| Cache de workbook aberto para múltiplas leituras | Performance em validações repetidas |
| Validação de schema do catálogo (EAN único, preço > 0) | Qualidade de dados upstream |

---

**Fim do README - Módulo Reader**  
*Última atualização: 2026-06-21 | Versão 2.1.0*