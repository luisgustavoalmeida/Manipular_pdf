# -*- coding: utf-8 -*-
"""Widgets reutilizáveis da interface gráfica."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk

from interface_grafica import tema as t
from configuracoes import (
    limitar_threads_traducao,
    nucleos_disponiveis,
    threads_sugeridas_traducao,
)
from seletor_arquivos import (
    salvar_arquivo_pdf,
    selecionar_arquivo_convertivel,
    selecionar_arquivos_convertiveis,
    selecionar_arquivo_pdf,
    selecionar_arquivos_pdf,
    selecionar_pasta,
)


class RotuloSecao(ctk.CTkLabel):
    """Título de seção dentro de um painel."""

    def __init__(self, master, texto: str, **kwargs):
        super().__init__(
            master,
            text=texto,
            font=t.FONT_SUBTITULO,
            text_color=t.COR_TEXTO,
            anchor="w",
            **kwargs,
        )


class RotuloDescricao(ctk.CTkLabel):
    """Texto explicativo secundário."""

    def __init__(self, master, texto: str, **kwargs):
        super().__init__(
            master,
            text=texto,
            font=t.FONT_PEQUENA,
            text_color=t.COR_TEXTO_SECUNDARIO,
            anchor="w",
            justify="left",
            wraplength=560,
            **kwargs,
        )


class CampoCaminho(ctk.CTkFrame):
    """Campo de texto + botão para selecionar arquivo ou pasta."""

    def __init__(
        self,
        master,
        rotulo: str,
        modo: str = "arquivo_pdf",
        placeholder: str = "Nenhum arquivo selecionado",
        ao_selecionar: Callable[[str], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.modo = modo
        self._placeholder = placeholder
        self._ao_selecionar = ao_selecionar
        self._pasta_base: Path | None = None
        self._nome_sugerido: str = "documento.pdf"

        ctk.CTkLabel(self, text=rotulo, font=t.FONT_CORPO, anchor="w").pack(fill="x", pady=(0, 4))

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x")
        linha.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            linha,
            placeholder_text=placeholder,
            font=t.FONT_CORPO,
            height=36,
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            linha,
            text="Procurar…",
            width=100,
            height=36,
            font=t.FONT_CORPO,
            fg_color=t.COR_PRIMARIA,
            hover_color=t.COR_PRIMARIA_HOVER,
            command=self._selecionar,
        ).grid(row=0, column=1)

    def valor(self) -> str:
        return self.entry.get().strip()

    def valor_efetivo(self) -> str:
        """Retorna o caminho informado ou a sugestão padrão (pasta origem + nome)."""
        valor = self.valor()
        if valor:
            return valor
        if self.modo == "salvar_pdf" and self._pasta_base is not None:
            return str(self._pasta_base / self._nome_sugerido)
        if self.modo == "pasta" and self._pasta_base is not None:
            return str(self._pasta_base)
        return ""

    def definir(self, caminho: str, notificar: bool = True) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, caminho)
        if notificar and self._ao_selecionar and caminho:
            self._ao_selecionar(caminho)

    def definir_sugestao_saida(self, pasta: Path | str, nome_arquivo: str, preencher: bool = True) -> None:
        """Define pasta e nome sugeridos para salvar PDF."""
        self._pasta_base = Path(pasta)
        self._nome_sugerido = (
            nome_arquivo if nome_arquivo.lower().endswith(".pdf") else f"{nome_arquivo}.pdf"
        )
        if preencher and self.modo == "salvar_pdf":
            self.definir(str(self._pasta_base / self._nome_sugerido), notificar=False)

    def definir_pasta_origem(self, caminho_origem: str) -> None:
        """Preenche com a pasta de origem (arquivo → pasta pai; pasta → ela mesma)."""
        if self.modo == "pasta" and caminho_origem:
            p = Path(caminho_origem).resolve()
            pasta = p if p.is_dir() else p.parent
            self._pasta_base = pasta
            self.definir(str(pasta), notificar=False)

    def limpar(self) -> None:
        self.entry.delete(0, "end")
        self._pasta_base = None
        self._nome_sugerido = "documento.pdf"

    def _selecionar(self) -> None:
        valor_atual = self.valor()
        if self.modo == "arquivo_pdf":
            caminho = selecionar_arquivo_pdf(
                "Selecione um PDF",
                valor_atual or (str(self._pasta_base) if self._pasta_base else None),
            )
        elif self.modo == "pasta":
            caminho = selecionar_pasta(
                "Selecione uma pasta",
                valor_atual or (str(self._pasta_base) if self._pasta_base else None),
            )
        elif self.modo == "arquivo_convertivel":
            caminho = selecionar_arquivo_convertivel("Selecione o arquivo", valor_atual or None)
        elif self.modo == "salvar_pdf":
            pasta = self._pasta_base
            if valor_atual:
                p = Path(valor_atual)
                pasta = p.parent
                nome = p.name
            else:
                nome = self._nome_sugerido
            caminho = salvar_arquivo_pdf("Salvar PDF como", nome, pasta)
        else:
            caminho = None

        if caminho:
            self.definir(caminho)
            if self.modo == "salvar_pdf":
                p = Path(caminho)
                self._pasta_base = p.parent
                self._nome_sugerido = p.name


class ListaArquivos(ctk.CTkFrame):
    """Lista de arquivos com adicionar/remover."""

    def __init__(
        self,
        master,
        rotulo: str,
        modo: str = "pdf_multi",
        ao_alterar: Callable[[list[str]], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.modo = modo
        self._ao_alterar = ao_alterar
        self._itens: list[str] = []

        ctk.CTkLabel(self, text=rotulo, font=t.FONT_CORPO, anchor="w").pack(fill="x", pady=(0, 4))

        self.listbox_frame = ctk.CTkScrollableFrame(self, height=120, fg_color=t.COR_FUNDO_CARD)
        self.listbox_frame.pack(fill="x", pady=(0, 8))

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.pack(fill="x")

        ctk.CTkButton(
            botoes,
            text="+ Adicionar",
            width=110,
            height=32,
            font=t.FONT_PEQUENA,
            fg_color=t.COR_PRIMARIA,
            hover_color=t.COR_PRIMARIA_HOVER,
            command=self._adicionar,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            botoes,
            text="− Remover",
            width=110,
            height=32,
            font=t.FONT_PEQUENA,
            fg_color=t.COR_FUNDO_CARD,
            hover_color=t.COR_BORDA,
            command=self._remover,
        ).pack(side="left")

        self._labels: list[ctk.CTkLabel] = []

    def valores(self) -> list[str]:
        return self._itens.copy()

    def limpar(self) -> None:
        self._itens.clear()
        self._atualizar_lista()
        self._notificar()

    def _notificar(self) -> None:
        if self._ao_alterar:
            self._ao_alterar(self._itens.copy())

    def _atualizar_lista(self) -> None:
        for lbl in self._labels:
            lbl.destroy()
        self._labels.clear()

        if not self._itens:
            lbl = ctk.CTkLabel(
                self.listbox_frame,
                text="Nenhum arquivo selecionado",
                font=t.FONT_PEQUENA,
                text_color=t.COR_TEXTO_SECUNDARIO,
                anchor="w",
            )
            lbl.pack(fill="x", padx=8, pady=4)
            self._labels.append(lbl)
            return

        for i, caminho in enumerate(self._itens, 1):
            nome = Path(caminho).name
            lbl = ctk.CTkLabel(
                self.listbox_frame,
                text=f"{i}. {nome}",
                font=t.FONT_PEQUENA,
                text_color=t.COR_TEXTO,
                anchor="w",
            )
            lbl.pack(fill="x", padx=8, pady=2)
            self._labels.append(lbl)

    def _adicionar(self) -> None:
        diretorio = self._itens[-1] if self._itens else None
        if self.modo == "pdf_multi":
            novos = selecionar_arquivos_pdf("Selecione PDF(s)", diretorio)
        elif self.modo == "convertivel_multi":
            novos = selecionar_arquivos_convertiveis("Selecione arquivo(s)", diretorio)
        else:
            novos = []

        for caminho in novos:
            resolvido = str(Path(caminho).resolve())
            if resolvido not in self._itens:
                self._itens.append(resolvido)
        self._atualizar_lista()
        self._notificar()

    def _remover(self) -> None:
        if self._itens:
            self._itens.pop()
            self._atualizar_lista()
            self._notificar()


class BarraStatus(ctk.CTkFrame):
    """Barra inferior com mensagem de status e progresso."""

    def __init__(self, master, **kwargs):
        super().__init__(master, height=36, fg_color=t.COR_FUNDO_SECUNDARIO, corner_radius=0, **kwargs)
        self.label = ctk.CTkLabel(
            self,
            text="Pronto",
            font=t.FONT_PEQUENA,
            text_color=t.COR_TEXTO_SECUNDARIO,
            anchor="w",
        )
        self.label.pack(side="left", fill="x", expand=True, padx=t.PADDING, pady=8)

        self.progress = ctk.CTkProgressBar(self, width=200, height=12, mode="determinate")
        self.progress.pack(side="right", padx=t.PADDING, pady=8)
        self.progress.pack_forget()

    def definir(self, texto: str, tipo: str = "info") -> None:
        cores = {
            "info": t.COR_TEXTO_SECUNDARIO,
            "ok": t.COR_SUCESSO,
            "aviso": t.COR_AVISO,
            "erro": t.COR_ERRO,
        }
        self.label.configure(text=texto, text_color=cores.get(tipo, t.COR_TEXTO_SECUNDARIO))

    def iniciar_progresso(self) -> None:
        self.progress.set(0)
        self.progress.pack(side="right", padx=t.PADDING, pady=8)

    def atualizar_progresso(self, fracao: float, texto: str = "") -> None:
        self.progress.set(max(0.0, min(1.0, fracao)))
        if texto:
            self.definir(texto)

    def parar_progresso(self) -> None:
        self.progress.set(0)
        self.progress.pack_forget()


class PainelResultado(ctk.CTkFrame):
    """Exibe resultado de uma operação concluída."""

    _GRID_ROW = 2

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=t.COR_FUNDO_CARD, corner_radius=t.RAIO_BORDA, **kwargs)

        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", padx=12, pady=(12, 4))
        cabecalho.grid_columnconfigure(0, weight=1)

        self.titulo_lbl = ctk.CTkLabel(cabecalho, text="", font=t.FONT_SUBTITULO, anchor="w")
        self.titulo_lbl.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            cabecalho,
            text="✕",
            width=28,
            height=28,
            font=t.FONT_PEQUENA,
            fg_color="transparent",
            hover_color=t.COR_BORDA,
            text_color=t.COR_TEXTO_SECUNDARIO,
            command=self.ocultar,
        ).grid(row=0, column=1, sticky="e")

        self.msg_lbl = ctk.CTkLabel(
            self,
            text="",
            font=t.FONT_PEQUENA,
            text_color=t.COR_TEXTO_SECUNDARIO,
            anchor="w",
            justify="left",
            wraplength=520,
        )
        self.msg_lbl.pack(fill="x", padx=12, pady=(0, 8))

        self.arquivos_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.arquivos_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.linha_botoes = ctk.CTkFrame(self, fg_color="transparent")
        self.linha_botoes.pack(fill="x", padx=12, pady=(0, 12))

        self.btn_abrir = ctk.CTkButton(
            self.linha_botoes,
            text="Abrir pasta no Explorador",
            height=32,
            font=t.FONT_PEQUENA,
            fg_color=t.COR_PRIMARIA,
            hover_color=t.COR_PRIMARIA_HOVER,
            command=self._abrir_pasta,
        )
        self.btn_fechar = ctk.CTkButton(
            self.linha_botoes,
            text="Fechar",
            width=100,
            height=32,
            font=t.FONT_PEQUENA,
            fg_color=t.COR_FUNDO_SECUNDARIO,
            hover_color=t.COR_BORDA,
            command=self.ocultar,
        )
        self._pasta: Path | None = None

    def _atualizar_botoes(self, mostrar_abrir: bool) -> None:
        self.btn_abrir.pack_forget()
        self.btn_fechar.pack_forget()
        if mostrar_abrir:
            self.btn_abrir.pack(side="left", padx=(0, 8))
        self.btn_fechar.pack(side="left")

    def mostrar(self, titulo: str, pasta: Path, arquivos: list[str], mensagem: str = "") -> None:
        self._pasta = pasta
        self.titulo_lbl.configure(text=f"✓ {titulo}", text_color=t.COR_SUCESSO)
        self.msg_lbl.configure(text=mensagem or f"Pasta: {pasta}")

        for w in self.arquivos_frame.winfo_children():
            w.destroy()

        for arq in arquivos[:8]:
            ctk.CTkLabel(
                self.arquivos_frame,
                text=f"• {Path(arq).name}",
                font=t.FONT_PEQUENA,
                anchor="w",
            ).pack(fill="x")
        if len(arquivos) > 8:
            ctk.CTkLabel(
                self.arquivos_frame,
                text=f"… e mais {len(arquivos) - 8} arquivo(s)",
                font=t.FONT_PEQUENA,
                text_color=t.COR_TEXTO_SECUNDARIO,
                anchor="w",
            ).pack(fill="x")

        self._atualizar_botoes(mostrar_abrir=bool(arquivos and self._pasta))
        self._exibir()

    def mostrar_erro(self, titulo: str, mensagem: str) -> None:
        self._pasta = None
        self.titulo_lbl.configure(text=f"✗ {titulo}", text_color=t.COR_ERRO)
        self.msg_lbl.configure(text=mensagem)
        for w in self.arquivos_frame.winfo_children():
            w.destroy()
        self._atualizar_botoes(mostrar_abrir=False)
        self._exibir()

    def ocultar(self) -> None:
        self.grid_remove()

    def _exibir(self) -> None:
        self.grid(row=self._GRID_ROW, column=0, sticky="ew", pady=(12, 0))

    def _abrir_pasta(self) -> None:
        if self._pasta:
            from seletor_arquivos import abrir_pasta_explorador

            try:
                abrir_pasta_explorador(self._pasta)
            except Exception:
                pass


class SeletorThreadsTraducao(ctk.CTkFrame):
    """Controle para escolher quantas threads usar na tradução paralela."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._nucleos = nucleos_disponiveis()
        self._sugestao = threads_sugeridas_traducao()

        ctk.CTkLabel(
            self,
            text="Threads de tradução em paralelo",
            font=t.FONT_CORPO,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        RotuloDescricao(
            self,
            f"Seu computador tem {self._nucleos} núcleo(s) lógico(s). "
            f"Recomendado: {self._sugestao} thread(s). "
            "Mais threads aceleram a tradução, mas valores muito altos podem "
            "atingir o limite do Google Translate.",
        ).pack(fill="x", pady=(0, 8))

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x")
        linha.grid_columnconfigure(1, weight=1)

        self.label_valor = ctk.CTkLabel(
            linha,
            text=f"{self._sugestao}",
            font=t.FONT_SUBTITULO,
            width=36,
        )
        self.label_valor.grid(row=0, column=0, padx=(0, 12))

        passos = max(1, self._nucleos - 1)
        self.slider = ctk.CTkSlider(
            linha,
            from_=1,
            to=self._nucleos,
            number_of_steps=passos,
            command=self._ao_mover_slider,
        )
        self.slider.set(self._sugestao)
        self.slider.grid(row=0, column=1, sticky="ew")

        self.label_faixa = ctk.CTkLabel(
            linha,
            text=f"1 – {self._nucleos}",
            font=t.FONT_PEQUENA,
            text_color=t.COR_TEXTO_SECUNDARIO,
            width=48,
        )
        self.label_faixa.grid(row=0, column=2, padx=(12, 0))

    def _ao_mover_slider(self, valor: float) -> None:
        threads = limitar_threads_traducao(round(valor))
        self.label_valor.configure(text=str(threads))

    def valor(self) -> int:
        return limitar_threads_traducao(round(self.slider.get()))

    def limpar(self) -> None:
        self.slider.set(self._sugestao)
        self.label_valor.configure(text=str(self._sugestao))


def criar_botoes_acao(
    master,
    executar: Callable,
    limpar: Callable,
) -> ctk.CTkFrame:
    """Linha com botões Executar e Limpar."""
    frame = ctk.CTkFrame(master, fg_color="transparent")
    frame.pack(fill="x", pady=(16, 0))

    ctk.CTkButton(
        frame,
        text="Executar",
        width=140,
        height=40,
        font=t.FONT_BOTAO,
        fg_color=t.COR_PRIMARIA,
        hover_color=t.COR_PRIMARIA_HOVER,
        command=executar,
    ).pack(side="left", padx=(0, 8))

    ctk.CTkButton(
        frame,
        text="Limpar",
        width=100,
        height=40,
        font=t.FONT_CORPO,
        fg_color=t.COR_FUNDO_CARD,
        hover_color=t.COR_BORDA,
        command=limpar,
    ).pack(side="left")

    return frame
