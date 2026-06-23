#!/usr/bin/env python3
"""
Validation Logger Module - Unified logging system with filters and levels.
Provides clear, filterable logs aligned with final test results.
"""

from typing import Dict, Any, List, Set, Optional
from enum import Enum
from datetime import datetime
from collections import Counter
from dataclasses import dataclass, field
import json


class LogLevel(Enum):
    """Log detail levels."""
    RESUMO = "RESUMO"      # One line per test
    DETALHADO = "DETALHADO"  # Summary + key details
    DEBUG = "DEBUG"        # Full 4-stage breakdown


class TestStatus(Enum):
    """Possible test statuses in order of severity."""
    OK = "OK"
    REVISAO = "REVISAO"
    ERRO_PAGAMENTO = "ERRO_PAGAMENTO"
    ERRO_VALORES = "ERRO_VALORES"
    ERRO_ITENS = "ERRO_ITENS"
    ERRO_CONSISTENCIA = "ERRO_CONSISTENCIA"
    ERRO = "ERRO"
    NOT_RUN = "NOT_RUN"
    ERRO_DESCONHECIDO = "ERRO_DESCONHECIDO"


# Status display configuration
STATUS_ICONS = {
    TestStatus.OK: "✅",
    TestStatus.REVISAO: "⚠️",
    TestStatus.ERRO_PAGAMENTO: "❌",
    TestStatus.ERRO_VALORES: "❌",
    TestStatus.ERRO_ITENS: "❌",
    TestStatus.ERRO_CONSISTENCIA: "❌",
    TestStatus.ERRO: "❌",
    TestStatus.NOT_RUN: "⏭️",
    TestStatus.ERRO_DESCONHECIDO: "❓",
}

STATUS_COLORS = {
    TestStatus.OK: "#3BA55C",
    TestStatus.REVISAO: "#FAA61A",
    TestStatus.ERRO_PAGAMENTO: "#ED4245",
    TestStatus.ERRO_VALORES: "#ED4245",
    TestStatus.ERRO_ITENS: "#ED4245",
    TestStatus.ERRO_CONSISTENCIA: "#ED4245",
    TestStatus.ERRO: "#ED4245",
    TestStatus.NOT_RUN: "#CCCCCC",
    TestStatus.ERRO_DESCONHECIDO: "#ED4245",
}

# Filter groups - simplified per user request
FILTER_GROUPS = {
    "TODOS": set(TestStatus),
    "OK": {TestStatus.OK},
    "REVISAO": {TestStatus.REVISAO},
    "ERRO": {
        TestStatus.ERRO_PAGAMENTO,
        TestStatus.ERRO_VALORES,
        TestStatus.ERRO_ITENS,
        TestStatus.ERRO_CONSISTENCIA,
        TestStatus.ERRO,
        TestStatus.ERRO_DESCONHECIDO,
    },
    "NOT_RUN": {TestStatus.NOT_RUN},
}


def parse_status(status_str: str) -> TestStatus:
    """Parse status string to TestStatus enum."""
    try:
        return TestStatus(status_str.upper())
    except ValueError:
        return TestStatus.ERRO_DESCONHECIDO


def status_matches_filter(status: TestStatus, active_filters: Set[str]) -> bool:
    """Check if a status matches any active filter."""
    if "TODOS" in active_filters or not active_filters:
        return True
    
    status_enum = status if isinstance(status, TestStatus) else parse_status(str(status))
    
    for filter_name in active_filters:
        if filter_name in FILTER_GROUPS:
            if status_enum in FILTER_GROUPS[filter_name]:
                return True
    
    return False


@dataclass
class LogEntry:
    """Single log entry for a test result."""
    timestamp: datetime
    test_num: int
    status: TestStatus
    motivo: str
    resumo_etapas: str
    detalhes_etapas: Optional[Dict[str, Any]] = None
    
    def to_resumido(self) -> str:
        """Format as single-line summary."""
        icon = STATUS_ICONS.get(self.status, "❓")
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {icon} Teste {self.test_num:2d} | {self.status.value:15s} | {self.resumo_etapas}"
    
    def to_detalhado(self) -> List[str]:
        """Format as detailed multi-line entry."""
        lines = [self.to_resumido()]
        if self.detalhes_etapas:
            for etapa, info in self.detalhes_etapas.items():
                status = info.get('status', 'OK')
                motivo = info.get('motivo', '')
                icon = STATUS_ICONS.get(parse_status(status), "❓")
                lines.append(f"    {icon} {etapa}: {motivo}")
        return lines


class ValidationLogger:
    """
    Unified logging system for validation with filters and detail levels.
    
    Provides clear, filterable logs aligned with final test results.
    """
    
    def __init__(
        self,
        level: LogLevel = LogLevel.RESUMO,
        filters: Optional[Set[str]] = None,
        include_timestamp: bool = True,
    ):
        self.level = level
        self.filters = filters or {"TODOS"}
        self.include_timestamp = include_timestamp
        self.entries: List[LogEntry] = []
        self.counters = Counter()
        self._validation_start_time: Optional[datetime] = None
        self._total_tests = 0
    
    def set_level(self, level: LogLevel) -> None:
        """Change log detail level."""
        self.level = level
    
    def set_filters(self, filters: Set[str]) -> None:
        """Update active filters."""
        self.filters = filters or {"TODOS"}
    
    def add_filter(self, filter_name: str) -> None:
        """Add a filter to active set."""
        if filter_name in FILTER_GROUPS:
            self.filters.add(filter_name)
    
    def remove_filter(self, filter_name: str) -> None:
        """Remove a filter from active set."""
        self.filters.discard(filter_name)
    
    def clear_filters(self) -> None:
        """Reset to show all."""
        self.filters = {"TODOS"}
    
    def start_validation(self, total_tests: int) -> None:
        """Mark validation start."""
        self._validation_start_time = datetime.now()
        self._total_tests = total_tests
        self.counters.clear()
        self.entries.clear()
    
    def log_test_result(
        self,
        test_num: int,
        status: str,
        motivo: str,
        resumo_etapas: str,
        detalhes_etapas: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a test result (final status)."""
        status_enum = parse_status(status)
        
        entry = LogEntry(
            timestamp=datetime.now(),
            test_num=test_num,
            status=status_enum,
            motivo=motivo,
            resumo_etapas=resumo_etapas,
            detalhes_etapas=detalhes_etapas,
        )
        
        self.entries.append(entry)
        self.counters[status_enum] += 1
    
    def log_test_start(self, test_num: int, total: int) -> None:
        """Log validation start header."""
        self._validation_start_time = datetime.now()
        self._total_tests = total
    
    def log_summary(self) -> List[str]:
        """Generate summary lines."""
        if not self.entries:
            return ["Nenhum teste executado."]
        
        lines = []
        total = len(self.entries)
        
        # Count by status
        status_counts = Counter(e.status for e in self.entries)
        
        # Build summary line
        parts = []
        for status in TestStatus:
            count = status_counts.get(status, 0)
            if count > 0:
                icon = STATUS_ICONS.get(status, "❓")
                parts.append(f"{icon} {status.value}={count}")
        
        lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] RESUMO: {total} testes - {' | '.join(parts)}")
        return lines
    
    def get_filtered_entries(self) -> List[LogEntry]:
        """Get entries matching current filters."""
        return [e for e in self.entries if status_matches_filter(e.status, self.filters)]
    
    def get_formatted_lines(self, detailed: bool = False) -> List[str]:
        """Get formatted log lines for display."""
        filtered = self.get_filtered_entries()
        
        if not filtered:
            return ["[Nenhum teste corresponde aos filtros ativos]"]
        
        lines = []
        for entry in filtered:
            if detailed or self.level == LogLevel.DEBUG:
                lines.extend(entry.to_detalhado())
            else:
                lines.append(entry.to_resumido())
        
        return lines
    
    def export_json(self) -> str:
        """Export all entries as JSON."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.entries),
            "counters": {k.value: v for k, v in self.counters.items()},
            "filters": list(self.filters),
            "level": self.level.value,
            "entries": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "test_num": e.test_num,
                    "status": e.status.value,
                    "motivo": e.motivo,
                    "resumo_etapas": e.resumo_etapas,
                    "detalhes_etapas": e.detalhes_etapas,
                }
                for e in self.entries
            ]
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def reset(self) -> None:
        """Reset logger state."""
        self.entries.clear()
        self.counters.clear()
        self._validation_start_time = None
        self._total_tests = 0


# Convenience function for quick setup
def create_logger(
    level: str = "RESUMO",
    filters: Optional[List[str]] = None,
) -> ValidationLogger:
    """Factory function to create logger with string parameters."""
    log_level = LogLevel(level.upper()) if isinstance(level, str) else level
    filter_set = set(filters) if filters else {"TODOS"}
    return ValidationLogger(level=log_level, filters=filter_set)