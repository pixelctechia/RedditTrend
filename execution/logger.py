"""
logger.py — Módulo de logging centralizado para todas as automações.

Registra cada execução com timestamp, status, duração, métricas e erros.
Os logs são armazenados como JSON em .tmp/logs/run_history.json.

Uso nos scripts:
    from logger import AutomationLogger

    log = AutomationLogger("fetch_reddit_posts")
    log.info("Buscando posts...")
    log.metric("posts_coletados", 100)
    log.success()   # ou log.error("mensagem de erro")
"""

import json
import os
import traceback
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
TMP_DIR = os.getenv("TMP_DIR", ".tmp")
LOGS_DIR = Path(TMP_DIR) / "logs"
HISTORY_FILE = LOGS_DIR / "run_history.json"


class AutomationLogger:
    """Logger estruturado para automações. Grava em JSON."""

    def __init__(self, script_name: str):
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        self.script_name = script_name
        self.start_time = datetime.now(tz=timezone.utc)
        self.entries: list[dict] = []
        self.metrics: dict[str, any] = {}
        self.status = "running"
        self.error_msg = None

        self.info(f"Iniciando {script_name}")

    def _timestamp(self) -> str:
        return datetime.now(tz=timezone.utc).isoformat()

    def info(self, message: str):
        """Registra uma mensagem informativa."""
        entry = {"time": self._timestamp(), "level": "INFO", "message": message}
        self.entries.append(entry)
        print(f"  📋 [LOG] {message}")

    def warn(self, message: str):
        """Registra um aviso."""
        entry = {"time": self._timestamp(), "level": "WARN", "message": message}
        self.entries.append(entry)
        print(f"  ⚠️ [LOG] {message}")

    def error(self, message: str, exception: Exception = None):
        """Registra um erro e finaliza o run como falha."""
        error_detail = message
        if exception:
            error_detail += f"\n{traceback.format_exc()}"
        entry = {"time": self._timestamp(), "level": "ERROR", "message": error_detail}
        self.entries.append(entry)
        self.status = "error"
        self.error_msg = message
        self._save_run()
        print(f"  ❌ [LOG] {message}")

    def metric(self, key: str, value):
        """Registra uma métrica numérica ou textual."""
        self.metrics[key] = value

    def success(self, summary: str = ""):
        """Finaliza o run como sucesso e salva."""
        self.status = "success"
        if summary:
            self.info(summary)
        self.info(f"Finalizado com sucesso em {self._duration():.1f}s")
        self._save_run()

    def _duration(self) -> float:
        """Retorna a duração do run em segundos."""
        return (datetime.now(tz=timezone.utc) - self.start_time).total_seconds()

    def _save_run(self):
        """Salva o run no histórico JSON."""
        run = {
            "id": self.start_time.strftime("%Y%m%d_%H%M%S") + f"_{self.script_name}",
            "script": self.script_name,
            "status": self.status,
            "started_at": self.start_time.isoformat(),
            "finished_at": self._timestamp(),
            "duration_seconds": round(self._duration(), 2),
            "metrics": self.metrics,
            "error": self.error_msg,
            "log_entries": self.entries,
        }

        # Carregar histórico existente
        history = []
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except (json.JSONDecodeError, IOError):
                history = []

        history.append(run)

        # Manter no máximo 100 runs
        if len(history) > 100:
            history = history[-100:]

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
