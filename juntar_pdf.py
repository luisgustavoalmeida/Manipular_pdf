# -*- coding: utf-8 -*-
"""
Módulo para junção de múltiplos arquivos PDF em um único PDF.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from progresso import OperacaoCancelada, RelatorioProgresso, limpar_arquivos_gerados, percorrer


def _salvar_pdf(escritor: PdfWriter, destino: Path) -> None:
    """Grava o PDF de forma atômica (evita arquivo corrompido se interrompido)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(suffix=".pdf", dir=destino.parent)
    os.close(fd)
    try:
        with open(temp_path, "wb") as arquivo:
            escritor.write(arquivo)
        os.replace(temp_path, destino)
    except Exception:
        Path(temp_path).unlink(missing_ok=True)
        raise


def juntar_pdfs(
    lista_caminhos: list[str],
    caminho_saida: str,
    ordenar_por_nome: bool = True,
    progresso: RelatorioProgresso | None = None,
) -> str:
    """
    Junta vários arquivos PDF em um único arquivo.

    Args:
        lista_caminhos: Lista de caminhos dos PDFs a juntar.
        caminho_saida: Caminho do PDF de saída.
        ordenar_por_nome: Se True, ordena os arquivos pelo nome antes de juntar.

    Returns:
        Caminho do arquivo gerado.
    """
    if not lista_caminhos:
        raise ValueError("A lista de arquivos não pode estar vazia.")

    caminhos = [Path(p) for p in lista_caminhos]
    for caminho in caminhos:
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    if ordenar_por_nome:
        caminhos = sorted(caminhos, key=lambda p: p.name.lower())

    destino = Path(caminho_saida)
    escritor = PdfWriter()
    try:
        for caminho in percorrer(caminhos, descricao="Juntando PDFs", progresso=progresso, unit="arquivo"):
            escritor.append(PdfReader(str(caminho)))
        _salvar_pdf(escritor, destino)
    except OperacaoCancelada:
        limpar_arquivos_gerados([destino])
        raise
    finally:
        escritor.close()

    return str(destino)
