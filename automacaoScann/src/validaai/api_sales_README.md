# Módulo: API Sales (`src/validaai/api_sales.py`)

**Versão:** 2.1.0  
**Responsável:** ValidaAI Team  
**Status:** Produção

---

## 1. Objetivo do Módulo

Construir e validar **JSONs conformes à API 3.0 da Scanntech** para o endpoint `agregarMovimiento`, usando dados normalizados do pipeline + catálogo de produtos com preços reais.

---

## 2. Responsabilidade Principal

| Responsabilidade | Detalhe |
|------------------|---------|
| **Builder JSON API 3.0** | `build_sale_json()` → `{'movimiento': {...}}` completo |
| **Validador Estrutura** | `validate_sale_json()` → `OK` / `ALERTA_JSON` / `ERRO_JSON` |
| **Carregador Partner JSONs** | `_load_partner_jsons()` lê export_auditoria.xlsx (coluna Request) |
| **Preços Reais** | Usa `product_catalog` do Reader → `importeUnitario` exato do catálogo |
| **Cálculo Total Preciso** | Soma `importe` dos itens (mais preciso que subtotal do roteiro) |

---

## 3. Funcionalidades Existentes

| Funcionalidade | Método | Descrição |
|----------------|--------|-----------|
| `build_sale_json()` | Público | Constrói payload API 3.0 completo |
| `validate_sale_json()` | Público | Valida estrutura + campos obrigatórios + tipos |
| `_load_partner_jsons()` | Privado | Carrega JSONs do parceiro do export_auditoria.xlsx |
| `_parse_itens()` | Privado | Parse itens + lookup preço catálogo |
| `_codigo_pagamento()` | Privado | String → código API (9/10/13/14/15) |
| `_canal_venda()` | Privado | Detecta canal 1/2/3 via observações |
| `_eh_cancelamento()` | Privado | Detecta "cancelar venda" nas observações |

---

## 4. Estrutura JSON Gerada (API 3.0)

```json
{
  "movimiento": {
    "fecha": "2026-07-01T15:01:37.000-0300",
    "numero": "400",
    "descuentoTotal": 6.4,
    "recargoTotal": 0.0,
    "codigoMoneda": "986",
    "cotizacion": 1.00,
    "total": 7.85,
    "cancelacion": false,
    "documentoCliente": "",
    "codigoCanalVenta": 1,
    "descripcionCanalVenta": "VENDA NA LOJA",
    "detalles": [
      {
        "codigoArticulo": "123",
        "codigoBarras": "7894904573394",
        "descripcionArticulo": "PATE SEARA FRANGO 100G",
        "cantidad": 2.0,
        "importeUnitario": 2.85,
        "importe": 5.70,
        "impuesto": 0.0,
        "descuento": 3.2,
        "recargo": 0.0,
        "datosExtra": ""
      }
    ],
    "pagos": [
      {
        "codigoTipoPago": 14,
        "codigoProveedorQR": 1,
        "codigoBanco": 0,
        "descripcionBanco": "",
        "codigoMoneda": "986",
        "importe": 7.85,
        "cotizacion": 1.00,
        "documentoCliente": "",
        "bin": "",
        "codigoTarjeta": "",
        "numeroAutorizacao": "",
        "ultimosDigitosTarjeta": "",
        "detalleFinalizadora": "PIX",
        "cuotas": 0
      }
    ],
    "deliveryPostalCode": ""
  }
}
```

---

## 5. Dependências

### Internas
- Nenhuma direta (módulo independente)

### Externas
| Dependência | Uso |
|-------------|-----|
| `pandas` | Leitura `export_auditoria.xlsx` (múltiplas abas) |
| `json`, `re`, `datetime`, `decimal` | Stdlib |
| `typing` | Type hints |

---

## 6. Módulos Relacionados

| Módulo | Relação | Dados |
|--------|---------|-------|
| `reader.py` | **Fornecedor** | `product_catalog` para preços reais |
| `parser_items.py` | **Fornecedor** | `itens_parseados` (já parseados) |
| `payments.py` | **Fornecedor** | `pagamentos[]`, `tem_pos`, `canal_venda`, `codigo_tipo_pago` |
| `validators.py` | **Bidirecional** | Validador usa builder para JSON ideal; builder valida JSONs parceiro |
| `exporters.py` | **Consumidor** | Exporta `sale_json` gerado |

---

## 7. Pontos de Entrada

```python
from validaai import APISalesBuilder

builder = APISalesBuilder()

# 1. Construir JSON ideal para um teste
sale_json = builder.build_sale_json(
    teste=1,
    itens_da_venda="4 x 7894904573387",
    pagamento="Dinheiro",
    subtotal=11.4,
    desconto=6.4,
    total=5.0,
    observacoes="1 Promo [Paga $5]",
    numero_cupom="399",
    tipo_promo="PRECIO_FIJO",
    product_catalog=product_catalog  # do Reader
)

# 2. Validar JSON do parceiro (auditoria)
check = builder.validate_sale_json(partner_json)
# {'status': 'OK'|'ALERTA_JSON'|'ERRO_JSON', 'motivo': '...', 'alertas': [...]}

# 3. Carregar JSONs do parceiro do arquivo de auditoria
partner_jsons = builder._load_partner_jsons('export_auditoria.xlsx')
# {'399': {...}, '400': {...}, ...}
```

---

## 8. Fluxos Importantes

### 8.1 Build Sale JSON (`build_sale_json`)

```
build_sale_json()
    1. Converte subtotal/desconto/total para Decimal
    2. Detecta cancelamento: _eh_cancelamento(observacoes)
    3. Determina canal: _canal_venda(observacoes, pagamento)
    4. Parse itens: _parse_itens(itens_da_venda, product_catalog)
        → Para cada item: lookup preço no catálogo
        → Calcula importe = preco_unitario * quantidade
        → Garante campos: importeUnitario, importe, impuesto=0, descuento=0, recargo=0
    5. Calcula total_valor = soma(importe dos itens)
       Se tot_dec > 0 → usa total do roteiro (pode ter desconto/acréscimo global)
    6. Processa pagamentos:
       Se pagamentos[] fornecido (do PaymentNormalizer):
           Divide total_valor entre pagamentos
           Para cada: codigoTipoPago, detalleFinalizadora, bin (se cartão+promo)
       Senão: fallback para string 'pagamento' simples
    7. Monta detalhes[] com todos campos obrigatórios API
    8. Monta movimento{} com estrutura completa
    9. Retorna {'movimiento': movimiento}
```

### 8.2 Preços Reais do Catálogo (Diferencial)

```python
# _parse_itens usa product_catalog do Reader:
preco_unitario = product_catalog.get(codigo_limpo, {}).get('preco', 0.0)
descricao = product_catalog.get(codigo_limpo, {}).get('descricao', '')

# Isso garante importeUnitario = preço tabelado real (não estimado)
# importe = preco_unitario * quantidade (preciso centavo a centavo)
```

### 8.3 Validação JSON Parceiro (`validate_sale_json`)

Aceita **dois formatos**:
1. **Wrapped**: `{'movimiento': {...}}` (formato API oficial)
2. **Flat**: `{...}` (direto no root, como vem na auditoria)

Valida:
- Campos obrigatórios: `fecha, numero, descuentoTotal, recargoTotal, codigoMoneda, cotizacion, total, cancelacion, detalles, pagos`
- `codigoMoneda == "986"` (string, não int)
- `cotizacion == 1.00`
- Casas decimais ≤ 2 em valores monetários
- Cancelamento → número com hífen (`-XXXX`)
- `detalles[]` com `codigoArticulo, codigoBarras, cantidad` obrigatórios

---

## 9. Arquivos Críticos

| Arquivo | Função |
|---------|--------|
| `src/validaai/api_sales.py` | **Único arquivo** (549 linhas) |

---

## 10. Observações Técnicas e Débitos

### 🟢 Pontos Fortes
- **Preços Reais**: Único módulo que usa catálogo "Produtos a cadastrar" para `importeUnitario` exato
- **Total Preciso**: Soma `importe` dos itens (evita erro de arredondamento do subtotal)
- **Dupla Entrada**: Aceita JSON wrapped e flat (compatibilidade auditoria)
- **Cancelamento Correto**: Número com hífen `-XXXX` + `cancelacion: true` + timestamp = venda original
- **BIN Inteligente**: Extrai do cupom apenas para cartão + promoção ativa

### 🟡 Débitos Técnicos
| Débitos | Descrição | Prioridade |
|---------|-----------|------------|
| **_load_partner_jsons no Módulo Errado** | Deveria estar em loader dedicado, não no builder | **P1** |
| **Hardcoded `CODIGO_INTERNO_POR_EAN`** | Mapeamento EAN→código interno fixo (123, 124, 125) | **P2** |
| **Banco não Detectado** | `codigoBanco` sempre 0, `descripcionBanco` vazio | **P2** |
| **`_load_partner_jsons` Duplicado** | Existe em `api_sales.py` E em `gui_app_standalone.py` | **P1** |
| **Pandas Obrigatório para Auditoria** | `pd.read_excel` sem fallback stdlib | **P2** |

### 🔴 Riscos
- **Mudança API Scanntech**: Campos novos/obrigatórios quebram validação
- **Mapeamento EAN→Código Interno**: Fixado em 3 EANs (123, 124, 125) - não escala
- **Coupling Circular**: `validators` usa `api_sales` para partner_jsons; `api_sales` valida JSONs que validador gerou

---

## 9.1 Hipóteses de Melhoria

| Hipótese | Impacto |
|----------|---------|
| `PartnerJSONLoader` class separada em `loaders/` | Quebra circular dependency, testável |
| Config `ean_to_codigo_interno.yaml` versionado | Multi-parceiro, deploy-free |
| Detecção banco via regex `banco\s+(\w+)` em observações | Preenche `codigoBanco`/`descripcionBanco` |
| Validação schema JSON Schema (Draft 7) | Contrato formal, auto-documentado |

---

**Fim do README - Módulo API Sales**  
*Última atualização: 2026-06-21 | Versão 2.1.0*