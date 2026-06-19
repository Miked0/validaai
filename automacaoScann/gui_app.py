#!/usr/bin/env python3
"""
ValidaAI - GUI app for QA test route automation.
Features:
- Select test script (Excel/CSV)
- Optional: select coupon files (PDF/JPEG)
- Optional: select audit export folder (JSONs)
- Run validation and export results (Excel/CSV + audit JSON)
"""
import sys
import os
import json
import threading
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

BASE_DIR = Path(__file__).resolve().parent
if getattr(sys, "frozen", False):
    _CANDIDATES = [Path(sys.executable).parent, Path(sys._MEIPASS) if hasattr(sys, "_MEIPASS") else BASE_DIR, BASE_DIR]
else:
    _CANDIDATES = [BASE_DIR]
_ADDED = False
for _c in _CANDIDATES:
    if not _c:
        continue
    _src = _c / "src"
    _root = _c
    for _path in [_src, _root]:
        _p = str(_path)
        if _p not in sys.path:
            sys.path.insert(0, _p)
            _ADDED = True
        if _path.exists():
            break
    if _ADDED:
        break

from validaai.reader import TestScriptReader
from validaai.parser_items import ItemParser
from validaai.payments import PaymentNormalizer
from validaai.validators import TestValidator
from validaai.exporters import ResultExporter


class ValidaAIApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ValidaAI - Automação de Roteiro de Testes")
        self.root.geometry("720x520")
        self.root.resizable(True, True)

        # State
        self.roteiro_path = tk.StringVar()
        self.cupom_paths = []
        self.audit_dir = tk.StringVar()
        self.output_path = tk.StringVar(value=str(BASE_DIR / "output" / "validacao_resultado.xlsx"))
        self.status_var = tk.StringVar(value="Pronto")
        self.progress_var = tk.DoubleVar(value=0.0)

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main, text="ValidaAI", font=("Segoe UI", 18, "bold")).pack(pady=(0, 8))
        ttk.Label(main, text="Automação de validação de roteiro de testes PDV", font=("Segoe UI", 10)).pack(pady=(0, 12))

        # Inputs section
        inp = ttk.LabelFrame(main, text="Entradas", padding=10)
        inp.pack(fill=tk.X, pady=(0, 10))

        # Roteiro
        ttk.Label(inp, text="Roteiro de testes (Excel/CSV):").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(inp, textvariable=self.roteiro_path, width=70).grid(row=0, column=1, padx=6, pady=4)
        ttk.Button(inp, text="Selecionar", command=self._select_roteiro).grid(row=0, column=2, padx=4)

        # Cupons
        ttk.Label(inp, text="Cupons (PDF/JPEG):").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.cupom_listbox = tk.Listbox(inp, height=4)
        self.cupom_listbox.grid(row=1, column=1, sticky=tk.EW, padx=6, pady=4)
        ttk.Button(inp, text="Adicionar", command=self._add_cupons).grid(row=1, column=2, padx=4, sticky=tk.N)
        ttk.Button(inp, text="Remover", command=self._remove_cupom).grid(row=1, column=2, padx=4, sticky=tk.S)

        # Audit export
        ttk.Label(inp, text="Pasta de export da auditoria (JSONs):").grid(row=2, column=0, sticky=tk.W, pady=4)
        ttk.Entry(inp, textvariable=self.audit_dir, width=70).grid(row=2, column=1, padx=6, pady=4)
        ttk.Button(inp, text="Selecionar pasta", command=self._select_audit_dir).grid(row=2, column=2, padx=4)

        inp.columnconfigure(1, weight=1)

        # Output
        out = ttk.LabelFrame(main, text="Saída", padding=10)
        out.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(out, text="Arquivo de resultado:").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(out, textvariable=self.output_path, width=70).grid(row=0, column=1, padx=6, pady=4)
        ttk.Button(out, text="Salvar como...", command=self._select_output).grid(row=0, column=2, padx=4)
        out.columnconfigure(1, weight=1)

        # Actions
        actions = ttk.Frame(main)
        actions.pack(fill=tk.X, pady=(0, 10))

        self.run_btn = ttk.Button(actions, text="Executar Validação", command=self._run_validation)
        self.run_btn.pack(side=tk.LEFT, padx=4)

        ttk.Button(actions, text="Abrir pasta de saída", command=self._open_output_dir).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Sair", command=self.root.quit).pack(side=tk.RIGHT, padx=4)

        # Progress
        progress_frame = ttk.Frame(main)
        progress_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(progress_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(8, 0))

        # Log
        log_frame = ttk.LabelFrame(main, text="Log", padding=6)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(log_frame, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _log(self, msg: str):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _select_roteiro(self):
        path = filedialog.askopenfilename(
            title="Selecionar roteiro de testes",
            filetypes=[("Planilhas", "*.xlsx *.csv"), ("Excel", "*.xlsx"), ("CSV", "*.csv"), ("Todos", "*.*")],
        )
        if path:
            self.roteiro_path.set(path)

    def _add_cupons(self):
        paths = filedialog.askopenfilenames(
            title="Selecionar cupons (PDF/JPEG)",
            filetypes=[("Imagens/PDF", "*.pdf *.jpg *.jpeg *.png"), ("PDF", "*.pdf"), ("JPEG", "*.jpg *.jpeg"), ("Todos", "*.*")],
        )
        if paths:
            self.cupom_paths.extend(paths)
            self._refresh_cupom_list()

    def _remove_cupom(self):
        sel = self.cupom_listbox.curselection()
        if sel:
            idx = sel[0]
            self.cupom_paths.pop(idx)
            self._refresh_cupom_list()

    def _refresh_cupom_list(self):
        self.cupom_listbox.delete(0, tk.END)
        for p in self.cupom_paths:
            self.cupom_listbox.insert(tk.END, Path(p).name)

    def _select_audit_dir(self):
        path = filedialog.askdirectory(title="Selecionar pasta com export da auditoria (JSONs)")
        if path:
            self.audit_dir.set(path)

    def _select_output(self):
        path = filedialog.asksaveasfilename(
            title="Salvar resultado como",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile="validacao_resultado.xlsx",
        )
        if path:
            self.output_path.set(path)

    def _open_output_dir(self):
        out = Path(self.output_path.get()).parent
        out.mkdir(parents=True, exist_ok=True)
        os.startfile(str(out))

    def _set_busy(self, busy: bool):
        self.run_btn.configure(state=tk.DISABLED if busy else tk.NORMAL)
        self.root.update_idletasks()

    # ------------------------------------------------------------------
    # Validation flow (runs in background thread)
    # ------------------------------------------------------------------
    def _run_validation(self):
        roteiro = self.roteiro_path.get().strip()
        if not roteiro or not Path(roteiro).exists():
            messagebox.showerror("Erro", "Selecione um roteiro de testes válido.")
            return

        self._set_busy(True)
        self.status_var.set("Executando...")
        self.progress_var.set(0.0)
        self._log("Iniciando validação...")

        threading.Thread(target=self._validation_thread, args=(roteiro,), daemon=True).start()

    def _validation_thread(self, roteiro: str):
        try:
            self._log("1. Lendo roteiro de testes...")
            reader = TestScriptReader(roteiro)
            raw_tests = reader.read_tests()
            self._log(f"   Encontrados {len(raw_tests)} casos de teste.")
            self.progress_var.set(20)

            self._log("2. Parseando itens...")
            item_parser = ItemParser()
            parsed_tests = [item_parser.parse_items(t) for t in raw_tests]
            self.progress_var.set(40)

            self._log("3. Normalizando pagamentos...")
            payment_normalizer = PaymentNormalizer()
            normalized_tests = [payment_normalizer.normalize_payment(t) for t in parsed_tests]
            self.progress_var.set(60)

            self._log("4. Validando regras de negócio...")
            validator = TestValidator(tolerance=0.01)
            validated_tests = [validator.validate(t) for t in normalized_tests]
            self.progress_var.set(80)

            self._log("5. Exportando resultados...")
            exporter = ResultExporter()
            output_file = self.output_path.get()
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            exporter.export(validated_tests, output_file)

            # Optional: attach audit JSON export if directory selected
            audit_dir = self.audit_dir.get().strip()
            if audit_dir and Path(audit_dir).is_dir():
                self._log("   Exportando JSONs de auditoria...")
                self._export_audit_json(validated_tests, Path(audit_dir))

            self.progress_var.set(100)

            # Summary
            status_counts = {}
            for test in validated_tests:
                status = test.get("status_final", "UNKNOWN")
                status_counts[status] = status_counts.get(status, 0) + 1

            summary = " | ".join(f"{k}: {v}" for k, v in status_counts.items())
            self._log(f"Concluído. {summary}")
            self.status_var.set("Concluído")

            messagebox.showinfo("Validação concluída", f"Resultados exportados para:\n{output_file}")

        except Exception as e:
            self._log(f"ERRO: {e}")
            self.status_var.set("Erro")
            messagebox.showerror("Erro na validação", str(e))
        finally:
            self._set_busy(False)

    def _export_audit_json(self, validated_tests, audit_dir: Path):
        audit_path = audit_dir / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        payload = {
            "generated_at": datetime.now().isoformat(),
            "total": len(validated_tests),
            "results": validated_tests,
        }
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        self._log(f"   JSON de auditoria salvo em: {audit_path}")


def main():
    root = tk.Tk()
    app = ValidaAIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
