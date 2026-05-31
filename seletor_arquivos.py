# -*- coding: utf-8 -*-
"""
Diálogos nativos do Windows para seleção de arquivos e pastas.
Persiste a última pasta utilizada em config_usuario.json.
"""

import json
import os
import sys
from pathlib import Path

from recursos import caminho_config_usuario

CHAVE_ULTIMA_PASTA = "ultima_pasta"


def dialogos_disponiveis() -> bool:
    return sys.platform == "win32"


def _carregar_ultima_pasta() -> str | None:
    arquivo = caminho_config_usuario()
    if not arquivo.exists():
        return None
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
        pasta = dados.get(CHAVE_ULTIMA_PASTA)
        if pasta and Path(pasta).is_dir():
            return str(Path(pasta).resolve())
    except Exception:
        pass
    return None


def _salvar_ultima_pasta(caminho: str | Path) -> None:
    p = Path(caminho)
    pasta = p.parent if p.is_file() else p
    if not pasta.is_dir():
        return
    pasta_str = str(pasta.resolve())
    arquivo = caminho_config_usuario()
    dados: dict = {}
    if arquivo.exists():
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
        except Exception:
            dados = {}
    dados[CHAVE_ULTIMA_PASTA] = pasta_str
    try:
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _diretorio_inicial(caminho: str | Path | None = None) -> str | None:
    if caminho:
        p = Path(caminho)
        if p.is_file():
            p = p.parent
        if p.is_dir():
            return str(p.resolve())
    return _carregar_ultima_pasta() or str(Path.home())


def _criar_root():
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.update_idletasks()
    return root


def _registrar_selecao(caminho: str | None) -> None:
    if caminho:
        _salvar_ultima_pasta(caminho)


def selecionar_arquivos_convertiveis(
    titulo: str = "Selecione os arquivos para converter",
    diretorio_inicial: str | Path | None = None,
) -> list[str]:
    """Abre diálogo para escolher vários arquivos convertíveis. Preserva a ordem de seleção."""
    if not dialogos_disponiveis():
        return []

    from converter_para_pdf import FILTROS_DIALOGO
    from tkinter import filedialog

    root = _criar_root()
    try:
        caminhos = filedialog.askopenfilenames(
            title=titulo,
            initialdir=_diretorio_inicial(diretorio_inicial),
            filetypes=FILTROS_DIALOGO,
        )
        lista = list(caminhos)
        if lista:
            _registrar_selecao(lista[0])
        return lista
    finally:
        root.destroy()


def selecionar_arquivo_convertivel(
    titulo: str = "Selecione o arquivo para converter",
    diretorio_inicial: str | Path | None = None,
) -> str | None:
    """Abre diálogo para escolher um arquivo convertível para PDF."""
    if not dialogos_disponiveis():
        return None

    from converter_para_pdf import FILTROS_DIALOGO
    from tkinter import filedialog

    root = _criar_root()
    try:
        caminho = filedialog.askopenfilename(
            title=titulo,
            initialdir=_diretorio_inicial(diretorio_inicial),
            filetypes=FILTROS_DIALOGO,
        )
        _registrar_selecao(caminho or None)
        return caminho or None
    finally:
        root.destroy()


def selecionar_arquivo_pdf(
    titulo: str = "Selecione um arquivo PDF",
    diretorio_inicial: str | Path | None = None,
) -> str | None:
    if not dialogos_disponiveis():
        return None

    from tkinter import filedialog

    root = _criar_root()
    try:
        caminho = filedialog.askopenfilename(
            title=titulo,
            initialdir=_diretorio_inicial(diretorio_inicial),
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        _registrar_selecao(caminho or None)
        return caminho or None
    finally:
        root.destroy()


def selecionar_arquivos_pdf(
    titulo: str = "Selecione um ou mais arquivos PDF",
    diretorio_inicial: str | Path | None = None,
) -> list[str]:
    if not dialogos_disponiveis():
        return []

    from tkinter import filedialog

    root = _criar_root()
    try:
        caminhos = filedialog.askopenfilenames(
            title=titulo,
            initialdir=_diretorio_inicial(diretorio_inicial),
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        lista = list(caminhos)
        if lista:
            _registrar_selecao(lista[0])
        return lista
    finally:
        root.destroy()


def selecionar_pasta(
    titulo: str = "Selecione uma pasta",
    diretorio_inicial: str | Path | None = None,
) -> str | None:
    if not dialogos_disponiveis():
        return None

    from tkinter import filedialog

    root = _criar_root()
    try:
        caminho = filedialog.askdirectory(
            title=titulo,
            initialdir=_diretorio_inicial(diretorio_inicial),
            mustexist=True,
        )
        _registrar_selecao(caminho or None)
        return caminho or None
    finally:
        root.destroy()


def salvar_arquivo_pdf(
    titulo: str = "Salvar PDF como",
    nome_sugerido: str = "documento.pdf",
    diretorio_inicial: str | Path | None = None,
) -> str | None:
    if not dialogos_disponiveis():
        return None

    from tkinter import filedialog

    root = _criar_root()
    try:
        caminho = filedialog.asksaveasfilename(
            title=titulo,
            initialdir=_diretorio_inicial(diretorio_inicial),
            initialfile=nome_sugerido,
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        _registrar_selecao(caminho or None)
        return caminho or None
    finally:
        root.destroy()


def abrir_pasta_explorador(pasta: str | Path) -> None:
    """Abre a pasta no Explorador de Arquivos do Windows."""
    caminho = Path(pasta).resolve()
    if not caminho.is_dir():
        caminho = caminho.parent
    if sys.platform == "win32":
        os.startfile(str(caminho))
    elif sys.platform == "darwin":
        os.system(f'open "{caminho}"')
    else:
        os.system(f'xdg-open "{caminho}"')
