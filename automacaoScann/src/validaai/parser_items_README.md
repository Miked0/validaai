# Módulo: Parser Items (`src/validaai/parser_items.py`)

**Versão:** 2.1.0  
**Responsável:** ValidaAI Team  
**Status:** Produção

---

## 1. Objetivo do Módulo

Transformar a string bruta de itens do roteiro (`itens_da_venda`) em **estruturas tipadas** com quantidades, tipos, preços reais (via catálogo) e identificação de produtos pesáveis.

---

## 2. Responsabilidade Principal

| Responsabilidade | Detalhe |
|------------------|---------|
| **Parse de Strings Complexas** | `3 x EAN`, `EAN + EAN`, `3.579 x PESABLE`, `EAN (Cancelar item)` |
| **Identificação de Tipo** | `ean` (8-13 dígitos), `pesavel` (PESABLE/PESAVEL), `ean_invalido` (19 dígitos), `outro` |
| **Lookup de Preços Reais** | Usa `product_catalog` do Reader → `preco_unitario`, `descricao` |
| **Quantidades Esperadas** | Para pesáveis, armazena `quantidade_esperada` para validação posterior |
| **Cancelamentos** | Detecta `(Cancelar este ultimo item)` e `(Cancelar N unidade)` |

---

## 3. Funcionalidades Existentes

| Funcionalidade | Método | Formatos Suportados |
|----------------|--------|---------------------|
| `parse_items()` | Público | Entry point - recebe `test_dict`, retorna cópia enriquecida |
| `_parse_item_string()` | Privado | Core parser regex-based |
| `_determine_item_type()` | Privado | Classifica código → `ean`/`pesavel`/`ean_invalido`/`outro` |

### Formatos de Entrada Suportados

| Formato | Exemplo | Resultado |
|---------|---------|-----------|
| Quantidade × EAN | `4 x 7894904573387` | `{'codigo': '7894904573387', 'quantidade': 4, 'tipo': 'ean'}` |
| EANs simples | `7894904573387 + 7894904573387` | 2 itens, qtd=1 cada |
| Pesável | `3.579 x PESABLE` | `{'codigo': 'PESABLE', 'quantidade': 3.579, 'tipo': 'pesavel'}` |
| Cancelar item | `7891000029329 (Cancelar este ultimo item)` | `cancelar_item: True` |
| Cancelar unidade | `6 x 7896079500175(Cancelar 1 unidade)` | `cancelar_item: True` |
| Acréscimo linha | `4 x 7894904573394 + $4 de acrescimo na linha` | Ignora `$4...` (regex remove) |

---

## 4. Dependências

### Internas
- Nenhuma (módulo independente)

### Externas
| Dependência | Uso |
|-------------|-----|
| `re` (stdlib) | Regex parsing |
| `typing` | Type hints |

---

## 5. Módulos Relacionados

| Módulo | Relação | Dados |
|--------|---------|-------|
| `reader.py` | **Fornecedor** | Fornece `product_catalog` via `test_dict['product_catalog']` |
| `api_sales.py` | **Consumidor** | Usa `itens_parseados` + `pesaveis_esperados` no `build_sale_json()` |
| `validators.py` | **Consumidor** | Valida Etapa 1 (EANs, quantidades, pesáveis) |

---

## 6. Pontos de Entrada

```python
from validaai import ItemParser

parser = ItemParser()
result = parser.parse_items(test_dict)

# test_dict deve conter:
# - 'itens_da_venda': str (ex: "4 x 7894904573387")
# - 'product_catalog': dict (opcional, do Reader)

# Resultado (cópia enriquecida):
{
    ...campos originais...,
    'itens_parseados': [
        {'codigo': '7894904573387', 'quantidade': 4.0, 'tipo': 'ean', 
         'preco_unitario': 2.85, 'descricao': 'PATE SEARA...', 
         'cancelar_item': False}
    ],
    'pesaveis_esperados': {'PESABLE': 3.579}
}
```

---

## 7. Fluxos Importantes

### 7.1 Pipeline de Parsing
```
parse_items(test_dict)
    → _parse_item_string(itens_raw, product_catalog)
        → Split por '+'
        → Para cada parte:
            1. Detecta cancelamento: regex `\(cancelar[^)]*\)`
            2. Remove anotações: `$5 de acrescimo...`
            3. Match quantidade: `^(\d+[.,]?\d*)\s*[x*]\s*(.+)$`
            4. Determina tipo: _determine_item_type(codigo)
            5. Lookup preço: product_catalog[codigo].get('preco', 0.0)
            6. Se pesável → armazena em pesaveis_esperados[codigo] = qtd
    → Retorna (parsed_items[], pesaveis_esperados{})
```

### 7.2 Classificação de Tipo (`_determine_item_type`)
| Código | Tipo Retornado |
|--------|----------------|
| `PESABLE`, `PESAVEL`, `WEIGHT`, `PESO` | `pesavel` |
| `^\d{8,13}$` (EAN válido) | `ean` |
| `^\d{19}$` (EAN inválido teste) | `ean_invalido` |
| Outros | `outro` |

---

## 8. Arquivos Críticos

| Arquivo | Função |
|---------|--------|
| `src/validaai/parser_items.py` | **Único arquivo** (166 linhas) |

---

## 9. Observações Técnicas e Débitos

### 🟢 Pontos Fortes
- **Regex robusta**: Suporta vírgula/ponto decimal, `x` ou `*`, anotações complexas
- **Imutabilidade**: Retorna cópia do `test_dict` enriquecida
- **Extensível**: `_determine_item_type` isolado para novos tipos
- **Catálogo opcional**: Funciona sem `product_catalog` (preço=0.0)

### 🟡 Débitos Técnicos
| Débitos | Descrição | Prioridade |
|---------|-----------|------------|
| **Regex Frágil para Pesáveis** | `PESABLE` hardcoded; não detecta variações locale | P2 |
| **Cancelamento Parcial** | `Cancelar 1 unidade` detectado mas não quantifica | P2 |
| **Preço Zero Silencioso** | EAN não no catálogo → `preco=0.0` sem alerta | P3 |
| **Descrição Vazia** | Catálogo sem descrição → string vazia silenciosa | P3 |

### 🔴 Riscos
- **Dependência de Catálogo**: Se `reader.py` mudar estrutura do `product_catalog`, quebra lookup
- **Hardcoded `PESABLE`**: Se Scanntech mudar nomenclatura, parser falha silenciosamente

---

## 9.1 Hipóteses de Melhoria

| Hipótese | Impacto |
|----------|---------|
| Config `pesavel_keywords: ["PESABLE", "PESAVEL", "KG", "KILO"]` em YAML | Flexibilidade multi-parceiro |
| Retornar `preco_fonte: 'catalogo' | 'fallback_zero'` para auditoria | Rastreabilidade |
| Validar EAN checksum (GTIN-13) | Qualidade de dados |

---

**Fim do README - Módulo Parser Items**  
*Última atualização: 2026-06-21 | Versão 2.1.0*