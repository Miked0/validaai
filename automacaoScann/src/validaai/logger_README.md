# Módulo: Logger (`src/validaai/logger.py`)

**Versão:** 2.1.0  
**Responsável:** ValidaAI Team  
**Status:** Produção

---

## 1. Objetivo do Módulo

Fornecer **logging estruturado** para auditoria completa do pipeline de validação, com suporte a níveis de log, formatação consistente e export para análise posterior.

---

## 2. Responsabilidade Principal

| Responsabilidade | Detalhe |
|------------------|---------|
| **Logging Estruturado** | Cada evento: `test_num, status, motivo, resumo_etapas, detalhes_etapas` |
| **Níveis de Log** | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| **Status de Teste** | `OK`, `REVISAO`, `ERRO`, `ERRO_ITENS`, `ERRO_PAGAMENTO`, `ERRO_VALORES`, `NOT_RUN`, `ALERTA_JSON` |
| **Output Duplo** | Console (colorido) + Arquivo (JSONL para auditoria) |
| **Contexto Rico** | Detalhes por etapa para rastreabilidade completa |

---

## 3. Funcionalidades Existentes

| Funcionalidade | Classe/Método | Descrição |
|----------------|---------------|-----------|
| `ValidationLogger` | Classe principal | Logger configurável com handlers duplos |
| `log_test_result()` | Método principal | Log completo de resultado de teste |
| `LogLevel` | Enum | `DEBUG=10`, `INFO=20`, `WARNING=30`, `ERROR=40`, `CRITICAL=50` |
| `TestStatus` | Enum | Todos os status possíveis de teste |
| `log_validation_start()` | Método | Início de validação em lote |
| `log_validation_end()` | Método | Fim com estatísticas |

---

## 4. Dependências

### Internas
- Nenhuma

### Externas
| Dependência | Uso |
|-------------|-----|
| `logging` (stdlib) | Base logging framework |
| `json` | Serialização JSONL para arquivo |
| `datetime` | Timestamps ISO 8601 |
| `enum` | Enums para LogLevel e TestStatus |
| `pathlib` | Path handling para arquivo de log |

---

## 5. Módulos Relacionados

| Módulo | Relação |
|--------|---------|
| `validators.py` | **Consumidor Principal** - Usa `ValidationLogger` em `validate()` |
| `gui_app_standalone.py` | **Consumidor** - Logs da GUI |
| `run_full_validation.py` | **Consumidor** - Headless logging |

---

## 6. Pontos de Entrada

```python
from validaai import ValidationLogger, LogLevel

# Cria logger com arquivo de saída
logger = ValidationLogger(
    log_file='logs/validacao_2026-07-01.jsonl',
    console_level=LogLevel.INFO,
    file_level=LogLevel.DEBUG
)

# Log de resultado de teste
logger.log_test_result(
    test_num=1,
    status='OK',
    motivo='Todos os campos válidos',
    resumo_etapas='Etapa 1: OK | Etapa 2: OK | Etapa 3: OK | Etapa 4: OK',
    detalhes_etapas={
        'Etapa 1 (Itens)': {'status': 'OK', 'motivo': 'EANs e quantidades conferem'},
        'Etapa 2 (Pagamento)': {'status': 'OK', 'motivo': 'Código 9 (Dinheiro) confere'},
        ...
    }
)

# Início/fim de batch
logger.log_validation_start(total_tests=60, roteiro='roteiro.xlsx')
# ... processa ...
logger.log_validation_end(ok=50, revisao=5, erro=3, not_run=2)
```

---

## 7. Formato de Log (JSONL)

```json
{
  "timestamp": "2026-07-01T15:30:45.123456",
  "level": "INFO",
  "test_num": 1,
  "status": "OK",
  "motivo": "Todos os campos válidos e consistentes",
  "resumo_etapas": "Etapa 1: OK | Etapa 2: OK | Etapa 3: OK | Etapa 4: OK",
  "detalhes_etapas": {
    "Etapa 1 (Itens)": {"status": "OK", "motivo": "EANs e quantidades conferem"},
    "Etapa 2 (Pagamento)": {"status": "OK", "motivo": "Código 9 (Dinheiro) confere"}
  },
  "test_data": {
    "teste": 1,
    "nfce": "399",
    "tipo_promo": "PRECIO_FIJO"
  }
}
```

---

## 8. Arquivos Críticos

| Arquivo | Função |
|---------|--------|
| `src/validaai/logger.py` | **Único arquivo** (~150 linhas) |

---

## 9. Observações Técnicas e Débitos

### 🟢 Pontos Fortes
- **JSONL**: Formato linha-a-linha para processamento streaming
- **Campos Ricos**: `detalhes_etapas` permite drill-down por etapa
- **Níveis Independentes**: Console e arquivo com níveis diferentes
- **Test Data Context**: Inclui `teste`, `nfce`, `tipo_promo` para correlação

### 🟡 Débitos Técnicos
| Débitos | Descrição | Prioridade |
|---------|-----------|------------|
| **Sem Rotação de Log** | Arquivo cresce indefinidamente | P2 |
| **Sem Filtro por Teste** | Não permite filtrar logs por teste específico | P3 |
| **Console Colorido Hardcoded** | ANSI codes fixos | P3 |

### 🔴 Riscos
- **Arquivo Grande**: Validações de muitos testes geram arquivos grandes

---

## 9.1 Hipóteses de Melhoria

| Hipótese | Impacto |
|----------|---------|
| Rotação por tamanho/data (`RotatingFileHandler`) | Controle de disco |
| Query API sobre logs (SQLite backend) | Análise histórica |
| Structured logging com `structlog` | Ecossistema rico |

---

**Fim do README - Módulo Logger**  
*Última atualização: 2026-06-21 | Versão 2.1.0*