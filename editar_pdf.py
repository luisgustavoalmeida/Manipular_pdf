# -*- coding: utf-8 -*-
"""
Operações de edição em PDF: extrair páginas, rotacionar e comprimir.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import fitz
from pypdf import PdfReader, PdfWriter

from progresso import RelatorioProgresso


def obter_total_paginas(caminho: str | Path) -> int:
    """Retorna a quantidade de páginas do PDF."""
    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    leitor = PdfReader(str(caminho))
    return len(leitor.pages)


def interpretar_paginas(entrada: str, total_paginas: int) -> list[int]:
    """
    Interpreta intervalo de páginas (base 1).

    Exemplos: "1,3,5-8" → índices 0-based [0,2,4,5,6,7]
    """
    entrada = entrada.strip()
    if not entrada:
        raise ValueError("Informe ao menos uma página.")

    indices: list[int] = []
    vistos: set[int] = set()

    for parte in entrada.replace(" ", "").split(","):
        if not parte:
            continue
        if "-" in parte:
            inicio_str, fim_str = parte.split("-", 1)
            inicio, fim = int(inicio_str), int(fim_str)
            if inicio > fim:
                inicio, fim = fim, inicio
            paginas = range(inicio, fim + 1)
        else:
            paginas = [int(parte)]

        for pagina in paginas:
            if pagina < 1 or pagina > total_paginas:
                raise ValueError(
                    f"Página {pagina} inválida. O PDF tem {total_paginas} página(s)."
                )
            if pagina not in vistos:
                indices.append(pagina - 1)
                vistos.add(pagina)

    if not indices:
        raise ValueError("Nenhuma página válida informada.")
    return indices


def _salvar_writer(escritor: PdfWriter, destino: Path) -> None:
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


def extrair_paginas(
    caminho_entrada: str | Path,
    paginas: list[int],
    caminho_saida: str | Path,
    progresso: RelatorioProgresso | None = None,
) -> str:
    """
    Extrai páginas específicas (índices 0-based) para um novo PDF.

    A ordem em `paginas` define a ordem no PDF gerado.
    """
    entrada = Path(caminho_entrada)
    if not entrada.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {entrada}")

    leitor = PdfReader(str(entrada))
    total = len(leitor.pages)

    if progresso:
        progresso.iniciar(len(paginas) + 1, "Extraindo páginas")
        progresso.avancar(1, "Lendo PDF")

    for indice in paginas:
        if indice < 0 or indice >= total:
            raise ValueError(f"Índice de página inválido: {indice + 1}")

    escritor = PdfWriter()
    for indice in paginas:
        escritor.add_page(leitor.pages[indice])
        if progresso:
            progresso.avancar(1, f"Página {indice + 1}")

    destino = Path(caminho_saida)
    _salvar_writer(escritor, destino)
    if progresso:
        progresso.concluir()
    return str(destino.resolve())


def rotacionar_paginas(
    caminho_entrada: str | Path,
    angulo: int,
    caminho_saida: str | Path,
    paginas: list[int] | None = None,
    progresso: RelatorioProgresso | None = None,
) -> str:
    """
    Rotaciona páginas do PDF.

    Args:
        angulo: Graus (90, 180, 270 ou -90). Positivo = sentido horário (pypdf).
        paginas: Índices 0-based. None = todas as páginas.
    """
    if angulo not in (90, 180, 270, -90):
        raise ValueError("O ângulo deve ser 90, 180, 270 ou -90 graus.")

    entrada = Path(caminho_entrada)
    if not entrada.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {entrada}")

    leitor = PdfReader(str(entrada))
    total = len(leitor.pages)
    alvos = set(paginas if paginas is not None else range(total))

    if progresso:
        progresso.iniciar(total + 1, "Rotacionando páginas")

    for indice in alvos:
        if indice < 0 or indice >= total:
            raise ValueError(f"Índice de página inválido: {indice + 1}")

    escritor = PdfWriter()
    for indice, pagina in enumerate(leitor.pages):
        if indice in alvos:
            pagina.rotate(angulo)
        escritor.add_page(pagina)
        if progresso:
            progresso.avancar(1, f"Página {indice + 1}/{total}")

    destino = Path(caminho_saida)
    _salvar_writer(escritor, destino)
    if progresso:
        progresso.concluir()
    return str(destino.resolve())


def _tamanho_mb(caminho: Path) -> float:
    return caminho.stat().st_size / (1024 * 1024)


def comprimir_pdf(
    caminho_entrada: str | Path,
    caminho_saida: str | Path,
    nivel: str = "medio",
    progresso: RelatorioProgresso | None = None,
) -> str:
    """
    Reduz o tamanho do PDF.

    Níveis: 'leve', 'medio', 'forte'
    """
    niveis_validos = {"leve", "medio", "forte"}
    if nivel not in niveis_validos:
        raise ValueError(f"Nível inválido. Use: {', '.join(sorted(niveis_validos))}")

    entrada = Path(caminho_entrada)
    if not entrada.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {entrada}")

    destino = Path(caminho_saida)
    destino.parent.mkdir(parents=True, exist_ok=True)

    if progresso:
        progresso.iniciar(3, "Comprimindo PDF")

    doc = fitz.open(str(entrada))
    try:
        if progresso:
            progresso.avancar(1, "Analisando documento")
        if nivel == "forte" and hasattr(doc, "rewrite_images"):
            doc.rewrite_images(dpi_threshold=150, dpi_target=96, quality=65)

        opcoes: dict = {
            "garbage": 4,
            "deflate": True,
            "clean": True,
            "pretty": False,
        }
        if nivel in ("medio", "forte"):
            opcoes["deflate_images"] = True
            opcoes["deflate_fonts"] = True

        if progresso:
            progresso.avancar(1, "Aplicando compressão")

        fd, temp_path = tempfile.mkstemp(suffix=".pdf", dir=destino.parent)
        os.close(fd)
        try:
            doc.save(temp_path, **opcoes)
            os.replace(temp_path, destino)
        except Exception:
            Path(temp_path).unlink(missing_ok=True)
            raise
    finally:
        doc.close()

    if progresso:
        progresso.concluir()

    return str(destino.resolve())


def resumo_compressao(caminho_entrada: str | Path, caminho_saida: str | Path) -> str:
    """Retorna texto com tamanhos antes/depois da compressão."""
    antes = _tamanho_mb(Path(caminho_entrada))
    depois = _tamanho_mb(Path(caminho_saida))
    reducao = ((antes - depois) / antes * 100) if antes > 0 else 0
    return f"{antes:.2f} MB → {depois:.2f} MB (redução de {reducao:.1f}%)"
