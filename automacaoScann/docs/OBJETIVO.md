# Objetivo do Sistema ValidaAI

**Versão:** 2.1.0  
**Data:** 2026-06-21  
**Status:** Produção (Homologação Scanntech/ScannTech)

---

## 1. Propósito Principal

O **ValidaAI** é uma ferramenta de automação para **validação de roteiros de testes de PDV** no processo de homologação junto à **API 3.0 da Scanntech/ScannTech**.

> **Em uma frase:** Automatiza a leitura de roteiros de teste em Excel, confronta com JSONs reais de auditoria/movimentos da API, aplica regras de negócio SDD (5 estágios) e gera relatórios de conformidade para homologação de PDVs.

---

## 2. Problemas que Resolve

| Problema Anterior | Solução ValidaAI |
|-------------------|------------------|
| **Validação manual** de 60+ testes por roteiro | Pipeline automatizado: Excel → JSON API 3.0 → Regras SDD → Relatório |
| **Erros humanos** em conferência de EANs, quantidades, pagamentos | Validação programática: EAN-a-EAN, quantidade-a-quantidade, centavo-a-centavo |
| **Falsos positivos/negativos** por tolerância inadequada | Tolerância inteligente: `max(0.01, 0.011)` absorve `0.010000001` |
| **Desconhecimento do JSON real** enviado à API | Confronta roteiro vs `export_auditoria` (request) vs `export_movimentos` (promoções aplicadas) |
| **Falta de rastreabilidade** de falhas | Logging estruturado etapa-a-etapa + export Excel/CSV com evidências |
| **Retrabalho** a cada nova homologação | Roteiro padrão reutilizável + catálogo de produtos com preços reais |
| **Dependência de conhecimento tribal** | Regras SDD codificadas, documentadas e versionadas |

---

## 3. Principais Fluxos de Negócio

### 3.1 Fluxo Principal: Validação Completa (Headless)

```mermaid
graph TD
    A[Roteiro Excel] --> B[TestScriptReader]
    B --> C[Product Catalog\n(EAN → Preço/Desc)]
    B --> D[Test Cases Brutos]
    D --> E[ItemParser]
    D --> F[PaymentNormalizer]
    E --> G[Itens Parseados + Pesáveis]
    F --> H[Pagamentos Normalizados\n+ POS + Canal]
    G --> I[TestValidator\n(5 Estágios SDD)]
    H --> I
    I --> J[APISalesBuilder]
    J --> K[JSON API 3.0]
    K --> L[Validação Estrutura]
    I --> M[Resultado Final\nOK/REVISAO/ERRO]
    M --> N[ResultExporter\nExcel/CSV]
```

### 3.2 Fluxo GUI (Operador)

1. **Seleção de arquivos**: Roteiro + Export Auditoria + Export Movimentos (opcional)
2. **Configuração**: ETAPA alvo, tolerância, output path
3. **Execução**: Botão "Validar" → progress bar → resultados em tabela
4. **Análise**: Filtros por status (OK/REVISAO/ERRO), detalhes por etapa
5. **Export**: Relatório Excel com evidências para parceiro

### 3.3 Fluxo CI/CD (Futuro)

```
Git Push (tag v*) → GitHub Actions (Windows) → PyInstaller Build → Release .exe
```

---

## 4. Atores Envolvidos

| Ator | Papel | Interação |
|------|-------|-----------|
| **Analista de Homologação (QA)** | Usuário principal | Executa validações, analisa relatórios, reexecuta testes |
| **Desenvolvedor PDV** | Consumidor do relatório | Recebe lista de falhas (EAN, pagamento, valores) para correção |
| **Gerente de Projetos** | Acompanhamento | Dashboard de status (OK/REVISAO/ERRO) por parceiro |
| **Parceiro Scanntech** | Validador final | Recebe relatório de conformidade para aprovação |
| **DevOps** | Build/Deploy | Gera `.exe` via GitHub Actions, publica releases |

---

## 5. Funcionalidades Centrais

| Funcionalidade | Descrição | Módulo Principal |
|----------------|-----------|------------------|
| **Leitura Multi-formato** | Excel (.xlsx) multi-aba ETAPA 1/2/3 + CSV fallback | `reader.py` |
| **Catálogo de Produtos** | Extrai aba "Produtos a cadastrar" → EAN → preço real/descrição | `reader.py` |
| **Parse de Itens Inteligente** | Suporta `3 x EAN`, `EAN + EAN`, `3.579 x PESABLE`, cancelamentos | `parser_items.py` |
| **Normalização Pagamentos** | Mapeia strings → códigos API (9/10/13/14/15), detecta POS, multiplo, BIN | `payments.py` |
| **Pipeline SDD (5 Estágios)** | 1.Itens 2.Pagamento 3.Valores 4.Obs 5.Consolidação (prioridade) | `validators.py` |
| **Validação Legada** | Compatibilidade com `.exe` e testes headless existentes | `validators.py::validate_legacy()` |
| **Builder JSON API 3.0** | Constrói `movimiento` completo: detalles, pagos, promociones | `api_sales.py` |
| **Validador JSON Parceiro** | Confronta roteiro vs `export_auditoria` (request) vs `export_movimentos` | `api_sales.py` + `test_etapa2_movimentos.py` |
| **Export Multi-formato** | Excel (pandas) + CSV fallback, colunas padronizadas auditoria | `exporters.py` |
| **Logging Estruturado** | Etapa-a-etapa, prioridade de status, alertas, auditoria completa | `logger.py` |
| **GUI Tkinter Dark Theme** | Interface moderna, progress bar, filtros, export direto | `gui_app_standalone.py` |
| **Build .exe Automatizado** | GitHub Actions Windows + PyInstaller → Release automático | `.github/workflows/build-exe.yml` |

---

## 6. Visão de Produto

### 6.1 Posicionamento

> **ValidaAI** = "O validador definitivo para homologação Scanntech, eliminando retrabalho e garantindo conformidade 100% auditável."

### 6.2 Diferenciais Competitivos

| Diferencial | Valor |
|-------------|-------|
| **Confrontação Real** | Não simula — usa JSONs reais da auditoria/movimentos |
| **Preços Reais** | Catálogo "Produtos a cadastrar" → `importeUnitario` exato |
| **Regras SDD Codificadas** | 5 estágios, prioridade explícita, auditável |
| **Tolerância Inteligente** | `0.011` absorve ponto flutuante sem falsos positivos |
| **Cancelamentos Corretos** | Timestamp = venda original, número com hífen `-XXXX` |
| **POS Auto-detect** | Qualquer cartão → `tem_pos=True`, BIN extraído do cupom |
| **Build Automatizado** | Tag `v*` → GitHub Actions → `.exe` no Release |

### 6.3 Roadmap de Produto (Próximos 6 meses)

| Trimestre | Foco | Entregável |
|-----------|------|------------|
| **Q3 2026** | Estabilização Core | Testes 100% passing, 0 flaky, coverage >90% |
| **Q3 2026** | Desacoplamento GUI | Facade `ValidaAIService`, GUI 100% testeável |
| **Q4 2026** | Multi-parceiro | Config YAML por parceiro (mapeamentos, tolerâncias) |
| **Q4 2026** | Dashboard Web | Acompanhamento multi-homologação, histórico |
| **Q1 2027** | API REST | Endpoint `/validate` para integração CI/CD parceiros |

---

## 7. Contexto Operacional

### 7.1 Ambiente de Execução

| Componente | Detalhe |
|------------|---------|
| **Python** | 3.10+ (3.11/3.12 suportados) |
| **SO** | Windows (GUI/.exe), Linux (Headless/CI), macOS (Dev) |
| **Dependências** | `pandas>=2.0`, `openpyxl>=3pxl>=3.1` (stdlib para resto) |
| **Empacotamento** | `pip install -e .` (editable) ou `.exe` via PyInstaller |
| **Configuração** | `config/export.json` (colunas export), `design/tokens.json` (UI) |

### 7.2 Dados de Entrada Esperados

| Arquivo | Formato | Obrigatório | Descrição |
|---------|---------|-------------|-----------|
| **Roteiro** | `.xlsx` | Sim | Abas: ETAPA 1/2/3, "Produtos a cadastrar", coluna `Observacoes.1` |
| **Export Auditoria** | `.xlsx` | Sim | Colunas: `Número cupom`, `Request` (JSON), `Método=agregarMovimiento` |
| **Export Movimentos** | `.xlsx` | Opcional | Promoções aplicadas, descontos reais por item |
| **Cupons Fiscais** | `.pdf` | Opcional | Evidência visual (pasta `cupons/`) |

### 7.3 Saídas Geradas

| Saída | Formato | Uso |
|-------|---------|-----|
| **Relatório Completo** | `.xlsx` | Entrega ao parceiro/desenvolvedor |
| **Relatório Resumido** | `.csv` | Import em BI/dashboard |
| **Log Estruturado** | `.jsonl` | Auditoria técnica, debugging |
| **Executável** | `.exe` | Distribuição para QA sem Python |

### 7.4 Restrições e Limitações Conhecidas

| Limitação | Impacto | Workaround |
|-----------|---------|------------|
| **Bundled Source Trap** | Mudanças no core não atualizam `.exe` | Rebuild via `pyinstaller` ou GitHub Actions |
| **Single-threaded GUI** | Validações longas travam UI | Rodar headless para lotes grandes |
| **Mapeamentos Hardcoded** | `CODIGO_INTERNO_POR_EAN` fixo | Atualizar código + rebuild |
| **Pandas Opcional** | CSV fallback sem pandas | Instalar `pandas` para performance |
| **GUI Tkinter** | Look nativo limitado | Tema Dark customizado aplicado |

---

## 8. Métricas de Sucesso (KPIs)

| Métrica | Target Atual | Status |
|---------|--------------|--------|
| **Taxa de Automação** | 100% (0 validação manual) | ✅ |
| **Falsos Positivos** | < 1% (tolerância 0.011) | ✅ |
| **Tempo Validação 60 testes** | < 30s (headless) | ✅ |
| **Cobertura Testes Core** | > 90% | 🟡 ~85% |
| **Build .exe Sucesso** | 100% (GitHub Actions) | ✅ |
| **Tempo Build .exe** | < 10 min | ✅ |

---

## 9. Glossário de Termos

| Termo | Definição |
|-------|-----------|
| **ETAPA** | Fase do roteiro de testes (1=Básicos, 2=Promoções, 3=Avançados) |
| **Roteiro** | Planilha Excel com casos de teste padronizados |
| **Cupom/NFCE** | Identificador fiscal da venda (chave de correlação) |
| **EAN** | Código de barras do produto (GTIN-13) |
| **Pesável** | Produto vendido por peso (ex: 3.579 kg) |
| **LLEVA_PAGA** | Promoção "Leva X Paga Y" |
| **PRECIO_FIJO** | Preço fixo promocional |
| **DESCUENTO_VARIABLE** | Desconto percentual variável |
| **POS** | Terminal de pagamento (pinpad) |
| **BIN** | Primeiros 6-8 dígitos do cartão (identifica bandeira) |
| **Canal de Venda** | 1=Loja Física, 2=E-commerce, 3=Outros |
| **SDD** | Spec Driven Development (metodologia do projeto) |
| **Partner JSON** | JSON real enviado pelo PDV à API (coluna `Request` da auditoria) |
| **Movimentos** | Exportação com promoções já aplicadas (descontos reais) |

---

**Fim do Documento - Objetivo do Sistema ValidaAI**  
*Base oficial para desenvolvimento futuro no modelo SDD (Spec Driven Development)*