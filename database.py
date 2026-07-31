import json
import logging
import sqlite3
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

_local = threading.local()

DB_PATH = Path(__file__).resolve().parent / "rafael_code.db"


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(DB_PATH))
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessoes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT    DEFAULT (datetime('now','localtime')),
            pedido_usuario  TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS logs_agentes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sessao_id       INTEGER NOT NULL,
            agente          TEXT    NOT NULL,
            texto_gerado    TEXT    NOT NULL,
            FOREIGN KEY (sessao_id) REFERENCES sessoes(id)
        );
    """)
    conn.commit()
    logger.info("Banco inicializado: %s", DB_PATH)


def criar_sessao(pedido_usuario: str) -> int:
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO sessoes (pedido_usuario) VALUES (?)",
        (pedido_usuario,),
    )
    conn.commit()
    logger.info("Sessão criada: id=%d", cur.lastrowid)
    return cur.lastrowid


def salvar_log_agente(sessao_id: int, agente: str, texto_gerado: str) -> None:
    conn = _get_conn()
    conn.execute(
        "INSERT INTO logs_agentes (sessao_id, agente, texto_gerado) VALUES (?, ?, ?)",
        (sessao_id, agente, texto_gerado),
    )
    conn.commit()
    logger.debug("Log salvo: sessao=%d agente=%s", sessao_id, agente)


def ultimos_pedidos(limite: int = 2) -> list[str]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT pedido_usuario FROM sessoes ORDER BY id DESC LIMIT ?",
        (limite,),
    ).fetchall()
    pedidos = [row["pedido_usuario"] for row in reversed(rows)]
    return pedidos
