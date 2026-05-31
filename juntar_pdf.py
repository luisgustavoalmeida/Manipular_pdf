# -*- coding: utf-8 -*-
"""
Módulo para junção de múltiplos arquivos PDF em um único PDF.
"""

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from progresso import RelatorioProgresso, percorrer


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

    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    escritor = PdfWriter()
    for caminho in percorrer(caminhos, descricao="Juntando PDFs", progresso=progresso, unit="arquivo"):
        escritor.append(PdfReader(str(caminho)))

    with open(caminho_saida, "wb") as arquivo:
        escritor.write(arquivo)

    escritor.close()
    return str(caminho_saida)
