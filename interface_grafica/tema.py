# -*- coding: utf-8 -*-
"""Paleta de cores, dimensões e alternância claro/escuro da interface gráfica."""

from __future__ import annotations

import json
from typing import Literal

import customtkinter as ctk

ModoAparencia = Literal["dark", "light"]
CorTema = tuple[str, str]  # (claro, escuro) — formato nativo do CustomTkinter

from recursos import caminho_config_usuario

CHAVE_TEMA = "tema_aparencia"

MODO_ATUAL: ModoAparencia = "dark"


def _par(claro: str, escuro: str) -> CorTema:
    """Tupla (light, dark) para troca automática via CustomTkinter."""
    return (claro, escuro)


# Cores adaptativas — cada constante vale para claro e escuro ao mesmo tempo
COR_PRIMARIA = _par("#1a73e8", "#1a73e8")
COR_PRIMARIA_HOVER = _par("#1557b0", "#1557b0")
COR_FUNDO = _par("#f4f4f8", "#1e1e2e")
COR_FUNDO_SECUNDARIO = _par("#eaeaef", "#252536")
COR_FUNDO_CARD = _par("#ffffff", "#2a2a3d")
COR_BORDA = _par("#c5c5d2", "#3d3d5c")
COR_TEXTO = _par("#1c1c28", "#e8e8f0")
COR_TEXTO_SECUNDARIO = _par("#5f5f78", "#9898b0")
COR_SUCESSO = _par("#188038", "#34a853")
COR_AVISO = _par("#e37400", "#fbbc04")
COR_ERRO = _par("#d93025", "#ea4335")
COR_ERRO_HOVER = _par("#b3261e", "#c5221f")
COR_TEXTO_BOTAO_ATIVO = _par("#ffffff", "#ffffff")

# Dimensões
LARGURA_JANELA = 960
ALTURA_JANELA = 680
LARGURA_SIDEBAR = 240
ALTURA_CABECALHO = 72
PADDING = 16
RAIO_BORDA = 10

FONT_TITULO = ("Segoe UI", 22, "bold")
FONT_SUBTITULO = ("Segoe UI", 13, "bold")
FONT_CORPO = ("Segoe UI", 12)
FONT_PEQUENA = ("Segoe UI", 11)
FONT_BOTAO = ("Segoe UI", 12, "bold")


def carregar_tema_salvo() -> ModoAparencia:
    """Lê o tema salvo em config_usuario.json; padrão: escuro."""
    arquivo = caminho_config_usuario()
    if not arquivo.is_file():
        return "dark"
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        modo = dados.get(CHAVE_TEMA, "dark")
        if modo in ("dark", "light"):
            return modo  # type: ignore[return-value]
    except Exception:
        pass
    return "dark"


def salvar_tema(modo: ModoAparencia) -> None:
    """Persiste a preferência de tema."""
    arquivo = caminho_config_usuario()
    dados: dict = {}
    if arquivo.is_file():
        try:
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
        except Exception:
            dados = {}
    dados[CHAVE_TEMA] = modo
    try:
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_text(
            json.dumps(dados, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


def aplicar_tema(modo: ModoAparencia, persistir: bool = True) -> ModoAparencia:
    """Ativa claro/escuro; widgets com cores em tupla atualizam automaticamente."""
    global MODO_ATUAL

    if modo not in ("dark", "light"):
        modo = "dark"

    MODO_ATUAL = modo
    ctk.set_appearance_mode(modo)
    ctk.set_default_color_theme("blue")

    if persistir:
        salvar_tema(modo)

    return modo


def inicializar_tema() -> ModoAparencia:
    """Carrega e aplica o tema salvo (ou escuro)."""
    return aplicar_tema(carregar_tema_salvo(), persistir=False)


def alternar_tema() -> ModoAparencia:
    """Alterna entre claro e escuro."""
    novo: ModoAparencia = "light" if MODO_ATUAL == "dark" else "dark"
    return aplicar_tema(novo)


def _modo_ctk() -> str:
    return "Dark" if MODO_ATUAL == "dark" else "Light"


def _redesenhar_widget(widget) -> None:
    """Força atualização visual após troca de appearance mode."""
    modo = _modo_ctk()

    if hasattr(widget, "_set_appearance_mode"):
        try:
            widget._set_appearance_mode(modo)
        except Exception:
            pass

    if hasattr(widget, "_draw"):
        try:
            widget._draw()
        except Exception:
            pass

    if type(widget).__name__ == "CTkScrollableFrame":
        try:
            widget._parent_frame._draw()
            widget._scrollbar._draw()
            fundo = widget._parent_frame._apply_appearance_mode(widget._parent_frame._fg_color)
            if widget._parent_frame.cget("fg_color") in ("transparent", "Transparent"):
                fundo = widget._parent_frame._apply_appearance_mode(
                    widget._parent_frame._bg_color
                )
            widget._parent_canvas.configure(bg=fundo)
            widget.configure(bg=fundo)
        except Exception:
            pass


def forcar_redesenho_tema(janela, visitados: set[int] | None = None) -> None:
    """
    Percorre a árvore de widgets e força redesenho.

    O CustomTkinter atualiza o índice claro/escuro, mas vários widgets
    (CTkFrame, CTkLabel, CTkButton, CTkEntry…) não chamam _draw() sozinhos.
    """
    if visitados is None:
        visitados = set()

    wid = id(janela)
    if wid in visitados:
        return
    visitados.add(wid)

    _redesenhar_widget(janela)

    hook = getattr(janela, "refresh_apos_tema", None)
    if callable(hook):
        try:
            hook()
        except Exception:
            pass

    filhos: list = []
    try:
        filhos.extend(janela.winfo_children())
    except Exception:
        pass

    if hasattr(janela, "_parent_canvas"):
        try:
            filhos.extend(janela._parent_canvas.winfo_children())
        except Exception:
            pass

    if type(janela).__name__ == "Canvas":
        try:
            filhos.extend(janela.winfo_children())
        except Exception:
            pass

    for filho in filhos:
        forcar_redesenho_tema(filho, visitados)
