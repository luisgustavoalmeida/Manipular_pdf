# -*- coding: utf-8 -*-
"""Diálogo «Sobre» carregado a partir de sobre.json."""

from __future__ import annotations

import json
import sys
import webbrowser
from pathlib import Path
from typing import Any

import customtkinter as ctk

from interface_grafica import tema as t

from recursos import diretorio_recursos

ARQUIVO_SOBRE = "sobre.json"
_dialogo_aberto: DialogoSobre | None = None


def caminho_sobre_json() -> Path:
    return diretorio_recursos() / ARQUIVO_SOBRE


def carregar_sobre() -> dict[str, Any]:
    caminho = caminho_sobre_json()
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    return json.loads(caminho.read_text(encoding="utf-8"))


def _formatar_data(iso: str) -> str:
    partes = iso.split("-")
    if len(partes) == 3:
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return iso


def _abrir_url(url: str) -> None:
    if url:
        webbrowser.open(url)


class DialogoSobre(ctk.CTkToplevel):
    """Janela modal com informações do programa."""

    LARGURA = 520
    ALTURA = 580

    def __init__(self, master: ctk.CTk):
        super().__init__(master)
        self.title("Sobre")
        self.configure(fg_color=t.COR_FUNDO)
        self.resizable(True, True)
        self.minsize(420, 400)
        self.geometry(f"{self.LARGURA}x{self.ALTURA}")

        self._dados = carregar_sobre()
        self._montar_conteudo()
        self._centralizar(master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._fechar)
        self.bind("<Escape>", lambda _e: self._fechar())

    def refresh_apos_tema(self) -> None:
        """Hook chamado por forcar_redesenho_tema ao alternar claro/escuro."""
        self.configure(fg_color=t.COR_FUNDO)

    def _centralizar(self, master: ctk.CTk) -> None:
        self.update_idletasks()
        mx = master.winfo_rootx()
        my = master.winfo_rooty()
        mw = master.winfo_width()
        mh = master.winfo_height()
        w = self.winfo_width()
        h = self.winfo_height()
        x = mx + max(0, (mw - w) // 2)
        y = my + max(0, (mh - h) // 2)
        self.geometry(f"+{x}+{y}")

    def _fechar(self) -> None:
        global _dialogo_aberto
        _dialogo_aberto = None
        self.grab_release()
        self.destroy()

    def _secao(self, pai: ctk.CTkFrame, titulo: str) -> ctk.CTkFrame:
        bloco = ctk.CTkFrame(pai, fg_color="transparent")
        bloco.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(
            bloco,
            text=titulo,
            font=t.FONT_SUBTITULO,
            text_color=t.COR_TEXTO,
            anchor="w",
        ).pack(fill="x", pady=(0, 6))
        corpo = ctk.CTkFrame(bloco, fg_color="transparent")
        corpo.pack(fill="x")
        return corpo

    def _texto(self, pai: ctk.CTkFrame, texto: str, secundario: bool = False) -> None:
        ctk.CTkLabel(
            pai,
            text=texto,
            font=t.FONT_PEQUENA,
            text_color=t.COR_TEXTO_SECUNDARIO if secundario else t.COR_TEXTO,
            anchor="w",
            justify="left",
            wraplength=self.LARGURA - 56,
        ).pack(fill="x", pady=(0, 4))

    def _lista(self, pai: ctk.CTkFrame, itens: list[str]) -> None:
        for item in itens:
            self._texto(pai, f"•  {item}")

    def _link(self, pai: ctk.CTkFrame, rotulo: str, url: str) -> None:
        ctk.CTkButton(
            pai,
            text=rotulo,
            anchor="w",
            height=26,
            font=t.FONT_PEQUENA,
            fg_color="transparent",
            text_color=t.COR_PRIMARIA,
            hover_color=t.COR_FUNDO_CARD,
            command=lambda u=url: _abrir_url(u),
        ).pack(fill="x", anchor="w", pady=(0, 2))

    def _montar_conteudo(self) -> None:
        app = self._dados.get("aplicacao", {})
        criador = self._dados.get("criador", {})
        repo = self._dados.get("repositorio", {})
        doacao = self._dados.get("doacao", {})

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=t.COR_BORDA,
            scrollbar_button_hover_color=t.COR_PRIMARIA,
        )
        scroll.pack(fill="both", expand=True, padx=t.PADDING, pady=(t.PADDING, 8))

        # Cabeçalho
        cab = ctk.CTkFrame(scroll, fg_color=t.COR_FUNDO_CARD, corner_radius=t.RAIO_BORDA)
        cab.pack(fill="x", pady=(0, 16))
        inner = ctk.CTkFrame(cab, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        nome = app.get("nome_completo") or app.get("nome", "Manipulador PDF")
        ctk.CTkLabel(
            inner,
            text=f"📑  {nome}",
            font=t.FONT_TITULO,
            text_color=t.COR_TEXTO,
            anchor="w",
        ).pack(fill="x")

        versao = app.get("versao", "")
        data_ver = app.get("data_versao", "")
        meta = f"Versão {versao}"
        if data_ver:
            meta += f"  ·  {_formatar_data(data_ver)}"
        plataforma = app.get("plataforma")
        if plataforma:
            meta += f"  ·  {plataforma}"
        executavel = app.get("executavel")
        if executavel:
            meta += f"  ·  {executavel}"
        self._texto(inner, meta, secundario=True)

        subtitulo = self._dados.get("subtitulo", "")
        if subtitulo:
            self._texto(inner, subtitulo, secundario=True)

        descricao = app.get("descricao", "")
        if descricao:
            corpo = self._secao(scroll, "Descrição")
            self._texto(corpo, descricao)

        funcs = self._dados.get("funcionalidades", [])
        if funcs:
            corpo = self._secao(scroll, "Funcionalidades")
            self._lista(corpo, funcs)

        requisitos = self._dados.get("requisitos", [])
        if requisitos:
            corpo = self._secao(scroll, "Requisitos")
            self._lista(corpo, requisitos)

        instalacao = self._dados.get("instalacao", [])
        if instalacao:
            corpo = self._secao(scroll, "Como usar")
            self._lista(corpo, instalacao)

        suporte = self._dados.get("suporte", [])
        if suporte:
            corpo = self._secao(scroll, "Suporte")
            self._lista(corpo, suporte)

        historico = self._dados.get("historico_versoes", [])
        if historico:
            corpo = self._secao(scroll, "Histórico de versões")
            for item in historico:
                ver = item.get("versao", "?")
                data = _formatar_data(item.get("data", ""))
                notas = item.get("notas", "")
                self._texto(corpo, f"v{ver}  ({data})", secundario=False)
                if notas:
                    self._texto(corpo, notas, secundario=True)

        tecnologias = self._dados.get("tecnologias", [])
        if tecnologias:
            corpo = self._secao(scroll, "Tecnologias")
            for tech in tecnologias:
                nome_t = tech.get("nome", "")
                uso = tech.get("uso", "")
                linha = f"{nome_t} — {uso}" if uso else nome_t
                self._texto(corpo, f"•  {linha}", secundario=True)

        if criador:
            corpo = self._secao(scroll, "Desenvolvedor")
            if criador.get("nome"):
                self._texto(corpo, criador["nome"])
            if criador.get("papel"):
                self._texto(corpo, criador["papel"], secundario=True)
            if criador.get("organizacao"):
                self._texto(corpo, criador["organizacao"], secundario=True)
            if criador.get("email_profissional"):
                self._texto(corpo, criador["email_profissional"], secundario=True)
            if criador.get("email_pessoal"):
                self._texto(corpo, criador["email_pessoal"], secundario=True)
            if criador.get("linkedin"):
                self._link(corpo, "LinkedIn", criador["linkedin"])

        if repo.get("url"):
            corpo = self._secao(scroll, "Repositório")
            if repo.get("nome"):
                self._texto(corpo, repo["nome"], secundario=True)
            self._link(corpo, "Abrir no GitHub", repo["url"])

        if doacao.get("mensagem"):
            corpo = self._secao(scroll, "Apoio")
            self._texto(corpo, doacao["mensagem"], secundario=True)
            if doacao.get("chave_pix"):
                self._texto(corpo, f"PIX: {doacao['chave_pix']}", secundario=True)

        # Rodapé
        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=t.PADDING, pady=(0, t.PADDING))

        ctk.CTkButton(
            rodape,
            text="Fechar",
            width=100,
            height=32,
            font=t.FONT_CORPO,
            fg_color=t.COR_PRIMARIA,
            hover_color=t.COR_PRIMARIA_HOVER,
            command=self._fechar,
        ).pack(side="right")


def _mostrar_erro(master: ctk.CTk, titulo: str, mensagem: str) -> None:
    dlg = ctk.CTkToplevel(master)
    dlg.title(titulo)
    dlg.configure(fg_color=t.COR_FUNDO)
    dlg.geometry("400x160")
    dlg.transient(master)
    dlg.grab_set()
    ctk.CTkLabel(
        dlg,
        text=mensagem,
        font=t.FONT_PEQUENA,
        text_color=t.COR_TEXTO,
        wraplength=360,
        justify="left",
    ).pack(fill="both", expand=True, padx=20, pady=(20, 8))
    ctk.CTkButton(dlg, text="OK", width=80, command=dlg.destroy).pack(pady=(0, 16))


def abrir_dialogo_sobre(master: ctk.CTk) -> None:
    """Abre ou foca o diálogo Sobre."""
    global _dialogo_aberto
    if _dialogo_aberto is not None and _dialogo_aberto.winfo_exists():
        _dialogo_aberto.lift()
        _dialogo_aberto.focus_force()
        return
    try:
        _dialogo_aberto = DialogoSobre(master)
    except FileNotFoundError:
        _mostrar_erro(master, "Sobre", f"Arquivo {ARQUIVO_SOBRE} não encontrado.")
    except (json.JSONDecodeError, OSError) as exc:
        _mostrar_erro(master, "Sobre", f"Não foi possível ler {ARQUIVO_SOBRE}:\n{exc}")
