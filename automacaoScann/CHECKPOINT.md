# Checkpoint ValidaAI — 2026-06-16

## Estado atual
- P1 (API JSON generation/validation) integrada no `gui_app_standalone.py`.
- Módulo `api_sales.py` criado e validado com sucesso.
- `NameError: name 'output_file'` resolvido; variável correta em uso é `output_resumo`.
- `_to_dec()` ajustado para decimais brasileiros (R$ 149,065 => 149.065).
- Fluxo da GUI agora exporta `api_status`, `api_alertas`, `sale_json`.
- Próximo passo: teste real pela GUI com o `ValidaAI.exe` atual e, se necessário, rebuild antes de seguir para P2..P9.

## Como retomar
1. Abra o terminal e navegue até `C:\Users\Usuario\.hermes\validaai-main\automacaoScann`.
2. Rodar `ValidaAI.exe` ou `python gui_app_standalone.py`.
3. Usar como roteiro de teste o `biblioteca/TEMPLATE_COM_BIN_NOVO.xlsx` (linha 1 da ETAPA 1).
4. Validar se o JSON gerado bate com o esperado e se o campo `total` fica 149.065.

## Pendente
- P2: separação clara `codigoArticulo` vs `codigoBarras`
- P3..P9: demais gaps alinhados à API Vendas e Promoções.
