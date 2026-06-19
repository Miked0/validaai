+# QA Roteiro Automation MVP
+
+Este projeto é um MVP (Minimum Viable Product) para automação da validação de roteiros de teste de um sistema de PDV (Point of Sale). Ele lê um arquivo de teste (Excel ou CSV), parseia os itens, normaliza os métodos de pagamento, valida as regras de negócio e exporta os resultados para uma planilha.
+
+## Funcionalidades
+
+- **Leitura de script de teste**: Suporta arquivos `.xlsx` e `.csv`.
+- **Parse de itens**: Converte strings como `"4 x 7894904573387"` ou `"7894904573387 + 7894904573387"` em listas estruturadas.
+- **Normalização de pagamento**: Mapeia descrições de pagamento (ex: `"Dinheiro"`, `"Cartao Debito"`) para códigos padrão.
+- **Validação de regras de negócio**:
+  - Verifica presença de identificador de teste.
+  - Valida que os itens foram parseados corretamente.
+  - Confirma que o pagamento foi mapeado.
+  - Assegura que subtotal, desconto e total são numéricos.
+  - Valida a consistência: `total ≈ subtotal - desconto` (com tolerância de 0,01).
+- **Exportação de resultados**: Gera um arquivo Excel (ou CSV como fallback) contendo os dados originais, os valores normalizados e o status de validação.
+
+## Estrutura do Projeto
+
+```
+automacaoScann/
+├── input/               # Arquivos de entrada (roteiro_testes.csv ou .xlsx)
+├── output/              # Resultados da validação
+├── src/                 # Código-fonte
+│   ├── __init__.py
+│   ├── reader.py        # Leitura do arquivo de teste
+│   ├── parser_items.py  # Parse das strings de itens
+│   ├── payments.py      # Normalização de pagamento
+│   ├── validators.py    # Validação das regras de negócio
+│   ├── exporters.py     # Exportação para Excel/CSV
+│   └── main.py          # Orquestração do fluxo
+├── test_core.py         # Script de teste rápido da funcionalidade núcleo
+└── README.md
+```
+
+## Pré‑requisitos
+
+- Python 3.8+
+- Bibliotecas opcionais (para melhor experiência):
+  - `pandas` e `openpyxl` (para leitura de Excel e exportação nativa)
+  - Caso não estejam instaladas, o código funcionará em modo "CSV‑only" usando a biblioteca padrão.
+
+## Instalação
+
+1. Clone ou copie este repositório para a máquina desejada.
+2. (Opcional) Crie um ambiente virtual:
+   ```bash
+   python -m venv venv
+   source venv/bin/activate   # Linux/Mac
+   venv\Scripts\activate      # Windows
+   ```
+3. Instale as dependências recomendadas:
+   ```bash
+   pip install pandas openpyxl
+   ```
+
+## Como usar
+
+### Via linha de comando (orquestração completa)
+
+```bash
+cd automacaoScann
+python src/main.py
+```
+
+O script irá:
+1. Detectar automaticamente `input/roteiro_testes.xlsx` ou `input/roteiro_testes.csv`.
+2. Processar todos os casos de teste.
+3. Salvar o resultado em `output/validacao_resultado.xlsx` (se o pandas estiver disponível) ou em `output/validacao_resultado.csv` (fallback).
+
+### Teste rápido da núcleo
+
+```bash
+python test_core.py
+```
+
+Executa o fluxo de leitura → parse → pagamento → validação usando o arquivo de entrada padrão e imprime o resumo no console.
+
