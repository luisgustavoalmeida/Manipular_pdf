# -*- coding: utf-8 -*-
"""Painéis de operação da interface gráfica."""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import customtkinter as ctk

from constantes import IDIOMAS_DISPONIVEIS
from converter_para_pdf import formatos_suportados_texto, libreoffice_disponivel
from editar_pdf import interpretar_paginas, obter_total_paginas
from interface_grafica import tema as t
from interface_grafica.componentes import (
    BarraStatus,
    CampoCaminho,
    ListaArquivos,
    PainelResultado,
    RotuloDescricao,
    RotuloSecao,
    SeletorThreadsTraducao,
    criar_botoes_acao,
)
from nomes_saida import (
    sugestao_comprimir,
    sugestao_converter,
    sugestao_extrair,
    sugestao_juntar,
    sugestao_rotacionar,
)
from operacoes import (
    ResultadoOperacao,
    operacao_comprimir,
    operacao_converter_arquivos,
    operacao_converter_pasta,
    operacao_dividir_em_partes,
    operacao_dividir_por_paginas,
    operacao_extrair_paginas,
    operacao_juntar,
    operacao_rotacionar,
    operacao_traduzir,
    operacao_traduzir_2colunas,
    resolver_idiomas_por_indices,
)
from progresso import (
    ControleCancelamento,
    OperacaoCancelada,
    ProgressoInterface,
    RelatorioProgresso,
    formatar_duracao,
)

if TYPE_CHECKING:
    from interface_grafica.app import AplicacaoPDF


class PainelOperacao(ABC, ctk.CTkFrame):
    """Base para painéis de operação PDF."""

    titulo: str = ""
    descricao: str = ""

    def __init__(
        self,
        master,
        status: BarraStatus,
        resultado: PainelResultado,
        app: AplicacaoPDF | None = None,
        op_id: str = "",
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.status = status
        self.painel_resultado = resultado
        self._app = app
        self._op_id = op_id
        self._executando = False
        self._controle_cancelamento: ControleCancelamento | None = None
        self._montar_cabecalho()
        self._montar_barra_progresso()
        self.montar_conteudo()
        criar_botoes_acao(self, self._executar_com_thread, self.limpar)

    def _montar_barra_progresso(self) -> None:
        self.frame_progresso = ctk.CTkFrame(
            self,
            fg_color=t.COR_FUNDO_CARD,
            corner_radius=t.RAIO_BORDA,
        )
        self.lbl_progresso_etapa = ctk.CTkLabel(
            self.frame_progresso,
            text="Processando…",
            font=t.FONT_PEQUENA,
            text_color=t.COR_TEXTO,
            anchor="w",
        )
        self.lbl_progresso_etapa.pack(fill="x", padx=12, pady=(10, 6))

        linha = ctk.CTkFrame(self.frame_progresso, fg_color="transparent")
        linha.pack(fill="x", padx=12, pady=(0, 10))
        linha.grid_columnconfigure(0, weight=1)

        self.barra_progresso_painel = ctk.CTkProgressBar(linha, height=14, mode="determinate")
        self.barra_progresso_painel.set(0)
        self.barra_progresso_painel.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.lbl_progresso_pct = ctk.CTkLabel(
            linha,
            text="0%",
            font=t.FONT_PEQUENA,
            text_color=t.COR_PRIMARIA,
            width=44,
        )
        self.lbl_progresso_pct.grid(row=0, column=1)

        self.lbl_progresso_tempo = ctk.CTkLabel(
            self.frame_progresso,
            text="Decorrido: 0s  ·  Restante: —",
            font=t.FONT_PEQUENA,
            text_color=t.COR_TEXTO_SECUNDARIO,
            anchor="w",
        )
        self.lbl_progresso_tempo.pack(fill="x", padx=12, pady=(0, 6))

        self.btn_cancelar = ctk.CTkButton(
            self.frame_progresso,
            text="Cancelar operação",
            width=160,
            height=32,
            font=t.FONT_PEQUENA,
            fg_color=t.COR_ERRO,
            hover_color=t.COR_ERRO_HOVER,
            command=self._solicitar_cancelamento,
        )
        self.btn_cancelar.pack(anchor="w", padx=12, pady=(0, 10))

    def _exibir_progresso(self) -> None:
        self.frame_progresso.pack(fill="x", pady=(0, 12))

    def _ocultar_progresso(self) -> None:
        self.frame_progresso.pack_forget()
        self.barra_progresso_painel.set(0)
        self.lbl_progresso_pct.configure(text="0%")
        self.lbl_progresso_tempo.configure(text="Decorrido: 0s  ·  Restante: —")

    def esta_executando(self) -> bool:
        return self._executando

    def _criar_progresso(self) -> ProgressoInterface:
        def callback(
            fracao: float,
            mensagem: str,
            atual: int,
            total: int,
            decorrido: float,
            restante: float | None,
        ) -> None:
            if self._app and self._op_id:
                self._app.atualizar_progresso_operacao(
                    self._op_id, fracao, mensagem, atual, total, decorrido, restante
                )
            if self.winfo_exists():
                self.after(
                    0,
                    lambda f=fracao, m=mensagem, a=atual, t=total, d=decorrido, r=restante: (
                        self._atualizar_progresso_ui(f, m, a, t, d, r)
                    ),
                )

        return ProgressoInterface(callback, controle=self._controle_cancelamento)

    def _texto_tempo_progresso(self, decorrido: float, restante: float | None) -> str:
        decorrido_txt = formatar_duracao(decorrido)
        if restante is None:
            restante_txt = "—"
        elif restante <= 0:
            restante_txt = "0s"
        else:
            restante_txt = f"~{formatar_duracao(restante)}"
        return f"Decorrido: {decorrido_txt}  ·  Restante: {restante_txt}"

    def _atualizar_progresso_ui(
        self,
        fracao: float,
        mensagem: str,
        atual: int,
        total: int,
        decorrido: float = 0.0,
        restante: float | None = None,
    ) -> None:
        if not self.winfo_exists():
            return
        pct = int(fracao * 100)
        self.barra_progresso_painel.set(fracao)
        self.lbl_progresso_pct.configure(text=f"{pct}%")
        if mensagem:
            if total > 1:
                self.lbl_progresso_etapa.configure(text=f"{mensagem} ({atual}/{total})")
            else:
                self.lbl_progresso_etapa.configure(text=mensagem)
        tempo_txt = self._texto_tempo_progresso(decorrido, restante)
        self.lbl_progresso_tempo.configure(text=tempo_txt)

    def cancelar_operacao(self) -> None:
        """Troca de painel não interrompe a thread em execução."""
        pass

    def _solicitar_cancelamento(self) -> None:
        if not self._executando:
            return
        if self._app and self._op_id:
            if self._app.solicitar_cancelamento_operacao(self._op_id):
                self.btn_cancelar.configure(state="disabled", text="Cancelando…")
            return
        if self._controle_cancelamento:
            self._controle_cancelamento.solicitar()
            self.btn_cancelar.configure(state="disabled", text="Cancelando…")

    def _montar_cabecalho(self) -> None:
        RotuloSecao(self, self.titulo).pack(fill="x", pady=(0, 4))
        if self.descricao:
            RotuloDescricao(self, self.descricao).pack(fill="x", pady=(0, 12))

    @abstractmethod
    def montar_conteudo(self) -> None:
        """Constrói widgets específicos da operação."""

    @abstractmethod
    def validar(self) -> str | None:
        """Retorna mensagem de erro ou None se válido."""

    @abstractmethod
    def executar_operacao(self, progresso: RelatorioProgresso | None = None) -> ResultadoOperacao:
        """Executa a operação e retorna o resultado."""

    def limpar(self) -> None:
        """Redefine campos; subclasses podem estender."""
        self.painel_resultado.ocultar()
        self._ocultar_progresso()
        self.status.definir("Pronto")

    def _executar_com_thread(self) -> None:
        if self._executando:
            return
        if (
            self._app
            and self._op_id
            and self._app.operacao_em_outro_painel(self._op_id)
        ):
            titulo = self._app.titulo_operacao_ativa()
            self.status.definir(
                f"Aguarde: «{titulo}» ainda está em execução. Use o banner ou o menu ⏳ para acompanhar.",
                "aviso",
            )
            return
        erro = self.validar()
        if erro:
            self.status.definir(erro, "erro")
            self.painel_resultado.mostrar_erro("Validação", erro)
            return

        self._executando = True
        self._controle_cancelamento = ControleCancelamento()
        self.painel_resultado.ocultar()
        self._exibir_progresso()
        self.btn_cancelar.configure(state="normal", text="Cancelar operação")
        if self._app and self._op_id:
            self._app.registrar_operacao_iniciada(
                self._op_id, self, self._controle_cancelamento
            )
        else:
            self.status.definir("Iniciando…")
            self.status.iniciar_progresso()
        progresso = self._criar_progresso()

        def tarefa():
            try:
                resultado = self.executar_operacao(progresso)
                if self.winfo_exists():
                    self.after(0, lambda: self._finalizar(resultado))
                elif self._app and self._op_id:
                    self._app.registrar_operacao_finalizada(self._op_id, resultado)
            except OperacaoCancelada:
                cancelado = ResultadoOperacao(
                    sucesso=False,
                    titulo="Operação cancelada",
                    pasta=Path("."),
                    mensagem="Operação cancelada pelo usuário.",
                    detalhes="Operação cancelada pelo usuário.",
                    cancelado=True,
                )
                if self.winfo_exists():
                    self.after(0, lambda: self._finalizar(cancelado))
                elif self._app and self._op_id:
                    self._app.registrar_operacao_finalizada(self._op_id, cancelado)
            except Exception as e:
                if self.winfo_exists():
                    self.after(0, lambda: self._finalizar_erro(str(e)))
                elif self._app and self._op_id:
                    self._app.registrar_operacao_finalizada(
                        self._op_id,
                        ResultadoOperacao(
                            sucesso=False,
                            titulo="Erro",
                            pasta=Path("."),
                            detalhes=str(e),
                        ),
                    )

        threading.Thread(target=tarefa, daemon=True).start()

    def _finalizar(self, resultado: ResultadoOperacao) -> None:
        self._executando = False
        self._controle_cancelamento = None
        if self._app and self._op_id:
            self._app.registrar_operacao_finalizada(self._op_id, resultado)
            return
        if not self.winfo_exists():
            return
        self._ocultar_progresso()
        self.status.parar_progresso()
        self._mostrar_resultado(resultado)

    def _finalizar_erro(self, mensagem: str) -> None:
        self._finalizar(
            ResultadoOperacao(
                sucesso=False,
                titulo="Erro",
                pasta=Path("."),
                detalhes=mensagem,
            )
        )

    def _mostrar_resultado(self, resultado: ResultadoOperacao) -> None:
        if resultado.cancelado:
            self.status.definir(resultado.mensagem or "Operação cancelada", "aviso")
            self.painel_resultado.mostrar_erro(
                "Operação cancelada",
                resultado.detalhes or "A operação foi interrompida pelo usuário.",
            )
        elif resultado.sucesso:
            self.status.definir(resultado.mensagem or "Concluído", "ok")
            self.painel_resultado.mostrar(
                resultado.titulo,
                resultado.pasta,
                resultado.arquivos,
                resultado.mensagem,
            )
        else:
            self.status.definir(resultado.detalhes or "Erro na operação", "erro")
            self.painel_resultado.mostrar_erro(resultado.titulo, resultado.detalhes)


class PainelDividirPaginas(PainelOperacao):
    titulo = "Dividir PDF — a cada N páginas"
    descricao = "Gera vários arquivos com um número fixo de páginas em cada um."

    def montar_conteudo(self) -> None:
        self.campo_pasta = CampoCaminho(
            self,
            "Pasta de saída",
            modo="pasta",
            placeholder="Preenchida automaticamente com a pasta do PDF",
        )
        self.campo_pdf = CampoCaminho(
            self,
            "Arquivo PDF",
            modo="arquivo_pdf",
            ao_selecionar=lambda arq: self.campo_pasta.definir_pasta_origem(arq),
        )
        self.campo_pdf.pack(fill="x", pady=(0, 12))

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(linha, text="Páginas por parte", font=t.FONT_CORPO).pack(side="left")
        self.spin_paginas = ctk.CTkEntry(linha, width=80, placeholder_text="10")
        self.spin_paginas.pack(side="left", padx=(12, 0))
        self.spin_paginas.insert(0, "10")

        self.campo_pasta.pack(fill="x")
        RotuloDescricao(
            self,
            "Arquivos gerados: nome_parte_01.pdf, nome_parte_02.pdf … na pasta de saída.",
        ).pack(fill="x", pady=(8, 0))

    def limpar(self) -> None:
        super().limpar()
        self.campo_pdf.limpar()
        self.campo_pasta.limpar()
        self.spin_paginas.delete(0, "end")
        self.spin_paginas.insert(0, "10")

    def validar(self) -> str | None:
        if not self.campo_pdf.valor():
            return "Selecione um arquivo PDF."
        try:
            n = int(self.spin_paginas.get())
            if n < 1:
                return "Informe ao menos 1 página por parte."
        except ValueError:
            return "Páginas por parte deve ser um número inteiro."
        return None

    def executar_operacao(self, progresso: RelatorioProgresso | None = None) -> ResultadoOperacao:
        pasta = self.campo_pasta.valor() or None
        return operacao_dividir_por_paginas(
            self.campo_pdf.valor(),
            int(self.spin_paginas.get()),
            pasta,
            progresso=progresso,
        )


class PainelDividirPartes(PainelOperacao):
    titulo = "Dividir PDF — em N partes iguais"
    descricao = "Divide o documento em partes com quantidade equilibrada de páginas."

    def montar_conteudo(self) -> None:
        self.campo_pasta = CampoCaminho(
            self,
            "Pasta de saída",
            modo="pasta",
            placeholder="Preenchida automaticamente com a pasta do PDF",
        )
        self.campo_pdf = CampoCaminho(
            self,
            "Arquivo PDF",
            modo="arquivo_pdf",
            ao_selecionar=lambda arq: self.campo_pasta.definir_pasta_origem(arq),
        )
        self.campo_pdf.pack(fill="x", pady=(0, 12))

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(linha, text="Número de partes", font=t.FONT_CORPO).pack(side="left")
        self.spin_partes = ctk.CTkEntry(linha, width=80, placeholder_text="2")
        self.spin_partes.pack(side="left", padx=(12, 0))
        self.spin_partes.insert(0, "2")

        self.campo_pasta.pack(fill="x")
        RotuloDescricao(
            self,
            "Arquivos gerados: nome_parte_01.pdf, nome_parte_02.pdf … na pasta de saída.",
        ).pack(fill="x", pady=(8, 0))

    def limpar(self) -> None:
        super().limpar()
        self.campo_pdf.limpar()
        self.campo_pasta.limpar()
        self.spin_partes.delete(0, "end")
        self.spin_partes.insert(0, "2")

    def validar(self) -> str | None:
        if not self.campo_pdf.valor():
            return "Selecione um arquivo PDF."
        try:
            n = int(self.spin_partes.get())
            if n < 2:
                return "Informe ao menos 2 partes."
        except ValueError:
            return "Número de partes deve ser inteiro."
        return None

    def executar_operacao(self, progresso: RelatorioProgresso | None = None) -> ResultadoOperacao:
        pasta = self.campo_pasta.valor() or None
        return operacao_dividir_em_partes(
            self.campo_pdf.valor(),
            int(self.spin_partes.get()),
            pasta,
            progresso=progresso,
        )


class PainelJuntar(PainelOperacao):
    titulo = "Juntar PDFs"
    descricao = "Concatena vários PDFs em um único arquivo, na ordem selecionada."

    def montar_conteudo(self) -> None:
        self.campo_saida = CampoCaminho(
            self,
            "Arquivo de saída",
            modo="salvar_pdf",
            placeholder="Preenchido automaticamente ao selecionar os PDFs",
        )
        self.lista = ListaArquivos(
            self,
            "Arquivos PDF (ordem = ordem no documento final)",
            modo="pdf_multi",
            ao_alterar=self._atualizar_saida_juntar,
        )
        self.lista.pack(fill="x", pady=(0, 12))
        self.campo_saida.pack(fill="x")

    def _atualizar_saida_juntar(self, arquivos: list[str]) -> None:
        if not arquivos:
            return
        pasta, nome = sugestao_juntar(arquivos)
        self.campo_saida.definir_sugestao_saida(pasta, nome)

    def limpar(self) -> None:
        super().limpar()
        self.lista.limpar()
        self.campo_saida.limpar()

    def validar(self) -> str | None:
        if len(self.lista.valores()) < 1:
            return "Adicione ao menos um PDF."
        if not self.campo_saida.valor_efetivo():
            return "Informe o arquivo de saída."
        return None

    def executar_operacao(self, progresso: RelatorioProgresso | None = None) -> ResultadoOperacao:
        return operacao_juntar(self.lista.valores(), self.campo_saida.valor_efetivo(), progresso=progresso)


class PainelTraduzir(PainelOperacao):
    titulo = "Traduzir PDF"
    descricao = "Traduz o conteúdo via Google Translate, preservando layout e imagens."

    def montar_conteudo(self) -> None:
        self.campo_pdf = CampoCaminho(self, "Arquivo PDF", modo="arquivo_pdf")
        self.campo_pdf.pack(fill="x", pady=(0, 12))

        RotuloDescricao(
            self,
            "Saída na mesma pasta do PDF: documento_google_pt.pdf (ou outro idioma).",
        ).pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(self, text="Idioma(s) de destino", font=t.FONT_CORPO, anchor="w").pack(fill="x", pady=(0, 4))
        self.modo_idioma = ctk.CTkSegmentedButton(
            self,
            values=["Um idioma", "Vários idiomas", "Todos"],
            command=self._alternar_modo_idioma,
        )
        self.modo_idioma.set("Um idioma")
        self.modo_idioma.pack(fill="x", pady=(0, 8))

        self.frame_idioma = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_idioma.pack(fill="x", pady=(0, 12))

        opcoes = [f"{nome} ({cod})" for cod, nome in IDIOMAS_DISPONIVEIS]
        self.combo_idioma = ctk.CTkComboBox(self.frame_idioma, values=opcoes, width=280)
        self.combo_idioma.set(opcoes[0])
        self.combo_idioma.pack(anchor="w")

        self.frame_multi = ctk.CTkFrame(self, fg_color="transparent")
        self.checks_idioma: list[ctk.CTkCheckBox] = []
        for cod, nome in IDIOMAS_DISPONIVEIS:
            cb = ctk.CTkCheckBox(self.frame_multi, text=f"{nome} ({cod})", font=t.FONT_PEQUENA)
            cb.pack(anchor="w", pady=1)
            self.checks_idioma.append(cb)

        self.frame_multi.pack_forget()

        ctk.CTkLabel(self, text="Idioma de origem (opcional)", font=t.FONT_CORPO, anchor="w").pack(fill="x", pady=(0, 4))
        self.combo_origem = ctk.CTkComboBox(
            self,
            values=["Detectar automaticamente"] + [f"{nome} ({cod})" for cod, nome in IDIOMAS_DISPONIVEIS],
            width=280,
        )
        self.combo_origem.set("Detectar automaticamente")
        self.combo_origem.pack(anchor="w", pady=(0, 12))

        self.seletor_threads = SeletorThreadsTraducao(self)
        self.seletor_threads.pack(fill="x")

    def _alternar_modo_idioma(self, valor: str) -> None:
        self.frame_idioma.pack_forget()
        self.frame_multi.pack_forget()
        if valor == "Um idioma":
            self.frame_idioma.pack(fill="x", pady=(0, 12))
        elif valor == "Vários idiomas":
            self.frame_multi.pack(fill="x", pady=(0, 12))

    def _obter_idiomas(self) -> list[tuple[str, str]]:
        modo = self.modo_idioma.get()
        if modo == "Todos":
            return IDIOMAS_DISPONIVEIS.copy()
        if modo == "Um idioma":
            texto = self.combo_idioma.get()
            cod = texto.split("(")[-1].rstrip(")")
            nome = next(n for c, n in IDIOMAS_DISPONIVEIS if c == cod)
            return [(cod, nome)]
        indices = [i for i, cb in enumerate(self.checks_idioma) if cb.get()]
        return resolver_idiomas_por_indices(indices)

    def _obter_origem(self) -> str | None:
        texto = self.combo_origem.get()
        if texto == "Detectar automaticamente":
            return None
        return texto.split("(")[-1].rstrip(")")

    def limpar(self) -> None:
        super().limpar()
        self.campo_pdf.limpar()
        self.modo_idioma.set("Um idioma")
        self._alternar_modo_idioma("Um idioma")
        for cb in self.checks_idioma:
            cb.deselect()
        self.combo_origem.set("Detectar automaticamente")
        self.seletor_threads.limpar()

    def validar(self) -> str | None:
        if not self.campo_pdf.valor():
            return "Selecione um arquivo PDF."
        if not self._obter_idiomas():
            return "Selecione ao menos um idioma de destino."
        return None

    def executar_operacao(self, progresso: RelatorioProgresso | None = None) -> ResultadoOperacao:
        return operacao_traduzir(
            self.campo_pdf.valor(),
            self._obter_idiomas(),
            self._obter_origem(),
            numero_workers=self.seletor_threads.valor(),
            progresso=progresso,
        )


class PainelTraduzir2Colunas(PainelOperacao):
    titulo = "Traduzir PDF — 2 colunas"
    descricao = "Gera PDF com original à esquerda e tradução à direita."

    def montar_conteudo(self) -> None:
        self.campo_pdf = CampoCaminho(self, "Arquivo PDF", modo="arquivo_pdf")
        self.campo_pdf.pack(fill="x", pady=(0, 12))

        opcoes = [f"{nome} ({cod})" for cod, nome in IDIOMAS_DISPONIVEIS]
        ctk.CTkLabel(self, text="Idioma de destino", font=t.FONT_CORPO, anchor="w").pack(fill="x", pady=(0, 4))
        self.combo_destino = ctk.CTkComboBox(
            self,
            values=opcoes,
            width=280,
            command=self._atualizar_info_saida_2col,
        )
        self.combo_destino.set(opcoes[0])
        self.combo_destino.pack(anchor="w", pady=(0, 8))

        self.info_saida = RotuloDescricao(self, "")
        self.info_saida.pack(fill="x", pady=(0, 12))
        self._atualizar_info_saida_2col(self.combo_destino.get())

        ctk.CTkLabel(self, text="Idioma de origem (opcional)", font=t.FONT_CORPO, anchor="w").pack(fill="x", pady=(0, 4))
        self.combo_origem = ctk.CTkComboBox(
            self,
            values=["Detectar automaticamente"] + opcoes,
            width=280,
        )
        self.combo_origem.set("Detectar automaticamente")
        self.combo_origem.pack(anchor="w", pady=(0, 12))

        self.seletor_threads = SeletorThreadsTraducao(self)
        self.seletor_threads.pack(fill="x")

    def _atualizar_info_saida_2col(self, _valor: str = "") -> None:
        cod = self.combo_destino.get().split("(")[-1].rstrip(")")
        self.info_saida.configure(
            text=f"Saída na mesma pasta do PDF: documento_2colunas_{cod}.pdf",
        )

    def limpar(self) -> None:
        super().limpar()
        self.campo_pdf.limpar()
        self.combo_origem.set("Detectar automaticamente")
        self.seletor_threads.limpar()

    def validar(self) -> str | None:
        if not self.campo_pdf.valor():
            return "Selecione um arquivo PDF."
        return None

    def executar_operacao(self, progresso: RelatorioProgresso | None = None) -> ResultadoOperacao:
        cod = self.combo_destino.get().split("(")[-1].rstrip(")")
        origem_txt = self.combo_origem.get()
        origem = None if origem_txt == "Detectar automaticamente" else origem_txt.split("(")[-1].rstrip(")")
        return operacao_traduzir_2colunas(
            self.campo_pdf.valor(),
            cod,
            origem,
            numero_workers=self.seletor_threads.valor(),
            progresso=progresso,
        )


class PainelConverter(PainelOperacao):
    titulo = "Converter arquivos para PDF"
    descricao = formatos_suportados_texto()

    def montar_conteudo(self) -> None:
        if not libreoffice_disponivel():
            RotuloDescricao(
                self,
                "Word/Excel/PowerPoint exigem LibreOffice. Imagens, texto e HTML funcionam sem instalação extra.",
            ).pack(fill="x", pady=(0, 8))

        self.modo = ctk.CTkSegmentedButton(
            self,
            values=["Arquivos", "Pasta inteira"],
            command=self._alternar_modo,
        )
        self.modo.set("Arquivos")
        self.modo.pack(fill="x", pady=(0, 12))

        self.frame_arquivos = ctk.CTkFrame(self, fg_color="transparent")
        self.lista = ListaArquivos(
            self.frame_arquivos,
            "Arquivos (ordem = ordem no PDF)",
            modo="convertivel_multi",
            ao_alterar=self._atualizar_saida_converter,
        )
        self.lista.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(self.frame_arquivos, text="Saída dos PDFs", font=t.FONT_CORPO, anchor="w").pack(
            fill="x"
        )
        self.opcao_saida = ctk.CTkSegmentedButton(
            self.frame_arquivos,
            values=["Unir em um PDF", "PDF por arquivo"],
            command=self._alternar_opcao_saida,
        )
        self.opcao_saida.set("Unir em um PDF")
        self.opcao_saida.pack(fill="x", pady=(4, 8))
        self.campo_saida = CampoCaminho(
            self.frame_arquivos,
            "PDF de saída",
            modo="salvar_pdf",
            placeholder="Preenchido automaticamente ao selecionar os arquivos",
        )
        self.campo_pasta_saida_arq = CampoCaminho(
            self.frame_arquivos,
            "Pasta de saída",
            modo="pasta",
            placeholder="Preenchida automaticamente com a pasta do 1º arquivo",
        )
        self.campo_saida.pack(fill="x")
        self.frame_arquivos.pack(fill="x")

        self.frame_pasta = ctk.CTkFrame(self, fg_color="transparent")
        self.campo_pasta_saida = CampoCaminho(
            self.frame_pasta,
            "Pasta de saída",
            modo="pasta",
            placeholder="Preenchida automaticamente com a pasta de origem",
        )
        self.campo_pasta = CampoCaminho(
            self.frame_pasta,
            "Pasta com arquivos",
            modo="pasta",
            ao_selecionar=lambda arq: self.campo_pasta_saida.definir_pasta_origem(arq),
        )
        self.campo_pasta.pack(fill="x", pady=(0, 8))
        self.campo_pasta_saida.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(self.frame_pasta, text="Imagens na pasta", font=t.FONT_CORPO, anchor="w").pack(fill="x")
        self.opcao_imagens = ctk.CTkSegmentedButton(
            self.frame_pasta,
            values=["Unir em um PDF", "PDF por imagem"],
        )
        self.opcao_imagens.set("Unir em um PDF")
        self.opcao_imagens.pack(fill="x", pady=(4, 0))
        self.frame_pasta.pack_forget()

    def _atualizar_saida_converter(self, arquivos: list[str]) -> None:
        if not arquivos:
            return
        pasta, nome = sugestao_converter(arquivos)
        if self.opcao_saida.get() == "Unir em um PDF":
            self.campo_saida.definir_sugestao_saida(pasta, nome)
        else:
            self.campo_pasta_saida_arq.definir_pasta_origem(arquivos[0])

    def _alternar_opcao_saida(self, valor: str) -> None:
        if valor == "Unir em um PDF":
            self.campo_pasta_saida_arq.pack_forget()
            self.campo_saida.pack(fill="x")
        else:
            self.campo_saida.pack_forget()
            self.campo_pasta_saida_arq.pack(fill="x")
        arquivos = self.lista.valores()
        if arquivos:
            self._atualizar_saida_converter(arquivos)

    def _alternar_modo(self, valor: str) -> None:
        if valor == "Arquivos":
            self.frame_pasta.pack_forget()
            self.frame_arquivos.pack(fill="x")
        else:
            self.frame_arquivos.pack_forget()
            self.frame_pasta.pack(fill="x")

    def limpar(self) -> None:
        super().limpar()
        self.lista.limpar()
        self.campo_saida.limpar()
        self.campo_pasta_saida_arq.limpar()
        self.campo_pasta.limpar()
        self.campo_pasta_saida.limpar()
        self.opcao_saida.set("Unir em um PDF")
        self._alternar_opcao_saida("Unir em um PDF")
        self.modo.set("Arquivos")
        self._alternar_modo("Arquivos")

    def validar(self) -> str | None:
        if self.modo.get() == "Arquivos":
            if not self.lista.valores():
                return "Adicione ao menos um arquivo."
            if self.opcao_saida.get() == "Unir em um PDF":
                if not self.campo_saida.valor_efetivo():
                    return "Informe o PDF de saída."
            elif not self.campo_pasta_saida_arq.valor_efetivo():
                return "Informe a pasta de saída."
        else:
            if not self.campo_pasta.valor():
                return "Selecione a pasta com os arquivos."
        return None

    def executar_operacao(self, progresso: RelatorioProgresso | None = None) -> ResultadoOperacao:
        if self.modo.get() == "Arquivos":
            juntar = self.opcao_saida.get() == "Unir em um PDF"
            saida = (
                self.campo_saida.valor_efetivo()
                if juntar
                else self.campo_pasta_saida_arq.valor_efetivo()
            )
            return operacao_converter_arquivos(
                self.lista.valores(),
                saida,
                juntar_em_um=juntar,
                progresso=progresso,
            )
        juntar = self.opcao_imagens.get() == "Unir em um PDF"
        pasta_saida = self.campo_pasta_saida.valor() or self.campo_pasta.valor() or None
        return operacao_converter_pasta(
            self.campo_pasta.valor(),
            pasta_saida,
            juntar,
            progresso=progresso,
        )


class PainelExtrair(PainelOperacao):
    titulo = "Extrair páginas específicas"
    descricao = "Informe páginas como: 1,3,5-10 (a ordem será mantida)."

    def montar_conteudo(self) -> None:
        self.campo_saida = CampoCaminho(
            self,
            "PDF de saída",
            modo="salvar_pdf",
            placeholder="Preenchido automaticamente ao selecionar o PDF",
        )
        self.campo_pdf = CampoCaminho(
            self,
            "Arquivo PDF",
            modo="arquivo_pdf",
            ao_selecionar=self._atualizar_saida_extrair,
        )
        self.campo_pdf.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(self, text="Páginas a extrair", font=t.FONT_CORPO, anchor="w").pack(fill="x", pady=(0, 4))
        self.campo_paginas = ctk.CTkEntry(self, placeholder_text="Ex: 1,3,5-10", height=36)
        self.campo_paginas.pack(fill="x", pady=(0, 12))
        self.campo_paginas.bind("<KeyRelease>", lambda _e: self._atualizar_saida_extrair())

        self.campo_saida.pack(fill="x")

    def _atualizar_saida_extrair(self, arquivo: str = "") -> None:
        arq = arquivo or self.campo_pdf.valor()
        if not arq:
            return
        pasta, nome = sugestao_extrair(arq, self.campo_paginas.get())
        self.campo_saida.definir_sugestao_saida(pasta, nome)

    def limpar(self) -> None:
        super().limpar()
        self.campo_pdf.limpar()
        self.campo_paginas.delete(0, "end")
        self.campo_saida.limpar()

    def validar(self) -> str | None:
        if not self.campo_pdf.valor():
            return "Selecione um arquivo PDF."
        if not self.campo_paginas.get().strip():
            return "Informe as páginas a extrair."
        if not self.campo_saida.valor_efetivo():
            return "Informe o PDF de saída."
        return None

    def executar_operacao(self, progresso: RelatorioProgresso | None = None) -> ResultadoOperacao:
        arquivo = self.campo_pdf.valor()
        total = obter_total_paginas(arquivo)
        paginas = interpretar_paginas(self.campo_paginas.get(), total)
        return operacao_extrair_paginas(
            arquivo, paginas, self.campo_saida.valor_efetivo(), progresso=progresso
        )


class PainelRotacionar(PainelOperacao):
    titulo = "Rotacionar páginas"
    descricao = "Gira páginas específicas ou todo o documento."

    def montar_conteudo(self) -> None:
        self.campo_saida = CampoCaminho(
            self,
            "PDF de saída",
            modo="salvar_pdf",
            placeholder="Preenchido automaticamente ao selecionar o PDF",
        )
        self.campo_pdf = CampoCaminho(
            self,
            "Arquivo PDF",
            modo="arquivo_pdf",
            ao_selecionar=self._atualizar_saida_rotacionar,
        )
        self.campo_pdf.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(self, text="Páginas (vazio = todas)", font=t.FONT_CORPO, anchor="w").pack(fill="x", pady=(0, 4))
        self.campo_paginas = ctk.CTkEntry(self, placeholder_text="Ex: 1,3,5-8 ou vazio para todas", height=36)
        self.campo_paginas.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(self, text="Rotação", font=t.FONT_CORPO, anchor="w").pack(fill="x", pady=(0, 4))
        self.combo_rotacao = ctk.CTkComboBox(
            self,
            values=["90° horário", "90° anti-horário", "180°"],
            width=200,
            command=self._atualizar_saida_rotacionar_combo,
        )
        self.combo_rotacao.set("90° horário")
        self.combo_rotacao.pack(anchor="w", pady=(0, 12))

        self.campo_saida.pack(fill="x")

    def _atualizar_saida_rotacionar(self, arquivo: str = "") -> None:
        arq = arquivo or self.campo_pdf.valor()
        if not arq:
            return
        pasta, nome = sugestao_rotacionar(arq, self.combo_rotacao.get())
        self.campo_saida.definir_sugestao_saida(pasta, nome)

    def _atualizar_saida_rotacionar_combo(self, _valor: str) -> None:
        self._atualizar_saida_rotacionar()

    def limpar(self) -> None:
        super().limpar()
        self.campo_pdf.limpar()
        self.campo_paginas.delete(0, "end")
        self.campo_saida.limpar()

    def validar(self) -> str | None:
        if not self.campo_pdf.valor():
            return "Selecione um arquivo PDF."
        if not self.campo_saida.valor_efetivo():
            return "Informe o PDF de saída."
        return None

    def executar_operacao(self, progresso: RelatorioProgresso | None = None) -> ResultadoOperacao:
        arquivo = self.campo_pdf.valor()
        total = obter_total_paginas(arquivo)
        entrada_pag = self.campo_paginas.get().strip()
        paginas = None if not entrada_pag else interpretar_paginas(entrada_pag, total)
        angulos = {"90° horário": 90, "90° anti-horário": -90, "180°": 180}
        angulo = angulos[self.combo_rotacao.get()]
        return operacao_rotacionar(
            arquivo, angulo, self.campo_saida.valor_efetivo(), paginas, progresso=progresso
        )


class PainelComprimir(PainelOperacao):
    titulo = "Comprimir PDF"
    descricao = "Reduz o tamanho do arquivo com diferentes níveis de compressão."

    def montar_conteudo(self) -> None:
        self.campo_saida = CampoCaminho(
            self,
            "PDF de saída",
            modo="salvar_pdf",
            placeholder="Preenchido automaticamente ao selecionar o PDF",
        )
        self.campo_pdf = CampoCaminho(
            self,
            "Arquivo PDF",
            modo="arquivo_pdf",
            ao_selecionar=self._atualizar_saida_comprimir,
        )
        self.campo_pdf.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(self, text="Nível de compressão", font=t.FONT_CORPO, anchor="w").pack(fill="x", pady=(0, 4))
        self.combo_nivel = ctk.CTkComboBox(
            self,
            values=["Leve — melhor qualidade", "Médio — recomendado", "Forte — maior redução"],
            width=320,
            command=self._atualizar_saida_comprimir_combo,
        )
        self.combo_nivel.set("Médio — recomendado")
        self.combo_nivel.pack(anchor="w", pady=(0, 12))

        self.campo_saida.pack(fill="x")

    def _atualizar_saida_comprimir(self, arquivo: str = "") -> None:
        arq = arquivo or self.campo_pdf.valor()
        if not arq:
            return
        pasta, nome = sugestao_comprimir(arq, self.combo_nivel.get())
        self.campo_saida.definir_sugestao_saida(pasta, nome)

    def _atualizar_saida_comprimir_combo(self, _valor: str) -> None:
        self._atualizar_saida_comprimir()

    def limpar(self) -> None:
        super().limpar()
        self.campo_pdf.limpar()
        self.campo_saida.limpar()

    def validar(self) -> str | None:
        if not self.campo_pdf.valor():
            return "Selecione um arquivo PDF."
        if not self.campo_saida.valor_efetivo():
            return "Informe o PDF de saída."
        return None

    def executar_operacao(self, progresso: RelatorioProgresso | None = None) -> ResultadoOperacao:
        niveis = {
            "Leve — melhor qualidade": "leve",
            "Médio — recomendado": "medio",
            "Forte — maior redução": "forte",
        }
        return operacao_comprimir(
            self.campo_pdf.valor(),
            self.campo_saida.valor_efetivo(),
            niveis[self.combo_nivel.get()],
            progresso=progresso,
        )


CATEGORIAS = [
    ("dividir", "Dividir", "✂"),
    ("juntar", "Juntar", "🔗"),
    ("traduzir", "Traduzir", "🌐"),
    ("converter", "Converter", "📄"),
    ("editar", "Editar", "✎"),
]

OPERACOES: list[tuple[str, str, str, type[PainelOperacao]]] = [
    ("dividir_paginas", "A cada N páginas", "dividir", PainelDividirPaginas),
    ("dividir_partes", "Em N partes iguais", "dividir", PainelDividirPartes),
    ("juntar", "Juntar PDFs", "juntar", PainelJuntar),
    ("traduzir", "Traduzir PDF", "traduzir", PainelTraduzir),
    ("traduzir_2col", "Original + tradução (2 col.)", "traduzir", PainelTraduzir2Colunas),
    ("converter", "Converter para PDF", "converter", PainelConverter),
    ("extrair", "Extrair páginas", "editar", PainelExtrair),
    ("rotacionar", "Rotacionar páginas", "editar", PainelRotacionar),
    ("comprimir", "Comprimir PDF", "editar", PainelComprimir),
]
