#!/usr/bin/env python3
"""Unit tests for ValidationLogger - SDD compliant."""
import pytest
import json
from datetime import datetime
from collections import Counter

from validaai.logger import (
    ValidationLogger,
    LogLevel,
    TestStatus,
    LogEntry,
    STATUS_ICONS,
    FILTER_GROUPS,
    parse_status,
    status_matches_filter,
    create_logger,
)


class TestValidationLogger:
    """Tests for ValidationLogger core functionality."""

    @pytest.fixture
    def logger(self):
        return ValidationLogger()

    def test_logger_creation_defaults(self, logger):
        assert logger.level == LogLevel.RESUMO
        assert logger.filters == {"TODOS"}
        assert logger.entries == []
        assert logger.counters == Counter()

    def test_logger_creation_with_params(self):
        logger = ValidationLogger(level=LogLevel.DEBUG, filters={"OK", "ERRO"})
        assert logger.level == LogLevel.DEBUG
        assert logger.filters == {"OK", "ERRO"}

    def test_create_logger_factory(self):
        logger = create_logger(level="DEBUG", filters=["OK", "REVISAO"])
        assert logger.level == LogLevel.DEBUG
        assert logger.filters == {"OK", "REVISAO"}

    def test_set_level(self, logger):
        logger.set_level(LogLevel.DETALHADO)
        assert logger.level == LogLevel.DETALHADO
        
        logger.set_level(LogLevel.DEBUG)
        assert logger.level == LogLevel.DEBUG

    def test_set_filters(self, logger):
        logger.set_filters({"OK", "REVISAO"})
        assert logger.filters == {"OK", "REVISAO"}
        
        logger.set_filters({"ERRO"})
        assert logger.filters == {"ERRO"}

    def test_add_remove_filters(self, logger):
        logger.add_filter("OK")
        assert "OK" in logger.filters
        
        logger.add_filter("REVISAO")
        assert "REVISAO" in logger.filters
        
        logger.remove_filter("OK")
        assert "OK" not in logger.filters
        
        logger.clear_filters()
        assert logger.filters == {"TODOS"}

    def test_start_validation(self, logger):
        logger.start_validation(27)
        assert logger._total_tests == 27
        assert logger._validation_start_time is not None

    def test_log_test_result(self, logger):
        logger.log_test_result(
            test_num=1,
            status="OK",
            motivo="Todos os campos válidos",
            resumo_etapas="Itens OK | Pagamento OK | Valores OK | Obs OK",
        )
        
        assert len(logger.entries) == 1
        entry = logger.entries[0]
        assert entry.test_num == 1
        assert entry.status == TestStatus.OK
        assert entry.motivo == "Todos os campos válidos"
        assert entry.resumo_etapas == "Itens OK | Pagamento OK | Valores OK | Obs OK"
        assert logger.counters[TestStatus.OK] == 1

    def test_log_test_result_various_statuses(self, logger):
        statuses = ["OK", "REVISAO", "ERRO_PAGAMENTO", "ERRO_VALORES", "NOT_RUN"]
        for i, status in enumerate(statuses, 1):
            logger.log_test_result(i, status, f"Motivo {status}", "Resumo")
        
        assert len(logger.entries) == 5
        assert logger.counters[TestStatus.OK] == 1
        assert logger.counters[TestStatus.REVISAO] == 1
        assert logger.counters[TestStatus.ERRO_PAGAMENTO] == 1
        assert logger.counters[TestStatus.ERRO_VALORES] == 1
        assert logger.counters[TestStatus.NOT_RUN] == 1

    def test_log_summary(self, logger):
        logger.log_test_result(1, "OK", "OK", "Resumo")
        logger.log_test_result(2, "REVISAO", "Revisão", "Resumo")
        logger.log_test_result(3, "ERRO_PAGAMENTO", "Erro", "Resumo")
        
        summary_lines = logger.log_summary()
        assert len(summary_lines) == 1
        assert "RESUMO" in summary_lines[0]
        assert "3 testes" in summary_lines[0]
        assert "OK=1" in summary_lines[0]
        assert "REVISAO=1" in summary_lines[0]
        assert "ERRO_PAGAMENTO=1" in summary_lines[0]

    def test_get_filtered_entries_all(self, logger):
        logger.log_test_result(1, "OK", "OK", "Resumo")
        logger.log_test_result(2, "REVISAO", "Revisão", "Resumo")
        logger.log_test_result(3, "ERRO_PAGAMENTO", "Erro", "Resumo")
        
        filtered = logger.get_filtered_entries()
        assert len(filtered) == 3

    def test_get_filtered_entries_ok_only(self, logger):
        logger.log_test_result(1, "OK", "OK", "Resumo")
        logger.log_test_result(2, "REVISAO", "Revisão", "Resumo")
        logger.log_test_result(3, "ERRO_PAGAMENTO", "Erro", "Resumo")
        
        logger.set_filters({"OK"})
        filtered = logger.get_filtered_entries()
        assert len(filtered) == 1
        assert filtered[0].status == TestStatus.OK

    def test_get_filtered_entries_revisao_only(self, logger):
        logger.log_test_result(1, "OK", "OK", "Resumo")
        logger.log_test_result(2, "REVISAO", "Revisão", "Resumo")
        
        logger.set_filters({"REVISAO"})
        filtered = logger.get_filtered_entries()
        assert len(filtered) == 1
        assert filtered[0].status == TestStatus.REVISAO

    def test_get_filtered_entries_erro_group(self, logger):
        logger.log_test_result(1, "ERRO_PAGAMENTO", "Erro pagamento", "Resumo")
        logger.log_test_result(2, "ERRO_VALORES", "Erro valores", "Resumo")
        logger.log_test_result(3, "ERRO_ITENS", "Erro itens", "Resumo")
        
        logger.set_filters({"ERRO"})
        filtered = logger.get_filtered_entries()
        assert len(filtered) == 3

    def test_get_formatted_lines_resumido(self, logger):
        logger.log_test_result(1, "OK", "Todos OK", "Itens OK | Pagamento OK")
        logger.log_test_result(2, "REVISAO", "Troco", "Itens OK | Pagamento: Troco")
        
        lines = logger.get_formatted_lines(detailed=False)
        assert len(lines) == 2
        assert "✅" in lines[0]
        assert "⚠️" in lines[1]
        assert "Teste  1" in lines[0]
        assert "Teste  2" in lines[1]

    def test_get_formatted_lines_detalhado(self, logger):
        logger.log_test_result(
            test_num=1,
            status="REVISAO",
            motivo="Pagamento com troco",
            resumo_etapas="Itens OK | Pagamento: Troco",
            detalhes_etapas={
                "Etapa 1": {"status": "OK", "motivo": "Itens conferem"},
                "Etapa 2": {"status": "REVISAO", "motivo": "Pagamento com troco"},
                "Etapa 3": {"status": "OK", "motivo": "Valores conferem"},
                "Etapa 4": {"status": "OK", "motivo": "Obs OK"},
            }
        )
        
        lines = logger.get_formatted_lines(detailed=True)
        assert len(lines) >= 5  # header + 4 etapas
        assert "⚠️" in lines[0]

    def test_export_json(self, logger):
        logger.log_test_result(1, "OK", "OK", "Resumo")
        logger.log_test_result(2, "ERRO_PAGAMENTO", "Erro", "Resumo")
        
        json_str = logger.export_json()
        data = json.loads(json_str)
        
        assert data["total_tests"] == 2
        assert data["counters"]["OK"] == 1
        assert data["counters"]["ERRO_PAGAMENTO"] == 1
        assert data["filters"] == ["TODOS"]
        assert data["level"] == "RESUMO"
        assert len(data["entries"]) == 2

    def test_reset(self, logger):
        logger.log_test_result(1, "OK", "OK", "Resumo")
        logger.reset()
        
        assert logger.entries == []
        assert logger.counters == Counter()
        assert logger._validation_start_time is None
        assert logger._total_tests == 0


class TestStatusParsing:
    """Tests for status parsing and filtering."""

    def test_parse_status_valid(self):
        assert parse_status("OK") == TestStatus.OK
        assert parse_status("ok") == TestStatus.OK
        assert parse_status("REVISAO") == TestStatus.REVISAO
        assert parse_status("revisao") == TestStatus.REVISAO
        assert parse_status("ERRO_PAGAMENTO") == TestStatus.ERRO_PAGAMENTO
        assert parse_status("ERRO_VALORES") == TestStatus.ERRO_VALORES
        assert parse_status("NOT_RUN") == TestStatus.NOT_RUN

    def test_parse_status_invalid(self):
        assert parse_status("INVALIDO") == TestStatus.ERRO_DESCONHECIDO
        assert parse_status("") == TestStatus.ERRO_DESCONHECIDO

    def test_status_matches_filter_todos(self):
        assert status_matches_filter(TestStatus.OK, {"TODOS"}) is True
        assert status_matches_filter(TestStatus.ERRO_PAGAMENTO, {"TODOS"}) is True

    def test_status_matches_filter_empty(self):
        assert status_matches_filter(TestStatus.OK, set()) is True
        assert status_matches_filter(TestStatus.ERRO, set()) is True

    def test_status_matches_filter_specific(self):
        assert status_matches_filter(TestStatus.OK, {"OK"}) is True
        assert status_matches_filter(TestStatus.REVISAO, {"REVISAO"}) is True
        assert status_matches_filter(TestStatus.ERRO_PAGAMENTO, {"ERRO"}) is True
        assert status_matches_filter(TestStatus.ERRO_VALORES, {"ERRO"}) is True
        assert status_matches_filter(TestStatus.ERRO_ITENS, {"ERRO"}) is True
        assert status_matches_filter(TestStatus.ERRO_CONSISTENCIA, {"ERRO"}) is True

    def test_status_matches_filter_no_match_filter_no_match(self):
        assert status_matches_filter(TestStatus.OK, {"REVISAO"}) is False
        assert status_matches_filter(TestStatus.REVISAO, {"OK"}) is False
        assert status_matches_filter(TestStatus.OK, {"ERRO"}) is False

    def test_filter_groups_correct(self):
        assert TestStatus.OK in FILTER_GROUPS["OK"]
        assert TestStatus.REVISAO in FILTER_GROUPS["REVISAO"]
        assert TestStatus.ERRO_PAGAMENTO in FILTER_GROUPS["ERRO"]
        assert TestStatus.ERRO_VALORES in FILTER_GROUPS["ERRO"]
        assert TestStatus.ERRO_ITENS in FILTER_GROUPS["ERRO"]
        assert TestStatus.ERRO_CONSISTENCIA in FILTER_GROUPS["ERRO"]
        assert TestStatus.ERRO in FILTER_GROUPS["ERRO"]
        assert TestStatus.NOT_RUN in FILTER_GROUPS["NOT_RUN"]
        assert TestStatus.OK in FILTER_GROUPS["TODOS"]
        assert TestStatus.ERRO in FILTER_GROUPS["TODOS"]


class TestLogEntry:
    """Tests for LogEntry formatting."""

    def test_to_resumido(self):
        entry = LogEntry(
            timestamp=datetime(2026, 6, 20, 14, 30, 15),
            test_num=1,
            status=TestStatus.OK,
            motivo="Todos os campos válidos",
            resumo_etapas="Itens OK | Pagamento OK",
        )
        line = entry.to_resumido()
        assert "14:30:15" in line
        assert "✅" in line
        assert "Teste  1" in line
        assert "OK" in line
        assert "Itens OK | Pagamento OK" in line

    def test_to_resumido_revisao(self):
        entry = LogEntry(
            timestamp=datetime(2026, 6, 20, 14, 30, 15),
            test_num=2,
            status=TestStatus.REVISAO,
            motivo="Pagamento com troco",
            resumo_etapas="Itens OK | Pagamento: Troco",
        )
        line = entry.to_resumido()
        assert "⚠️" in line
        assert "REVISAO" in line

    def test_to_resumido_erro(self):
        entry = LogEntry(
            timestamp=datetime(2026, 6, 20, 14, 30, 15),
            test_num=3,
            status=TestStatus.ERRO_PAGAMENTO,
            motivo="Múltiplo divergente",
            resumo_etapas="Itens OK | Pagamento: Múltiplo divergente",
        )
        line = entry.to_resumido()
        assert "❌" in line
        assert "ERRO_PAGAMENTO" in line

    def test_to_detalhado(self):
        entry = LogEntry(
            timestamp=datetime(2026, 6, 20, 14, 30, 15),
            test_num=1,
            status=TestStatus.REVISAO,
            motivo="Pagamento com troco",
            resumo_etapas="Itens OK | Pagamento: Troco",
            detalhes_etapas={
                "Etapa 1": {"status": "OK", "motivo": "Itens conferem"},
                "Etapa 2": {"status": "REVISAO", "motivo": "Pagamento com troco"},
                "Etapa 3": {"status": "OK", "motivo": "Valores conferem"},
            }
        )
        lines = entry.to_detalhado()
        assert len(lines) == 4  # header + 3 etapas
        assert "⚠️" in lines[0]
        assert "Etapa 1" in lines[1]
        assert "Etapa 2" in lines[2]
        assert "Etapa 3" in lines[3]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])