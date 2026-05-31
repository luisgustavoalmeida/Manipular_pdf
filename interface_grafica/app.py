# -*- coding: utf-8 -*-
"""Janela principal da interface gráfica."""

from __future__ import annotations

import customtkinter as ctk

from constantes import TITULO_APLICACAO, texto_versao, titulo_com_versao
from interface_grafica import tema as t
from interface_grafica.componentes import BarraStatus, PainelResultado
from interface_grafica.sobre import abrir_dialogo_sobre
from interface_grafica.operacao_ativa import GerenciadorOperacoes
from interface_grafica.paineis import CATEGORIAS, OPERACOES, PainelOperacao
from operacoes import ResultadoOperacao
from progresso import ControleCancelamento, formatar_duracao


class AplicacaoPDF(ctk.CTk):
    """Aplicação principal com barra lateral e área de conteúdo."""

    def __init__(self):
        super().__init__()
        self.title(titulo_com_versao())
        self.geometry(f"{t.LARGURA_JANELA}x{t.ALTURA_JANELA}")
        self.minsize(800, 560)

        t.inicializar_tema()
        self.configure(fg_color=t.COR_FUNDO)

        self._sidebar: ctk.CTkFrame | None = None
        self._paineis: dict[str, PainelOperacao] = {}
        self._lbl_categorias: list[ctk.CTkLabel] = []
        self._lbl_titulo_app: ctk.CTkLabel | None = None
        self._lbl_versao_app: ctk.CTkLabel | None = None
        self._separador_sidebar: ctk.CTkFrame | None = None
        self._btn_tema: ctk.CTkButton | None = None
        self._btn_sobre: ctk.CTkButton | None = None
        self._op_visivel: str | None = None
        self._botoes_nav: dict[str, ctk.CTkButton] = {}
        self._classes_painel = {op_id: cls for op_id, _, _, cls in OPERACOES}
        self._titulos_op = {op_id: titulo for op_id, titulo, _, _ in OPERACOES}
        self._operacoes = GerenciadorOperacoes(titulos=self._titulos_op)
        self._montar_layout()

    def _montar_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._montar_sidebar()
        self._montar_area_conteudo()
        self._montar_status()

        self._selecionar_operacao(OPERACOES[0][0])

    def _montar_sidebar(self) -> None:
        self._sidebar = ctk.CTkFrame(
            self,
            width=t.LARGURA_SIDEBAR,
            fg_color=t.COR_FUNDO_SECUNDARIO,
            corner_radius=0,
        )
        sidebar = self._sidebar
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        sidebar.grid_propagate(False)

        header = ctk.CTkFrame(sidebar, fg_color="transparent")
        header.pack(fill="x", padx=t.PADDING, pady=(t.PADDING, 2))

        ctk.CTkLabel(header, text="📑", font=("Segoe UI", 28)).pack(anchor="w")
        self._lbl_titulo_app = ctk.CTkLabel(
            header,
            text=TITULO_APLICACAO,
            font=t.FONT_TITULO,
            text_color=t.COR_TEXTO,
            anchor="w",
        )
        self._lbl_titulo_app.pack(anchor="w")
        self._lbl_versao_app = ctk.CTkLabel(
            header,
            text=texto_versao(),
            font=t.FONT_PEQUENA,
            text_color=t.COR_TEXTO_SECUNDARIO,
            anchor="w",
        )
        self._lbl_versao_app.pack(anchor="w")

        barra_header = ctk.CTkFrame(header, fg_color="transparent")
        barra_header.pack(anchor="w", pady=(2, 0))

        self._btn_tema = ctk.CTkButton(
            barra_header,
            text=self._icone_tema(),
            width=28,
            height=24,
            font=("Segoe UI", 12),
            fg_color="transparent",
            text_color=t.COR_TEXTO_SECUNDARIO,
            hover_color=t.COR_FUNDO_CARD,
            corner_radius=6,
            command=self._alternar_tema_clique,
        )
        self._btn_tema.pack(side="left")

        self._btn_sobre = ctk.CTkButton(
            barra_header,
            text="ⓘ",
            width=28,
            height=24,
            font=("Segoe UI", 12),
            fg_color="transparent",
            text_color=t.COR_TEXTO_SECUNDARIO,
            hover_color=t.COR_FUNDO_CARD,
            corner_radius=6,
            command=self._abrir_sobre,
        )
        self._btn_sobre.pack(side="left", padx=(4, 0))

        self._separador_sidebar = ctk.CTkFrame(sidebar, height=1, fg_color=t.COR_BORDA)
        self._separador_sidebar.pack(fill="x", padx=t.PADDING, pady=(4, 2))

        scroll = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._scroll_sidebar = scroll

        ops_por_categoria: dict[str, list] = {}
        for op_id, titulo, cat_id, _ in OPERACOES:
            ops_por_categoria.setdefault(cat_id, []).append((op_id, titulo))

        for indice, (cat_id, cat_titulo, cat_icone) in enumerate(CATEGORIAS):
            lbl_cat = ctk.CTkLabel(
                scroll,
                text=f"{cat_icone}  {cat_titulo}",
                font=t.FONT_PEQUENA,
                text_color=t.COR_TEXTO_SECUNDARIO,
                anchor="w",
            )
            lbl_cat.pack(fill="x", padx=8, pady=(4 if indice == 0 else 10, 4))
            self._lbl_categorias.append(lbl_cat)

            for op_id, titulo in ops_por_categoria.get(cat_id, []):
                btn = ctk.CTkButton(
                    scroll,
                    text=titulo,
                    anchor="w",
                    height=34,
                    font=t.FONT_PEQUENA,
                    fg_color="transparent",
                    text_color=t.COR_TEXTO,
                    hover_color=t.COR_FUNDO_CARD,
                    command=lambda oid=op_id: self._selecionar_operacao(oid),
                )
                btn.pack(fill="x", padx=4, pady=1)
                self._botoes_nav[op_id] = btn

    def _montar_area_conteudo(self) -> None:
        self.area = ctk.CTkFrame(self, fg_color=t.COR_FUNDO, corner_radius=0)
        self.area.grid(row=0, column=1, sticky="nsew")
        self.area.grid_columnconfigure(0, weight=1)
        self.area.grid_rowconfigure(0, weight=1)
        self.area.grid_rowconfigure(1, weight=0)

        self.container = ctk.CTkFrame(self.area, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="nsew", padx=t.PADDING, pady=t.PADDING)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=0)
        self.container.grid_rowconfigure(1, weight=1)
        self.container.grid_rowconfigure(2, weight=0)

        self._montar_banner_execucao()

        self.viewport = ctk.CTkScrollableFrame(
            self.container,
            fg_color="transparent",
            scrollbar_button_color=t.COR_BORDA,
            scrollbar_button_hover_color=t.COR_PRIMARIA,
        )
        self.viewport.grid(row=1, column=0, sticky="nsew")

        self.painel_resultado = PainelResultado(self.container)
        self.painel_resultado.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        self.painel_resultado.grid_remove()

        self.status = BarraStatus(self)

    def _montar_banner_execucao(self) -> None:
        self.banner_exec = ctk.CTkFrame(
            self.container,
            fg_color=t.COR_FUNDO_CARD,
            corner_radius=t.RAIO_BORDA,
        )
        self.banner_exec.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.banner_exec.grid_columnconfigure(0, weight=1)
        self.banner_exec.grid_remove()

        self.lbl_banner_exec = ctk.CTkLabel(
            self.banner_exec,
            text="",
            font=t.FONT_PEQUENA,
            text_color=t.COR_TEXTO,
            anchor="w",
        )
        self.lbl_banner_exec.grid(row=0, column=0, sticky="ew", padx=12, pady=10)

        self.btn_banner_cancelar = ctk.CTkButton(
            self.banner_exec,
            text="Cancelar",
            width=90,
            height=28,
            font=t.FONT_PEQUENA,
            fg_color=t.COR_ERRO,
            hover_color=t.COR_ERRO_HOVER,
            command=self._cancelar_operacao_ativa,
        )
        self.btn_banner_cancelar.grid(row=0, column=1, padx=(0, 8), pady=10)

        self.btn_banner_exec = ctk.CTkButton(
            self.banner_exec,
            text="Ver operação",
            width=120,
            height=28,
            font=t.FONT_PEQUENA,
            command=self._ir_para_operacao_ativa,
        )
        self.btn_banner_exec.grid(row=0, column=2, padx=(0, 12), pady=10)

    def _montar_status(self) -> None:
        self.status.grid(row=1, column=1, sticky="ew")

    def _ocultar_painel_visivel(self) -> None:
        if self._op_visivel and self._op_visivel in self._paineis:
            self._paineis[self._op_visivel].pack_forget()
        self.painel_resultado.ocultar()

    def _rolar_para_topo(self) -> None:
        try:
            self.viewport._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def _texto_status_progresso(
        self,
        mensagem: str,
        atual: int,
        total: int,
        decorrido: float,
        restante: float | None,
    ) -> str:
        if mensagem and total > 1:
            etapa = f"{mensagem} ({atual}/{total})"
        elif mensagem:
            etapa = mensagem
        else:
            etapa = "Processando…"
        decorrido_txt = formatar_duracao(decorrido)
        if restante is None:
            restante_txt = "—"
        elif restante <= 0:
            restante_txt = "0s"
        else:
            restante_txt = f"~{formatar_duracao(restante)}"
        return f"{etapa}  |  Decorrido: {decorrido_txt}  ·  Restante: {restante_txt}"

    def _atualizar_nav(self, op_id: str) -> None:
        executando_id = self._operacoes.op_id
        for oid, btn in self._botoes_nav.items():
            titulo = self._titulos_op[oid]
            if oid == executando_id and oid != op_id:
                btn.configure(
                    fg_color="transparent",
                    text_color=t.COR_AVISO,
                    text=f"⏳ {titulo}",
                )
            elif oid == op_id:
                btn.configure(
                    fg_color=t.COR_PRIMARIA,
                    text_color=t.COR_TEXTO_BOTAO_ATIVO,
                    text=titulo,
                )
            else:
                btn.configure(fg_color="transparent", text_color=t.COR_TEXTO, text=titulo)

    def _atualizar_banner_execucao(self) -> None:
        op = self._operacoes.ativa
        if op is None:
            self.banner_exec.grid_remove()
            return

        pct = int(op.fracao * 100)
        if self._op_visivel == op.op_id:
            self.banner_exec.grid_remove()
            return

        self.lbl_banner_exec.configure(
            text=f"⏳ {op.titulo} em execução — {pct}% — {op.mensagem}"
        )
        self.banner_exec.grid()

    def _ir_para_operacao_ativa(self) -> None:
        op_id = self._operacoes.op_id
        if op_id:
            self._selecionar_operacao(op_id)

    def solicitar_cancelamento_operacao(self, op_id: str) -> bool:
        if not self._operacoes.esta_executando(op_id):
            return False
        if not self._operacoes.solicitar_cancelamento():
            return False
        op = self._operacoes.ativa
        if op and op.painel.winfo_exists():
            op.painel.btn_cancelar.configure(state="disabled", text="Cancelando…")
        self.btn_banner_cancelar.configure(state="disabled", text="Cancelando…")
        self.status.definir("Cancelando operação…", "aviso")
        return True

    def _cancelar_operacao_ativa(self) -> None:
        op_id = self._operacoes.op_id
        if op_id:
            self.solicitar_cancelamento_operacao(op_id)

    def operacao_em_outro_painel(self, op_id: str) -> bool:
        return self._operacoes.esta_executando() and not self._operacoes.esta_executando(op_id)

    def titulo_operacao_ativa(self) -> str:
        op = self._operacoes.ativa
        return op.titulo if op else ""

    def registrar_operacao_iniciada(
        self,
        op_id: str,
        painel: PainelOperacao,
        controle: ControleCancelamento,
    ) -> None:
        self._operacoes.iniciar(op_id, painel, controle)
        self.btn_banner_cancelar.configure(state="normal", text="Cancelar")
        self.status.definir("Iniciando…")
        self.status.iniciar_progresso()
        self._atualizar_nav(self._op_visivel or op_id)
        self._atualizar_banner_execucao()

    def atualizar_progresso_operacao(
        self,
        op_id: str,
        fracao: float,
        mensagem: str,
        atual: int,
        total: int,
        decorrido: float,
        restante: float | None,
    ) -> None:
        self._operacoes.atualizar_progresso(
            op_id, fracao, mensagem, atual, total, decorrido, restante
        )
        if not self._operacoes.esta_executando(op_id):
            return

        status_txt = self._texto_status_progresso(mensagem, atual, total, decorrido, restante)
        self.after(0, lambda: self._aplicar_progresso_global(op_id, fracao, status_txt))

    def _aplicar_progresso_global(self, op_id: str, fracao: float, status_txt: str) -> None:
        if not self._operacoes.esta_executando(op_id):
            return
        self.status.atualizar_progresso(fracao, status_txt)
        self._atualizar_banner_execucao()
        self._atualizar_nav(self._op_visivel or op_id)

    def registrar_operacao_finalizada(self, op_id: str, resultado: ResultadoOperacao) -> None:
        concluida = self._operacoes.finalizar(op_id)
        if concluida is None:
            return

        painel = concluida.painel
        visivel = self._op_visivel == op_id

        if painel.winfo_exists():
            painel._ocultar_progresso()
            painel._executando = False
            painel._controle_cancelamento = None

        self.btn_banner_cancelar.configure(state="normal", text="Cancelar")
        self.status.parar_progresso()
        self._atualizar_banner_execucao()
        self._atualizar_nav(self._op_visivel or op_id)

        if resultado.cancelado:
            msg = resultado.mensagem or "Operação cancelada pelo usuário."
            if visivel and painel.winfo_exists():
                painel._mostrar_resultado(resultado)
            else:
                self.status.definir(msg, "aviso")
            return

        if visivel and painel.winfo_exists():
            painel._mostrar_resultado(resultado)
        elif resultado.sucesso:
            self.status.definir(
                f"✓ {concluida.titulo}: {resultado.mensagem or 'Concluído'} — clique em "
                f"«{concluida.titulo}» para ver detalhes",
                "ok",
            )
        else:
            self.status.definir(
                f"✗ {concluida.titulo}: {resultado.detalhes or 'Erro'} — clique em "
                f"«{concluida.titulo}» para detalhes",
                "erro",
            )

        if not visivel and painel.winfo_exists() and resultado.sucesso:
            painel.painel_resultado.mostrar(
                resultado.titulo,
                resultado.pasta,
                resultado.arquivos,
                resultado.mensagem,
            )

    def _selecionar_operacao(self, op_id: str) -> None:
        if op_id == self._op_visivel and op_id in self._paineis:
            return

        self._ocultar_painel_visivel()
        self._op_visivel = op_id
        self._atualizar_nav(op_id)

        if op_id not in self._paineis:
            cls = self._classes_painel[op_id]
            self._paineis[op_id] = cls(
                self.viewport,
                status=self.status,
                resultado=self.painel_resultado,
                app=self,
                op_id=op_id,
            )

        painel = self._paineis[op_id]
        painel.pack(fill="x", anchor="nw")
        self.update_idletasks()
        self._rolar_para_topo()
        self._atualizar_banner_execucao()

        if self._operacoes.esta_executando(op_id):
            op = self._operacoes.ativa
            assert op is not None
            status_txt = self._texto_status_progresso(
                op.mensagem, op.atual, op.total, op.decorrido, op.restante
            )
            self.status.iniciar_progresso()
            self.status.atualizar_progresso(op.fracao, status_txt)
        elif not self._operacoes.esta_executando():
            self.status.definir("Pronto")

    def _abrir_sobre(self) -> None:
        abrir_dialogo_sobre(self)

    @staticmethod
    def _icone_tema() -> str:
        """Ícone do modo para o qual o clique alterna (☀ claro / 🌙 escuro)."""
        return "☀" if t.MODO_ATUAL == "dark" else "🌙"

    def _alternar_tema_clique(self) -> None:
        self._aplicar_modo_tema("light" if t.MODO_ATUAL == "dark" else "dark")

    def _aplicar_modo_tema(self, modo: t.ModoAparencia) -> None:
        if modo == t.MODO_ATUAL:
            return
        t.aplicar_tema(modo)
        self._pos_tema_alterado()

    def _atualizar_botao_tema(self) -> None:
        if self._btn_tema:
            self._btn_tema.configure(text=self._icone_tema())

    def _pos_tema_alterado(self) -> None:
        """Reaplica estados visuais após troca de tema."""
        t.forcar_redesenho_tema(self)

        if self._op_visivel:
            self._atualizar_nav(self._op_visivel)

        self._atualizar_botao_tema()
        self.update_idletasks()


def iniciar_aplicacao() -> None:
    """Inicia a interface gráfica."""
    app = AplicacaoPDF()
    app.mainloop()
