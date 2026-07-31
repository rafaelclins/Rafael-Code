import logging
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class FileManager:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root).resolve()
        self.backups_dir = self.root / ".rafael_backups"

    def _validar_caminho(self, caminho: str | Path) -> Path:
        alvo = (self.root / str(caminho)).resolve()
        if not alvo.is_relative_to(self.root):
            raise ValueError(
                f"Caminho fora do repositório: '{caminho}' -> {alvo}"
            )
        return alvo

    def _criar_backup(self, arquivo: Path) -> Path | None:
        if not arquivo.exists():
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        relativo = arquivo.relative_to(self.root)
        destino = self.backups_dir / timestamp / relativo
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(arquivo, destino)
        return destino

    def aplicar_alteracoes(self, lista_arquivos: list[dict]) -> list[dict]:
        relatorio: list[dict] = []
        for item in lista_arquivos:
            try:
                caminho = (item.get("caminho") or "").strip()
                acao = (item.get("acao") or "criar").strip().lower()
                conteudo = item.get("conteudo") or ""
                if not caminho:
                    relatorio.append({
                        "caminho": "",
                        "acao": acao,
                        "backup": None,
                        "status": "ERRO",
                        "detalhe": "caminho vazio",
                    })
                    continue

                alvo = self._validar_caminho(caminho)
                backup = None

                if acao == "excluir":
                    if alvo.exists():
                        backup = self._criar_backup(alvo)
                        alvo.unlink()
                    acao_real = "excluido"
                else:
                    if alvo.exists():
                        backup = self._criar_backup(alvo)
                    alvo.parent.mkdir(parents=True, exist_ok=True)
                    with open(alvo, "w", encoding="utf-8", newline="\n") as arq:
                        arq.write(conteudo)
                    acao_real = "criado" if backup is None else "modificado"

                relatorio.append({
                    "caminho": caminho,
                    "acao": acao_real,
                    "backup": str(backup) if backup else None,
                    "status": "OK",
                    "detalhe": "",
                })
            except Exception as e:
                logger.error("Falha ao gravar %s: %s", item.get("caminho"), e)
                relatorio.append({
                    "caminho": item.get("caminho", ""),
                    "acao": (item.get("acao") or "criar").lower(),
                    "backup": None,
                    "status": "ERRO",
                    "detalhe": str(e),
                })
        return relatorio
