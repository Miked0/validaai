# ValidaAI PDV Test Automation

> Automação de validação de roteiros de teste para homologação de sistemas PDV (Point of Value) conforme requisitos Scanntech/ScannTech.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)

## 📋 Visão Gerale

O ValidaAI é um sistema de automação para validação de casos de teste de PDV contra regras de negócio específicas do Scanntech. O projeto foca na validação de transações fiscais, pagamentos e promoções através de múltiplas etapas de verificação.

Este repositório contém o núcleo do validador (`validaai-core`) e a aplicação standalone gerada pelo PyInstaller para execução em ambientes de produção.

## 🔑 Principais Características

- **Validação em Múltiplas Etapas**: Verificação sequencial de regras de negócio (Etapa 1→2→3→4→5)
- **Workflow Headless-Driven**: Ajuste de regras via `headless_official_test.py` seguido de rebuild do executável
- **Validação Estrrita de JSON Parceiro**: Validação direta contra JSONs de auditoria fornecidos pelo parceiro
- **Cadeia de Validadores com Prioridade**: Ordem específica de aplicação das validações sem retornos antecipados
- **Suporte a Múltiplos Formatos JSON**: Lida com estruturas JSON tanto aninhadas quanto planas
- **Pipeline de Exportação**: Geração de relatórios em Excel, CSV, JSON e HTML (auto-contenido com Chart.js)
- **Teste de Snapshot**: 15 testes couvrant todos os exportadores usando pytest-snapshot
- **Agendamento Integrado**: Validações cron-based com retentativas e notificações (Email/Slack)

## 📂 Estrutura do Projeto

```
validaai/
├── src/
│   └── validaai/                 # Pacote principal do validador
│       ├── __init__.py
│       ├── validators.py         # Lógica de validação central
│       ├── parser_items.py       # Parse de itens do PDV
│       ├── payments.py           # Normalização de pagamento
│       ├── exporters/            # Módulos de exportação
│       └── gui/                  # Componentes da interface
├── design/                       # Tokens de design do sistema
│   └── tokens.json
├── gui_app_standalone.py         # Entrypoint para PyInstaller
├── headless_official_test.py     # Script para ajuste headless de regras
├── run_full_validation.py        # Orquestrador de validação completa
├── ValidaAI.spec                 # Configuração do PyInstaller
├── pyproject.toml                # Dependências e metadata
├── input/                        # Diretório para arquivos de entrada
│   ├── templates/                # Templates Excel/CSV
│   └── audit/                    # JSONs de auditoria do parceiro
└── output/                       # Diretório para resultados
    ├── excel/
    ├── csv/
    ├── json/
    └── html/
```

## ⚙️ Como Funciona

### Workflow de Desenvolvimento (Headless-Driven Rebuild)

1. **Ajuste de Regras**: Modifique a validação em `headless_official_test.py` até atingir a distribuição alvo (~10 OK, ~18 REVISAO, ~1 ERRO/NOT_RUN)
2. **Rebuild do Executável**:
   ```bash
   pkill -f "ValidaAI.exe"  # Garante que nenhum processo antigo está rodando
   python -m PyInstaller ValidaAI.spec --clean  # Rebuild limpo
   ```
3. **Verificação**: Confirme que o novo executável foi gerado com timestamp atual

### Validação de JSON Parceiro (Requisito Crítico)

Quando fornecido um export de auditoria:
- Valide o JSON do parceiro **diretamente** - nenhum fallback para geração interna
- Ausência do JSON do parceiro = resultado ERRO
- Valide `pagos[].codigoTipoPago` contra códigos esperados
- Valide `pagos[].detalleFinalizadora` contra tipo de pagamento
- Faça cross-reference do `cupom` entre 3 fontes:
  - roteiro(Cupom/SAT/ECF/NFCE)
  - JSON(movimiento.numero)
- Suporte a dois formatos JSON:
  - Envolvido em `'movimiento'`
  - Plano na raiz do objeto

### Cadeia de Validadores (Ordem de Prioridade)

1. **Observação do Parceiro** (col U) → REVISAO (sobrescreve TUDO)
2. **Casos Especiais** (multi-tender, acréscimo, desconto, cancelar item, pesável, troco) → REVISAO
3. **NOT_RUN** (teste 26)
4. **Erros Críticos** → ERRO/ERRO_PAGAMENTO/ERRO_VALOR
5. **OK** → OK

*Nota: Todos os resultados são coletados primeiro, então a prioridade é aplicada no final.*

### Ajuste Iterativo de Regras

Quando o validador é muito permissivo (muitos OK):
1. Exporte JSON detalhado por teste com status + motivo
2. Identifique qual validador está gerando excesso de OK
3. Adicione regra específica em `_validate_special_cases` mapeando cenário → REVISAO
4. Re-execute `headless_official_test.py` até a distribuição bater a meta

## 🛠️ Pré-requisitos

- Python 3.8+
- Git
- Conta no Scanntech/ScannTech com acesso aos JSONs de auditoria

## 🚀 Instalação

```bash
# Clone o repositório
git clone https://github.com/Miked0/validaai.git
cd validaai

# Crie e ative um virtualenv (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Instale as dependências
pip install -e .

# Instale dependências de desenvolvimento
pip install -e ".[dev]"
```

## 🧪 Como Usar

### Validação Headless (Para Ajuste de Regras)

```bash
python headless_official_test.py
```
Este script executa todos os testes da ETAPA 1 e gera relatório detalhado com status e motivos.

### Execução Completa via PyInstaller

```bash
# Após build do executável
dist/ValidaAI.exe
```

### Validação Direta via API

```python
from validaai.validators import validate_test_case

resultado = validate_test_case(
    caminho_roto="input/templates/TEMPLATE_COM_BIN_NOVO-2.xlsx",
    caminho_json_partner="input/audit/partner_json.json",
    teste_id=1
)
print(resultado)
```

## 📊 Pipeline de Exportação

O sistema gera automaticamente os seguintes formatos em `output/`:
- **Excel**: Relatório detalhado com abas por etapa
- **CSV**: Dados tabulares para processamento externo
- **JSON**: Resultado estruturado para integração com sistemas
- **HTML**: Relatório visual auto-contido com gráficos Chart.js

## 🔬 Testes

### Executando Suite de Testes

```bash
# Testes unitários
pytest tests/

# Testes de snapshot (exportadores)
pytest tests/ -k snapshot

# Teste específico de validação headless
python headless_official_test.py
```

### Adicionando Novos Testes de Snapshot

1. Execute o validador com os parâmetros desejados
2. Salve a saída em `tests/snapshots/`
3. Use `@pytest.mark.snapshot` para comparar contra o snapshot salvo

## 📈 Métricas de Qualidade

- **Cobertura de Testes**: >85% (metas em validadores críticos)
- **Snapshot Tests**: 15 testes cobrindo todos os exportadores
- **Validação de Regras**: 27 casos de teste da ETAPA 1 totalmente documentados
- **Distribuição Alvo**: ~10 OK, ~18 REVISAO, ~1 ERRO/NOT_RUN por execução

## 🔄 Integração com Hermes Kanban

Este projeto pode ser integrado ao setup multi-profile do Hermes Agent:
- **Worker Profile**: Use `interface: cli` (obrigatório para execução headless)
- **Fluxo**: 
  1. Card entra em "PRONTO P/ RODAR" → Hermes dispara validação sequencial
  2. Atualiza status das Etapas 1-4 + Veredicto Final
  3. Preenche Job ID, timestamp e link para output
  4. Move automaticamente para "CONCLUÍDO" ou "EM REVISÃO"

## � debugging Sistemático

Siga o processo de 4 fases para todos os problemas:
1. **Root Cause**: Entenda profundamente por que o problema ocorre
2. **Pattern**: Identifique se é incidente isolado ou padrão recorrente
3. **Hypothesis**: Formule explicação testável
4. **Implementation**: Implemente fix e valide contra casos de teste

*Regra de Três*: Se 3+ tentativas de fix falham, questione a arquitetura subjacente.

## 📜 Contribuindo

1. Faça fork do projeto
2. Crie branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add: AmazingFeature'`)
4. Push para branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Diretrizes de Código
- Siga PEP 8 com exceções razoáveis para legibilidade
- Todo código novo deve ter testes unitários correspondentes
- Atualize documentação quando mudar comportamento
- Mantenha mensagens de commit claras e em português do Brasil

## 📝 Licença

Este projeto está licenciado sob os termos da licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👏 Agradecimentos

- Equipe Scanntech/ScannTech pelos requisitos detalhados e JSONs de auditoria
- Comunidade de código aberto por ferramentas como PyInstaller, pytest-sentinel e Chart.js
- Usuários finais que fornecem feedback crítico para melhoria contínua

---

**Nota Importante para Desenvolvedores**: Este projeto segue rigorosamente os princípios de TDD (Test-Driven Development). Nenhum código de produção deve ser escrito sem um teste falhando primeiro. Sempre siga o ciclo Vermelho-Verde-Refatorar.

*Desenvolvido com ❤️ para automação confiável de validação de PDV.*