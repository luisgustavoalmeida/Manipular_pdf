# -*- coding: utf-8 -*-
"""
Conversão de diversos formatos para PDF.

Suporta:
  - Imagens (JPG, PNG, GIF, BMP, TIFF, WEBP)
  - Texto (TXT, MD, CSV, LOG, JSON, XML)
  - HTML (HTML, HTM)
  - Office (DOC, DOCX, XLS, XLSX, PPT, PPTX, ODT, ODS, ODP, RTF) via LibreOffice
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz
from tqdm import tqdm

from progresso import OperacaoCancelada, RelatorioProgresso, limpar_arquivos_gerados, percorrer

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp"}
EXTENSOES_TEXTO = {".txt", ".md", ".csv", ".log", ".json", ".xml"}
EXTENSOES_HTML = {".html", ".htm"}
EXTENSOES_OFFICE = {
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".odt", ".ods", ".odp", ".rtf",
}
EXTENSOES_SUPORTADAS = EXTENSOES_IMAGEM | EXTENSOES_TEXTO | EXTENSOES_HTML | EXTENSOES_OFFICE

FILTROS_DIALOGO = [
    (
        "Todos os formatos suportados",
        " ".join(f"*{e}" for e in sorted(EXTENSOES_SUPORTADAS)),
    ),
    ("Documentos Office", " ".join(f"*{e}" for e in sorted(EXTENSOES_OFFICE))),
    ("Imagens", " ".join(f"*{e}" for e in sorted(EXTENSOES_IMAGEM))),
    ("Texto e Web", " ".join(f"*{e}" for e in sorted(EXTENSOES_TEXTO | EXTENSOES_HTML))),
    ("Todos os arquivos", "*.*"),
]

MSG_LIBREOFFICE = (
    "Para converter Word, Excel e PowerPoint é necessário o LibreOffice instalado.\n"
    "Download: https://www.libreoffice.org/download/download/"
)


def formatos_suportados_texto() -> str:
    """Lista legível dos formatos aceitos."""
    grupos = [
        ("Imagens", EXTENSOES_IMAGEM),
        ("Office", EXTENSOES_OFFICE),
        ("Texto", EXTENSOES_TEXTO),
        ("Web", EXTENSOES_HTML),
    ]
    partes = []
    for nome, exts in grupos:
        partes.append(f"{nome}: {', '.join(sorted(e.lstrip('.').upper() for e in exts))}")
    return " | ".join(partes)


def _classificar(arquivo: Path) -> str | None:
    ext = arquivo.suffix.lower()
    if ext in EXTENSOES_IMAGEM:
        return "imagem"
    if ext in EXTENSOES_TEXTO:
        return "texto"
    if ext in EXTENSOES_HTML:
        return "html"
    if ext in EXTENSOES_OFFICE:
        return "office"
    return None


def arquivo_e_convertivel(arquivo: str | Path) -> bool:
    """Retorna True se o arquivo possui formato suportado para conversão."""
    return _classificar(Path(arquivo)) is not None


def _ler_texto(arquivo: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return arquivo.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return arquivo.read_text(encoding="utf-8", errors="replace")


def _salvar_pdf(documento: fitz.Document, destino: Path) -> None:
    if destino.exists() and destino.is_dir():
        raise IsADirectoryError(f"O caminho de saída é uma pasta: {destino}")
    destino.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(suffix=".pdf", dir=destino.parent)
    os.close(fd)
    try:
        documento.save(temp_path)
        os.replace(temp_path, destino)
    except Exception:
        Path(temp_path).unlink(missing_ok=True)
        raise


def _normalizar_saida(arquivo_ou_pasta: Path, caminho_saida: str | Path | None) -> Path:
    if caminho_saida:
        saida = Path(caminho_saida)
        if saida.exists() and saida.is_dir():
            return saida / f"{arquivo_ou_pasta.stem}.pdf"
        if saida.suffix.lower() != ".pdf":
            return saida.with_suffix(".pdf")
        return saida
    if arquivo_ou_pasta.is_dir():
        return arquivo_ou_pasta / "convertidos.pdf"
    return arquivo_ou_pasta.with_suffix(".pdf")


def _converter_imagem_unica(arquivo: Path) -> fitz.Document:
    img_doc = fitz.open(str(arquivo))
    try:
        pdf_bytes = img_doc.convert_to_pdf()
        return fitz.open("pdf", pdf_bytes)
    finally:
        img_doc.close()


def _converter_imagens_lista(imagens: list[Path], destino: Path) -> None:
    pdf_final = fitz.open()
    try:
        for caminho in imagens:
            pagina = _converter_imagem_unica(caminho)
            try:
                pdf_final.insert_pdf(pagina)
            finally:
                pagina.close()
        _salvar_pdf(pdf_final, destino)
    finally:
        pdf_final.close()


def _converter_texto(arquivo: Path, destino: Path) -> None:
    texto = _ler_texto(arquivo)
    doc = fitz.open()
    try:
        largura, altura = fitz.paper_size("a4")
        margem = 50
        fontsize = 11
        restante = texto
        while restante:
            pagina = doc.new_page(width=largura, height=altura)
            rect = fitz.Rect(margem, margem, largura - margem, altura - margem)
            restante = pagina.insert_textbox(
                rect, restante, fontsize=fontsize, fontname="helv"
            )
        _salvar_pdf(doc, destino)
    finally:
        doc.close()


def _converter_html(arquivo: Path, destino: Path) -> None:
    conteudo = _ler_texto(arquivo)
    doc = fitz.open()
    try:
        story = fitz.Story(html=conteudo)
        mediabox = fitz.paper_rect("a4")
        area = mediabox + (36, 36, -36, -36)
        while True:
            pagina = doc.new_page(width=mediabox.width, height=mediabox.height)
            restante, _ = story.place(area)
            story.draw(pagina, area)
            if not restante:
                break
        _salvar_pdf(doc, destino)
    except Exception:
        doc.close()
        _converter_texto(arquivo, destino)
        return
    finally:
        if not doc.is_closed:
            doc.close()


def _encontrar_libreoffice() -> Path | None:
    candidatos = [
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
    ]
    for candidato in candidatos:
        if candidato.is_file():
            return candidato
    encontrado = shutil.which("soffice") or shutil.which("libreoffice")
    return Path(encontrado) if encontrado else None


def libreoffice_disponivel() -> bool:
    return _encontrar_libreoffice() is not None


def _converter_office(arquivo: Path, destino: Path) -> None:
    soffice = _encontrar_libreoffice()
    if not soffice:
        raise RuntimeError(MSG_LIBREOFFICE)

    pasta_temp = destino.parent
    pasta_temp.mkdir(parents=True, exist_ok=True)

    resultado = subprocess.run(
        [
            str(soffice),
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(pasta_temp),
            str(arquivo.resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if resultado.returncode != 0:
        detalhe = (resultado.stderr or resultado.stdout or "").strip()
        raise RuntimeError(
            f"LibreOffice não conseguiu converter '{arquivo.name}'. {detalhe}"
        )

    pdf_gerado = pasta_temp / f"{arquivo.stem}.pdf"
    if not pdf_gerado.exists():
        raise RuntimeError(f"Conversão concluída, mas o PDF não foi encontrado: {pdf_gerado}")

    if pdf_gerado.resolve() != destino.resolve():
        if destino.exists():
            destino.unlink()
        os.replace(pdf_gerado, destino)


def _arquivo_para_documento(arquivo: Path, temporarios: list[Path] | None = None) -> fitz.Document:
    """Converte um arquivo suportado em documento PDF em memória."""
    tipo = _classificar(arquivo)
    if not tipo:
        raise ValueError(f"Formato não suportado: {arquivo.suffix}")

    if tipo == "imagem":
        return _converter_imagem_unica(arquivo)

    fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    temp_pdf = Path(temp_path)
    if temporarios is not None:
        temporarios.append(temp_pdf)

    try:
        if tipo == "texto":
            _converter_texto(arquivo, temp_pdf)
        elif tipo == "html":
            _converter_html(arquivo, temp_pdf)
        elif tipo == "office":
            _converter_office(arquivo, temp_pdf)
        return fitz.open(str(temp_pdf))
    except Exception:
        temp_pdf.unlink(missing_ok=True)
        if temporarios is not None and temp_pdf in temporarios:
            temporarios.remove(temp_pdf)
        raise


def _unir_documentos(documentos: list[fitz.Document], destino: Path) -> None:
    pdf_final = fitz.open()
    try:
        for doc in documentos:
            pdf_final.insert_pdf(doc)
        _salvar_pdf(pdf_final, destino)
    finally:
        pdf_final.close()


def converter_arquivo_para_pdf(
    arquivo: str | Path,
    caminho_saida: str | Path | None = None,
) -> str:
    """Converte um único arquivo suportado para PDF."""
    origem = Path(arquivo).resolve()
    if not origem.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {origem}")

    tipo = _classificar(origem)
    if not tipo:
        raise ValueError(
            f"Formato não suportado: {origem.suffix}. "
            f"Formatos aceitos: {', '.join(sorted(EXTENSOES_SUPORTADAS))}"
        )

    destino = _normalizar_saida(origem, caminho_saida).resolve()

    if tipo == "imagem":
        pdf = _converter_imagem_unica(origem)
        try:
            _salvar_pdf(pdf, destino)
        finally:
            pdf.close()
    elif tipo == "texto":
        _converter_texto(origem, destino)
    elif tipo == "html":
        _converter_html(origem, destino)
    elif tipo == "office":
        _converter_office(origem, destino)

    return str(destino)


def _caminho_pdf_unico(pasta: Path, nome_arquivo: str) -> Path:
    """Retorna caminho PDF que não sobrescreve arquivos existentes."""
    caminho = pasta / nome_arquivo
    if not caminho.exists():
        return caminho
    stem = Path(nome_arquivo).stem
    sufixo = Path(nome_arquivo).suffix
    contador = 2
    while True:
        candidato = pasta / f"{stem}_{contador}{sufixo}"
        if not candidato.exists():
            return candidato
        contador += 1


def converter_arquivos_para_pdfs_individuais(
    arquivos: list[str | Path],
    pasta_saida: str | Path | None = None,
    progresso: RelatorioProgresso | None = None,
) -> list[str]:
    """Converte cada arquivo em um PDF separado na pasta de saída."""
    if not arquivos:
        raise ValueError("Nenhum arquivo informado.")

    caminhos = [Path(a).resolve() for a in arquivos]
    for caminho in caminhos:
        if not caminho.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
        if not arquivo_e_convertivel(caminho):
            raise ValueError(f"Formato não suportado: {caminho.name}")

    if pasta_saida:
        destino_dir = Path(pasta_saida).resolve()
        if destino_dir.is_file():
            destino_dir = destino_dir.parent
    else:
        destino_dir = caminhos[0].parent

    destino_dir.mkdir(parents=True, exist_ok=True)

    gerados: list[str] = []
    try:
        for caminho in percorrer(
            caminhos,
            descricao="Convertendo arquivos",
            progresso=progresso,
            unit="arquivo",
        ):
            destino = _caminho_pdf_unico(destino_dir, f"{caminho.stem}.pdf")
            gerados.append(converter_arquivo_para_pdf(caminho, destino))

        return gerados
    except OperacaoCancelada:
        limpar_arquivos_gerados(gerados)
        raise


def converter_arquivos_para_pdf(
    arquivos: list[str | Path],
    caminho_saida: str | Path | None = None,
    progresso: RelatorioProgresso | None = None,
) -> str:
    """
    Converte um ou mais arquivos em um único PDF.

    A ordem da lista define a ordem das páginas no PDF final.
    """
    if not arquivos:
        raise ValueError("Nenhum arquivo informado.")

    caminhos = [Path(a).resolve() for a in arquivos]
    for caminho in caminhos:
        if not caminho.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
        if not arquivo_e_convertivel(caminho):
            raise ValueError(f"Formato não suportado: {caminho.name}")

    if len(caminhos) == 1:
        destino = _normalizar_saida(caminhos[0], caminho_saida).resolve()
        try:
            if progresso:
                progresso.iniciar(1, "Convertendo arquivo")
                resultado = converter_arquivo_para_pdf(caminhos[0], caminho_saida)
                progresso.concluir()
                return resultado
            return converter_arquivo_para_pdf(caminhos[0], caminho_saida)
        except OperacaoCancelada:
            limpar_arquivos_gerados([destino])
            raise

    if caminho_saida:
        destino = _normalizar_saida(caminhos[0], caminho_saida).resolve()
    else:
        destino = caminhos[0].parent / "documento_convertido.pdf"

    temporarios: list[Path] = []
    documentos: list[fitz.Document] = []
    try:
        for caminho in percorrer(
            caminhos,
            descricao="Convertendo arquivos",
            progresso=progresso,
            unit="arquivo",
        ):
            doc = _arquivo_para_documento(caminho, temporarios)
            documentos.append(doc)
        _unir_documentos(documentos, destino)
    except OperacaoCancelada:
        limpar_arquivos_gerados([destino])
        raise
    finally:
        for doc in documentos:
            if not doc.is_closed:
                doc.close()
        for temp in temporarios:
            temp.unlink(missing_ok=True)

    return str(destino)


def _listar_convertiveis(pasta: Path) -> dict[str, list[Path]]:
    grupos: dict[str, list[Path]] = {
        "imagem": [],
        "texto": [],
        "html": [],
        "office": [],
    }
    for item in pasta.iterdir():
        if not item.is_file():
            continue
        tipo = _classificar(item)
        if tipo:
            grupos[tipo].append(item)
    for chave in grupos:
        grupos[chave] = sorted(grupos[chave], key=lambda p: p.name.lower())
    return grupos


def converter_pasta_para_pdf(
    pasta: str | Path,
    pasta_saida: str | Path | None = None,
    juntar_imagens: bool = True,
    progresso: RelatorioProgresso | None = None,
) -> list[str]:
    """
    Converte arquivos suportados de uma pasta.

    - Imagens: um PDF único (juntar_imagens=True) ou um PDF por imagem.
    - Demais formatos: um PDF por arquivo.
    """
    origem = Path(pasta).resolve()
    if not origem.is_dir():
        raise NotADirectoryError(f"Não é uma pasta válida: {origem}")

    destino_dir = Path(pasta_saida).resolve() if pasta_saida else origem
    destino_dir.mkdir(parents=True, exist_ok=True)

    grupos = _listar_convertiveis(origem)
    total = sum(len(v) for v in grupos.values())
    if total == 0:
        raise ValueError(
            f"Nenhum arquivo convertível em {origem}. {formatos_suportados_texto()}"
        )

    gerados: list[str] = []

    try:
        if progresso:
            progresso.iniciar(total, "Convertendo pasta")

        if grupos["imagem"]:
            if juntar_imagens:
                caminho = destino_dir / "imagens.pdf"
                if progresso:
                    progresso.avancar(0, "Unindo imagens")
                _converter_imagens_lista(grupos["imagem"], caminho)
                gerados.append(str(caminho))
                if progresso:
                    progresso.avancar(len(grupos["imagem"]), "Imagens convertidas")
            else:
                for img in percorrer(
                    grupos["imagem"],
                    descricao="Imagens",
                    progresso=progresso,
                    unit="arquivo",
                    gerencia_ciclo=False,
                ):
                    dest = destino_dir / f"{img.stem}.pdf"
                    converter_arquivo_para_pdf(img, dest)
                    gerados.append(str(dest))

        outros = grupos["office"] + grupos["texto"] + grupos["html"]
        for arq in percorrer(
            outros,
            descricao="Convertendo arquivos",
            progresso=progresso,
            unit="arquivo",
            gerencia_ciclo=False,
        ):
            dest = destino_dir / f"{arq.stem}.pdf"
            converter_arquivo_para_pdf(arq, dest)
            gerados.append(str(dest))

        if progresso:
            progresso.concluir()

        return gerados
    except OperacaoCancelada:
        limpar_arquivos_gerados(gerados)
        raise


# Compatibilidade com o módulo anterior
def converter_imagens_para_pdf(
    pasta_imagens: str,
    caminho_saida: str | None = None,
) -> str:
    """Converte imagens de uma pasta em um único PDF (comportamento legado)."""
    pasta = Path(pasta_imagens).resolve()
    imagens = _listar_convertiveis(pasta)["imagem"]
    if not imagens:
        raise ValueError(
            f"Nenhuma imagem encontrada em {pasta}. "
            f"Formatos: {', '.join(sorted(EXTENSOES_IMAGEM))}"
        )
    destino = _normalizar_saida(pasta, caminho_saida).resolve()
    _converter_imagens_lista(imagens, destino)
    return str(destino)
