#!/usr/bin/env python3
"""
ValidaAI Scheduled Validation Runner
Runs validation on a cron schedule with notifications.
"""
import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Add project root
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from validaai import (
    TestScriptReader, ItemParser, PaymentNormalizer, TestValidator,
    APISalesBuilder, API_SALES_AVAILABLE, get_payment_label
)
from core.exporters import ExportPipeline, ExportConfig

# ─── Logging ──────────────────────────────────────────────
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"scheduler_{datetime.now().strftime('%Y%m')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("validaai.scheduler")


@dataclass
class ScheduledJobResult:
    job_name: str
    started_at: str
    finished_at: str
    success: bool
    error: Optional[str] = None
    export_results: List[Dict[str, Any]] = None
    summary: Optional[Dict[str, int]] = None


class ValidationScheduler:
    """Runs validation on schedule with retries and notifications."""
    
    def __init__(self, config: ExportConfig):
        self.config = config
        self.scheduler_config = config.scheduler
        self.pipeline = None
        
        if self.scheduler_config.get("enabled", False):
            self.pipeline = ExportPipeline(config)
            self._setup_notifiers()
    
    def _setup_notifiers(self):
        """Initialize notifiers from config."""
        from core.exporters import EmailNotifier, SlackNotifier
        self.notifiers = []
        
        notif_config = self.config.notifications
        if notif_config.get("enabled", False):
            email_config = notif_config.get("email", {})
            if email_config.get("enabled", False):
                self.notifiers.append(("email", EmailNotifier(email_config)))
            
            slack_config = notif_config.get("slack", {})
            if slack_config.get("enabled", False):
                self.notifiers.append(("slack", SlackNotifier(slack_config)))
    
    def _notify(self, subject: str, message: str, attachments=None, metadata=None):
        for name, notifier in self.notifiers:
            try:
                notifier.send(subject, message, attachments, metadata)
                logger.info(f"Notification sent via {name}")
            except Exception as e:
                logger.error(f"Notifier {name} error: {e}")
    
    def run_validation(self) -> ScheduledJobResult:
        """Execute one validation run."""
        started_at = datetime.now().isoformat()
        job_name = "validaai_scheduled"
        
        try:
            logger.info("Starting scheduled validation...")
            
            # ─── Load configuration ───────────────────────
            roteiro_path = self.scheduler_config.get("roteiro_path")
            etapa = self.scheduler_config.get("etapa", "ETAPA 1")
            audit_file = self.scheduler_config.get("audit_file")
            output_dir = Path(self.scheduler_config.get("output_dir", "output/scheduled"))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if not roteiro_path or not Path(roteiro_path).exists():
                raise FileNotFoundError(f"Roteiro not found: {roteiro_path}")
            
            if audit_file and not Path(audit_file).exists():
                logger.warning(f"Audit file not found: {audit_file}")
                audit_file = ""
            
            # ─── Run validation pipeline ──────────────────
            logger.info(f"Reading roteiro: {roteiro_path}")
            reader = TestScriptReader(roteiro_path)
            reader.set_etapa(etapa)
            raw_tests = reader.read_tests()
            logger.info(f"Found {len(raw_tests)} test cases")
            
            item_parser = ItemParser()
            parsed_tests = [item_parser.parse_items(t) for t in raw_tests]
            
            payment_normalizer = PaymentNormalizer()
            normalized_tests = [payment_normalizer.normalize_payment(t) for t in parsed_tests]
            
            validator = TestValidator(tolerance=0.01)
            validated_tests = [validator.validate(t) for t in normalized_tests]
            
            # API validation if available
            if API_SALES_AVAILABLE and audit_file:
                api_builder = APISalesBuilder()
                # Load partner JSONs (simplified - reuse pipeline logic)
                self._enrich_with_partner_json(validated_tests, audit_file, api_builder)
            
            # ─── Export ──────────────────────────────────
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            etapa_slug = etapa.replace(" ", "_")
            base_path = output_dir / f"validacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{etapa.replace(' ', '_')}_v2.0"
            
            metadata = {
                "app_version": "2.1.0",
                "etapa": etapa,
                "roteiro": str(roteiro_path),
                "audit_file": audit_file,
                "generated_at": datetime.now().isoformat(),
            }
            
            pipeline_config = ExportConfig(
                exporters=["excel", "csv", "json_audit", "html_report"],
                excel={"sheet_name": "Resumo", "freeze_header": True},
                csv={"delimiter": ",", "encoding": "utf-8-sig"},
                json_audit={"indent": 2},
                html_report={"theme": "dark"},
            )
            pipeline = ExportPipeline(pipeline_config)
            
            export_results = pipeline.run(validated_tests, Path(".") / base_path, {
                "app_version": "2.1.0",
                "etapa": etapa,
                "generated_at": datetime.now().isoformat(),
            })
            
            # ─── Find output files ───────────────────────
            output_files = []
            for result in export_results:
                if result.success:
                    output_path = Path(result.output_path)
                    if output_path.exists():
                        output_files.append(output_path)
            
            # ─── Summary ────────────────────────────────
            status_counts = {}
            for test in validated_tests:
                status = test.get("status_final", "UNKNOWN")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            summary = {
                "total": len(validated_tests),
                "ok": status_counts.get("OK", 0),
                "revisao": status_counts.get("REVISAO", 0),
                "erro": status_counts.get("ERRO", 0),
                "erro_pagamento": status_counts.get("ERRO_PAGAMENTO", 0),
                "not_run": status_counts.get("NOT_RUN", 0),
            }
            
            # ─── Send success notification ──────────────
            finished_at = datetime.now().isoformat()
            
            subject = f"ValidaAI Scheduled - {summary['ok']} OK / {summary['revisao']} REVISAO / {summary['erro']} ERRO"
            message = (
                f"ValidaAI Scheduled Validation Complete\n"
                f"Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"Etapa: {etapa}\n"
                f"Roteiro: {roteiro_path}\n"
                f"Total: {summary['total']}\n"
                f"OK: {summary['ok']}\n"
                f"REVISAO: {summary['revisao']}\n"
                f"ERRO: {summary['erro']}\n"
                f"NOT_RUN: {summary.get('not_run', 0)}\n"
                f"Output: {len(output_dir.glob('*'))} files generated"
            )
            
            # Send notifications
            self._send_notifications(
                subject=subject,
                message=message,
                attachments=[str(f) for f in output_files[:3]],
                metadata={"summary": summary, "etapa": etapa, "generated_at": datetime.now().isoformat()}
            )
            
            return ScheduledJobResult(
                job_name="validaai_scheduled",
                started_at=started_at,
                finished_at=datetime.now().isoformat(),
                success=True,
                export_results=[{"exporter": r.exporter_name, "path": str(r.output_path), "rows": r.rows_exported} for r in export_results if hasattr(r, 'exporter_name')],
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Scheduled validation failed: {e}", exc_info=True)
            
            # Send error notification if configured
            if hasattr(self, 'notifiers') and self.notifiers:
                self._notify(
                    subject="ValidaAI Scheduler ERROR",
                    message=f"Scheduled validation failed:\n{e}\n\nCheck logs for details.",
                    metadata={"error": str(e)}
                )
            
            return ScheduledJobResult(
                job_name="validaai_scheduled",
                started_at=started_at,
                finished_at=datetime.now().isoformat(),
                success=False,
                error=str(e)
            )
    
    def _enrich_with_partner_json(self, validated_tests: List[Dict], audit_file: str, api_builder):
        """Enrich tests with partner JSON from audit file (simplified)."""
        import pandas as pd
        
        try:
            xls = pd.ExcelFile(audit_file)
            partner_jsons = {}
            
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(audit_file, sheet_name=sheet_name, dtype=str)
                
                test_col = None
                test_cols = [c for c in df.columns if c and ('teste' in c.lower() or 'cupom' in c.lower() or 'numero' in c.lower())]
                if test_cols:
                    for preferred in ['Número cupom', 'Numero cupom', 'Teste', 'Numero']:
                        if preferred in df.columns:
                            test_col = preferred
                            break
                        for c in test_cols:
                            if preferred.lower() in c.lower():
                                test_col = c
                                break
                    if test_col is None and test_cols:
                        test_col = test_cols[0]
                
                request_col = None
                if 'Request' in df.columns:
                    request_col = 'Request'
                else:
                    request_cols = [c for c in df.columns if c and ('request' in c.lower() or 'json' in c.lower() or 'movimiento' in c.lower()) and c.lower() != 'id request']
                    if request_cols:
                        request_col = request_cols[0]
                
                if test_col and request_col:
                    for _, row in df.iterrows():
                        test_val = str(row.get(test_col, '')).strip()
                        request_val = str(row.get(request_col, '')).strip()
                        if test_val and request_val and request_val not in ['nan', 'None', '']:
                            try:
                                partner_jsons[test_val] = json.loads(request_val)
                            except Exception:
                                pass
            
            # Enrich tests
            for t in validated_tests:
                test_cupom = ""
                for field in ['cupom', 'nfce', 'sat', 'ecf']:
                    val = str(t.get(field, '')).strip()
                    if val and val.lower() not in ['nan', 'none', '']:
                        test_cupom = val
                        break
                
                if test_cupom in partner_jsons:
                    t['sale_json'] = partner_jsons[test_cupom]
                    api_check = api_builder.validate_sale_json(partner_jsons[test_cupom])
                    t['api_status'] = api_check.get('status', 'ERRO_JSON')
                    t['api_alertas'] = api_check.get('alertas', []) or []
                    
                    # Validate cupom & payment codes (simplified)
                    self._validate_cupom_consistency(t, partner_jsons[test_cupom])
                    self._validate_payment_codes(t, partner_jsons[test_cupom])
                else:
                    t['sale_json'] = {}
                    t['api_status'] = 'ERRO'
                    t['api_alertas'] = [f"JSON do parceiro não encontrado para cupom {test_cupom}"]
        
        except Exception as e:
            logger.warning(f"Failed to enrich with partner JSON: {e}")
    
    def _validate_cupom_consistency(self, test_dict, partner_json):
        """Validate cupom consistency between roteiro and partner JSON."""
        def _extrair_cupom_json(json_data):
            if not isinstance(json_data, dict): return ''
            if isinstance(json_data.get('movimiento'), dict):
                return str(json_data['movimiento'].get('numero', '')).strip()
            return str(json_data.get('numero', '')).strip()
        
        cupom_roteiro = str(test_dict.get('cupom', '')).strip()
        cupom_json = _extrair_cupom_json(partner_json)
        cupom_sat = str(test_dict.get('sat', '')).strip()
        cupom_ecf = str(test_dict.get('ecf', '')).strip()
        cupom_nfce = str(test_dict.get('nfce', '')).strip()
        
        cupom_valido = False
        if cupom_roteiro and cupom_json and cupom_roteiro == cupom_json:
            cupom_valido = True
        elif cupom_sat and cupom_json and cupom_sat == cupom_json:
            cupom_valido = True
        elif cupom_ecf and cupom_json and cupom_ecf == cupom_json:
            cupom_valido = True
        elif cupom_nfce and cupom_json and cupom_nfce == cupom_json:
            cupom_valido = True
        
        if not cupom_valido:
            if cupom_roteiro or cupom_sat or cupom_ecf or cupom_nfce:
                test_dict['api_status'] = 'ERRO'
                motivo = f"Cupom não confere: Roteiro='{cupom_roteiro}', SAT='{cupom_sat}', ECF='{cupom_ecf}', NFCe='{cupom_nfce}' vs JSON='{cupom_json}'"
                test_dict['api_alertas'].append(motivo)
    
    def _validate_payment_codes(self, test_dict, partner_json):
        """Validate payment codes between expected and partner JSON."""
        def _extrair_pagos_json(json_data):
            if not isinstance(json_data, dict): return []
            if isinstance(json_data.get('movimiento'), dict):
                return json_data['movimiento'].get('pagos', [])
            return json_data.get('pagos', [])
        
        pagamentos_esperados = test_dict.get('pagamentos', [])
        if pagamentos_esperados:
            expected_codes = sorted([str(p.get('codigo', '')).strip() for p in pagamentos_esperados if p.get('codigo')])
        else:
            pgto_raw = str(test_dict.get('pagamento', '')).strip().lower()
            pgto_map = {
                'dinheiro': '9', 'dinheiro com troco': '9',
                'cartao credito': '10', 'cartao crédito': '10',
                'cartao debito': '13', 'cartao débito': '13',
                'pix': '14', 'qr': '14', 'pix/qr': '14',
                'cheque': '11', 'vale': '12', 'finalizadora': '15',
            }
            expected_codes = [pgto_map.get(pgto_raw, '')] if pgto_raw else []
        
        pagos_json = _extrair_pagos_json(partner_json)
        actual_codes = sorted([str(p.get('codigoTipoPago', '')).strip() for p in pagos_json if p.get('codigoTipoPago')])
        
        if expected_codes and actual_codes:
            if expected_codes != actual_codes:
                motivo = f"Códigos de pagamento divergentes: esperado={expected_codes} vs parceiro={actual_codes}"
                test_dict['api_alertas'].append(motivo)
                if test_dict.get('api_status') == 'OK':
                    test_dict['api_status'] = 'REVISAO'
    
    def _send_notifications(self, subject: str, message: str, attachments=None, metadata=None):
        """Send notifications via configured channels."""
        from core.exporters import EmailNotifier, SlackNotifier
        
        notif_config = self.config.notifications
        if not notif_config.get("enabled", False):
            return
        
        email_config = notif_config.get("email", {})
        if email_config.get("enabled", False):
            from core.exporters import EmailNotifier
            notifier = EmailNotifier(email_config)
            notifier.send(subject, "ValidaAI Scheduler\n\n" + message, attachments)
        
        slack_config = notif_config.get("slack", {})
        if slack_config.get("enabled", False):
            from core.exporters import SlackNotifier
            notifier = SlackNotifier(slack_config)
            notifier.send("ValidaAI Scheduler", "ValidaAI Scheduler: " + message)


def main():
    """Main entry point for cron execution."""
    config_path = BASE_DIR / "config" / "export.json"
    
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    config = ExportConfig.from_file(config_path)
    
    if not config.scheduler.get("enabled", False):
        logger.warning("Scheduler not enabled in config. Set scheduler.enabled=true in export.json")
        sys.exit(0)
    
    scheduler = ValidationScheduler(config)
    result = scheduler.run_validation()
    
    # Log result
    logger.info(f"Job completed: success={result.success}, summary={result.summary}")
    
    if not result.success:
        logger.error(f"Job failed: {result.error}")
        sys.exit(1)
    
    logger.info("Scheduled validation completed successfully")


if __name__ == "__main__":
    main()