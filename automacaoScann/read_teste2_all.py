from src.validaai.reader import TestScriptReader

reader = TestScriptReader('biblioteca/teste 2/TEMPLATE_COM_BIN_NOVO (2).xlsx')
# Don't filter by etapa - read all
tests = reader.read_tests()
print(f'Total tests read (all sheets): {len(tests)}')
for t in tests:
    print(f'Teste {t.get("teste")}: {t.get("itens_da_venda", "")[:80]} | Pag: {t.get("pagamento", "")} | Sub: {t.get("subtotal")} | Desc: {t.get("desconto")} | Tot: {t.get("total")} | Obs: {str(t.get("observacoes", ""))[:60]}')