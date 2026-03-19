# -*- coding: utf-8 -*-
"""
Módulo para divisão de arquivos PDF.
Suporta: dividir a cada N páginas ou dividir em N partes homogêneas.
"""

from pathlib import Path

from pypdf import PdfReader, PdfWriter
from tqdm import tqdm


def _caminho_saida_unico(pasta_saida: Path, nome_arquivo: str) -> Path:
    """Retorna um caminho que não sobrescreve arquivos existentes."""
    caminho = pasta_saida / nome_arquivo
    if not caminho.exists():
        return caminho

    stem = Path(nome_arquivo).stem
    sufixo = Path(nome_arquivo).suffix
    contador = 2
    while True:
        nome_futuro = f"{stem}_{contador}{sufixo}"
        caminho_futuro = pasta_saida / nome_futuro
        if not caminho_futuro.exists():
            return caminho_futuro
        contador += 1


def dividir_por_paginas(
    caminho_entrada: str,
    paginas_por_parte: int,
    pasta_saida: str | None = None,
    prefixo_nome: str = "parte",
) -> list[str]:
    """
    Divide o PDF em vários arquivos, cada um com um número fixo de páginas.

    Args:
        caminho_entrada: Caminho do arquivo PDF de entrada.
        paginas_por_parte: Quantidade de páginas em cada parte.
        pasta_saida: Pasta onde salvar os PDFs. Se None, usa a pasta do arquivo de entrada.
        prefixo_nome: Prefixo do nome dos arquivos gerados (ex: parte_01.pdf).

    Returns:
        Lista com os caminhos dos arquivos gerados.
    """
    if paginas_por_parte < 1:
        raise ValueError("paginas_por_parte deve ser pelo menos 1.")

    caminho_entrada = Path(caminho_entrada)
    if not caminho_entrada.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_entrada}")

    if pasta_saida is None:
        pasta_saida = caminho_entrada.parent
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    leitor = PdfReader(str(caminho_entrada))
    total_paginas = len(leitor.pages)
    total_partes = (total_paginas + paginas_por_parte - 1) // paginas_por_parte
    arquivos_gerados = []

    numero_parte = 1
    pagina_inicial = 0

    with tqdm(total=total_partes, desc="Dividindo PDF", unit="parte") as barra:
        while pagina_inicial < total_paginas:
            pagina_final = min(pagina_inicial + paginas_por_parte, total_paginas)
            escritor = PdfWriter()

            for indice in range(pagina_inicial, pagina_final):
                escritor.add_page(leitor.pages[indice])

            nome_arquivo = f"{prefixo_nome}_{numero_parte:02d}.pdf"
            caminho_saida = _caminho_saida_unico(pasta_saida, nome_arquivo)
            with open(caminho_saida, "wb") as arquivo:
                escritor.write(arquivo)

            arquivos_gerados.append(str(caminho_saida))
            numero_parte += 1
            pagina_inicial = pagina_final
            barra.update(1)

    return arquivos_gerados


def dividir_em_partes(
    caminho_entrada: str,
    numero_partes: int,
    pasta_saida: str | None = None,
    prefixo_nome: str = "parte",
) -> list[str]:
    """
    Divide o PDF em N partes com quantidade de páginas o mais homogênea possível.

    Args:
        caminho_entrada: Caminho do arquivo PDF de entrada.
        numero_partes: Em quantas partes dividir.
        pasta_saida: Pasta onde salvar os PDFs. Se None, usa a pasta do arquivo de entrada.
        prefixo_nome: Prefixo do nome dos arquivos gerados.

    Returns:
        Lista com os caminhos dos arquivos gerados.
    """
    if numero_partes < 1:
        raise ValueError("numero_partes deve ser pelo menos 1.")

    caminho_entrada = Path(caminho_entrada)
    if not caminho_entrada.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_entrada}")

    if pasta_saida is None:
        pasta_saida = caminho_entrada.parent
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    leitor = PdfReader(str(caminho_entrada))
    total_paginas = len(leitor.pages)

    if numero_partes > total_paginas:
        raise ValueError(
            f"O PDF tem {total_paginas} página(s). "
            f"Não é possível dividir em {numero_partes} partes."
        )

    # Distribuição homogênea: primeiras (total % numero_partes) partes têm uma página a mais
    paginas_por_parte_base = total_paginas // numero_partes
    resto = total_paginas % numero_partes

    tamanhos = []
    for i in range(numero_partes):
        extra = 1 if i < resto else 0
        tamanhos.append(paginas_por_parte_base + extra)

    arquivos_gerados = []
    pagina_atual = 0

    for numero_parte, qtd_paginas in enumerate(tqdm(tamanhos, desc="Dividindo PDF", unit="parte"), start=1):
        escritor = PdfWriter()
        for _ in range(qtd_paginas):
            escritor.add_page(leitor.pages[pagina_atual])
            pagina_atual += 1

        nome_arquivo = f"{prefixo_nome}_{numero_parte:02d}.pdf"
        caminho_saida = _caminho_saida_unico(pasta_saida, nome_arquivo)
        with open(caminho_saida, "wb") as arquivo:
            escritor.write(arquivo)

        arquivos_gerados.append(str(caminho_saida))

    return arquivos_gerados
