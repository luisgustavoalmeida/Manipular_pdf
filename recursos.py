# -*- coding: utf-8 -*-
"""Caminhos do projeto e do executável empacotado (PyInstaller)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

NOME_PASTA_DADOS = "ManipuladorPDF"
NOME_CONFIG = "config_usuario.json"
_migracao_config_feita = False


def diretorio_aplicacao() -> Path:
    """Pasta do .exe (frozen) ou raiz do projeto (desenvolvimento)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def diretorio_recursos() -> Path:
    """Arquivos empacotados (somente leitura quando frozen)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def diretorio_dados_usuario() -> Path:
    """
    Pasta gravável para preferências do usuário.

    No .exe usa %LOCALAPPDATA%\\ManipuladorPDF (fora da pasta do executável).
    Em desenvolvimento, usa a raiz do projeto.
    """
    if getattr(sys, "frozen", False):
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        pasta = Path(base) / NOME_PASTA_DADOS
        pasta.mkdir(parents=True, exist_ok=True)
        return pasta
    return Path(__file__).resolve().parent


def _migrar_config_legado() -> None:
    """Move config_usuario.json da pasta do .exe para AppData (versões antigas)."""
    global _migracao_config_feita
    if _migracao_config_feita or not getattr(sys, "frozen", False):
        _migracao_config_feita = True
        return

    _migracao_config_feita = True
    legado = diretorio_aplicacao() / NOME_CONFIG
    destino = diretorio_dados_usuario() / NOME_CONFIG
    if not legado.is_file() or destino.is_file():
        return
    try:
        legado.replace(destino)
    except OSError:
        try:
            destino.write_text(legado.read_text(encoding="utf-8"), encoding="utf-8")
            legado.unlink(missing_ok=True)
        except OSError:
            pass


def caminho_config_usuario() -> Path:
    """Caminho do JSON de preferências (tema, última pasta, etc.)."""
    _migrar_config_legado()
    return diretorio_dados_usuario() / NOME_CONFIG
