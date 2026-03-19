# -*- coding: utf-8 -*-
"""
Módulo para tradução de PDF mantendo formatação e imagens.
Usa PyMuPDF para preservar layout, imagens e substituir apenas o texto pelo traduzido.
Tradução em paralelo por threads para melhor desempenho (I/O da API), sem alterar qualidade.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import fitz  # PyMuPDF
from tqdm import tqdm

from configuracoes import (
    IDIOMA_TRADUCAO_PADRAO,
    NUMERO_WORKERS_TRADUCAO,
    TAMANHO_MINIMO_TEXTO_TRADUCAO,
)


def _traduzir_texto(
    texto: str,
    idioma_origem: str | None,
    idioma_destino: str,
    provedor: str = "google",
) -> str:
    """Traduz um trecho de texto usando Google Translate (com retentativas)."""
    import time

    texto = texto.strip()
    if not texto or len(texto) < TAMANHO_MINIMO_TEXTO_TRADUCAO:
        return texto

    ultimo_erro = None
    for tentativa in range(3):
        try:
            from deep_translator import GoogleTranslator

            tradutor = GoogleTranslator(
                source=idioma_origem or "auto",
                target=idioma_destino,
            )
            resultado = tradutor.translate(texto)
            if resultado is None or (isinstance(resultado, str) and not resultado.strip()):
                return texto
            return resultado
        except Exception as e:
            ultimo_erro = e
            if tentativa < 2:
                time.sleep(1.0 + tentativa * 0.5)
    return f"{texto} [erro tradução: {ultimo_erro}]"


def _testar_api_traducao(idioma_origem: str | None, idioma_destino: str) -> None:
    """Testa se a API do Google Translate responde. Levanta exceção em caso de falha."""
    try:
        from deep_translator import GoogleTranslator

        tradutor = GoogleTranslator(
            source=idioma_origem or "auto",
            target=idioma_destino,
        )
        resultado = tradutor.translate("Hello")
        if not resultado or not str(resultado).strip():
            raise RuntimeError(
                "A API do Google Translate não retornou texto. "
                "Tente novamente mais tarde ou verifique sua conexão."
            )
    except Exception as e:
        raise RuntimeError(
            "Não foi possível conectar ao Google Translate. "
            "Verifique sua internet ou tente novamente mais tarde.\n"
            f"Detalhe: {e}"
        ) from e


def _mapear_fonte_base(nome_fonte: str) -> str:
    """Mapeia nome da fonte do PDF para uma das fontes Base14 (helv, times, courier)."""
    if not nome_fonte:
        return "helv"
    n = nome_fonte.lower()
    if "times" in n or "serif" in n:
        return "times"
    if "courier" in n or "mono" in n:
        return "courier"
    return "helv"


def _obter_blocos_de_texto(pagina: fitz.Page) -> list[dict]:
    """Extrai blocos de texto da página com posição, tamanho e fonte (para preservar formatação)."""
    dict_texto = pagina.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    blocos = []
    for bloco in dict_texto.get("blocks", []):
        for linha in bloco.get("lines", []):
            for span in linha.get("spans", []):
                texto = span.get("text", "").strip()
                if not texto:
                    continue
                bbox = span.get("bbox")
                if not bbox or len(bbox) != 4:
                    continue
                tamanho = span.get("size", 11)
                nome_fonte = span.get("font", "")
                blocos.append({
                    "texto": texto,
                    "bbox": bbox,
                    "tamanho_fonte": tamanho,
                    "fonte": _mapear_fonte_base(nome_fonte),
                })
    return blocos


def _traduzir_bloco_em_thread(
    indice: int,
    texto: str,
    idioma_origem: str | None,
    idioma_destino: str,
    provedor: str,
) -> tuple[int, str]:
    """Traduz um único bloco (para uso em thread). Retorna (índice, texto_traduzido)."""
    return (indice, _traduzir_texto(texto, idioma_origem, idioma_destino, provedor))


def traduzir_pdf(
    caminho_entrada: str,
    caminho_saida: str,
    idioma_destino: str = IDIOMA_TRADUCAO_PADRAO,
    idioma_origem: str | None = None,
    provedor: str = "google",
    numero_workers: int | None = None,
) -> str:
    """
    Gera um novo PDF com todo o texto traduzido, mantendo imagens e layout.
    Usa Google Translate e threads para traduzir vários blocos em paralelo.
    O texto é colocado na mesma área do original; a fonte é reduzida se necessário para caber.

    Args:
        caminho_entrada: Caminho do PDF original.
        caminho_saida: Caminho do PDF traduzido a ser gerado.
        idioma_destino: Código do idioma de destino (ex: "pt", "en", "es").
        idioma_origem: Código do idioma de origem; None para detecção automática.
        provedor: Ignorado; a tradução usa sempre Google Translate.
        numero_workers: Threads para tradução; None usa NUMERO_WORKERS_TRADUCAO.

    Returns:
        Caminho do arquivo gerado.
    """
    caminho_entrada = Path(caminho_entrada)
    caminho_saida = Path(caminho_saida)
    workers = numero_workers if numero_workers is not None else NUMERO_WORKERS_TRADUCAO

    if not caminho_entrada.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_entrada}")

    if caminho_entrada.is_dir():
        raise ValueError("O caminho informado é uma pasta. Informe o caminho de um arquivo PDF (ex: arquivo.pdf).")

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    try:
        documento = fitz.open(str(caminho_entrada))
    except Exception as e:
        if "no file" in str(e).lower() or "cannot open" in str(e).lower():
            raise ValueError(
                "O arquivo não é um PDF válido ou o caminho está incorreto. "
                "Use um arquivo com extensão .pdf (ex: C:\\pasta\\arquivo.pdf)."
            ) from e
        raise

    total_paginas = len(documento)

    # Testa a API antes de começar (falha rápido se não houver conexão)
    _testar_api_traducao(idioma_origem, idioma_destino)

    paginas_sem_texto = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for indice_pagina in tqdm(range(total_paginas), desc="Traduzindo PDF", unit="página"):
            pagina = documento[indice_pagina]
            blocos = _obter_blocos_de_texto(pagina)

            if not blocos:
                paginas_sem_texto += 1
                continue

            # Submete todas as traduções da página em paralelo (mantém ordem pelos índices)
            futuras = {
                executor.submit(
                    _traduzir_bloco_em_thread,
                    i,
                    bloco["texto"],
                    idioma_origem,
                    idioma_destino,
                    provedor,
                ): i
                for i, bloco in enumerate(blocos)
            }

            # Coleta resultados na ordem dos blocos (qualidade e layout idênticos)
            textos_traduzidos: list[str] = [""] * len(blocos)
            for futura in as_completed(futuras):
                indice, texto_trad = futura.result()
                textos_traduzidos[indice] = texto_trad

            # Guardar links antes da redação (apply_redactions pode removê-los)
            links_pagina = pagina.get_links()

            # Redação: substitui o texto na mesma área do bloco; o motor reduz a fonte para caber.
            for bloco, texto_traduzido in zip(blocos, textos_traduzidos):
                if not (texto_traduzido or texto_traduzido.strip()):
                    continue
                bbox = bloco["bbox"]
                rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
                tamanho_orig = bloco["tamanho_fonte"]
                fonte = bloco.get("fonte", "helv")
                pagina.add_redact_annot(
                    rect,
                    text=texto_traduzido,
                    fontsize=tamanho_orig,
                    fontname=fonte,
                    fill=(1, 1, 1),
                    text_color=(0, 0, 0),
                    cross_out=False,
                )
            pagina.apply_redactions()

            # Reinserir links de navegação
            for link in links_pagina:
                try:
                    pagina.insert_link(link)
                except Exception:
                    pass

    if paginas_sem_texto > 0:
        import sys
        print(
            f"\n  Aviso: {paginas_sem_texto} página(s) sem texto extraível "
            "(pode ser PDF escaneado ou só imagens).",
            file=sys.stderr,
        )

    documento.save(str(caminho_saida), garbage=4, deflate=True)
    documento.close()

    return str(caminho_saida)


def criar_pdf_duas_colunas(
    caminho_original: str,
    caminho_traduzido: str,
    caminho_saida: str,
) -> str:
    """
    Cria um PDF com duas colunas por página: esquerda = original, direita = traduzido.
    Útil para leitura lado a lado (original e tradução ao mesmo tempo).

    Args:
        caminho_original: PDF original.
        caminho_traduzido: PDF já traduzido (mesmo número de páginas).
        caminho_saida: Onde salvar o PDF de duas colunas.

    Returns:
        Caminho do arquivo gerado.
    """
    path_orig = Path(caminho_original)
    path_trad = Path(caminho_traduzido)
    path_saida = Path(caminho_saida)

    if not path_orig.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path_orig}")
    if not path_trad.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path_trad}")

    path_saida.parent.mkdir(parents=True, exist_ok=True)

    doc_orig = fitz.open(str(path_orig))
    doc_trad = fitz.open(str(path_trad))

    try:
        n = len(doc_orig)
        if len(doc_trad) != n:
            raise ValueError(
                f"O PDF traduzido tem {len(doc_trad)} páginas e o original tem {n}. "
                "Devem ter o mesmo número de páginas."
            )

        doc_saida = fitz.open()

        for i in range(n):
            page_orig = doc_orig[i]
            page_trad = doc_trad[i]
            r = page_orig.rect
            w, h = r.width, r.height
            # Nova página: largura = 2 * largura original, mesma altura
            nova_pagina = doc_saida.new_page(width=2 * w, height=h)
            rect_esquerda = fitz.Rect(0, 0, w, h)
            rect_direita = fitz.Rect(w, 0, 2 * w, h)
            nova_pagina.show_pdf_page(rect_esquerda, doc_orig, i)
            nova_pagina.show_pdf_page(rect_direita, doc_trad, i)

            # show_pdf_page não copia anotações/links; copiar manualmente
            for link in page_orig.get_links():
                try:
                    nova_pagina.insert_link(link)
                except Exception:
                    pass
            for link in page_trad.get_links():
                try:
                    rfrom = link.get("from") or link.get("rect")
                    if rfrom is not None:
                        rfrom = fitz.Rect(rfrom)
                        link = dict(link)
                        link["from"] = fitz.Rect(rfrom.x0 + w, rfrom.y0, rfrom.x1 + w, rfrom.y1)
                    nova_pagina.insert_link(link)
                except Exception:
                    pass

        doc_saida.save(str(path_saida), garbage=4, deflate=True)
        doc_saida.close()
    finally:
        doc_orig.close()
        doc_trad.close()

    return str(path_saida)
