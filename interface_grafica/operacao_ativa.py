# -*- coding: utf-8 -*-
"""Estado global de operações em execução (independente do painel visível)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from operacoes import ResultadoOperacao
from progresso import ControleCancelamento

if TYPE_CHECKING:
    from interface_grafica.paineis import PainelOperacao


@dataclass
class OperacaoEmExecucao:
    op_id: str
    titulo: str
    painel: PainelOperacao
    fracao: float = 0.0
    mensagem: str = "Processando…"
    atual: int = 0
    total: int = 0
    decorrido: float = 0.0
    restante: float | None = None
    controle: ControleCancelamento | None = None


@dataclass
class GerenciadorOperacoes:
    """Rastreia uma operação longa enquanto o usuário navega entre painéis."""

    titulos: dict[str, str] = field(default_factory=dict)
    _ativa: OperacaoEmExecucao | None = None

    @property
    def op_id(self) -> str | None:
        return self._ativa.op_id if self._ativa else None

    @property
    def ativa(self) -> OperacaoEmExecucao | None:
        return self._ativa

    def esta_executando(self, op_id: str | None = None) -> bool:
        if self._ativa is None:
            return False
        if op_id is None:
            return True
        return self._ativa.op_id == op_id

    def iniciar(self, op_id: str, painel: PainelOperacao, controle: ControleCancelamento) -> None:
        self._ativa = OperacaoEmExecucao(
            op_id=op_id,
            titulo=self.titulos.get(op_id, op_id),
            painel=painel,
            controle=controle,
        )

    def solicitar_cancelamento(self) -> bool:
        if self._ativa is None or self._ativa.controle is None:
            return False
        if self._ativa.controle.cancelado:
            return False
        self._ativa.controle.solicitar()
        return True

    def atualizar_progresso(
        self,
        op_id: str,
        fracao: float,
        mensagem: str,
        atual: int = 0,
        total: int = 0,
        decorrido: float = 0.0,
        restante: float | None = None,
    ) -> None:
        if self._ativa is None or self._ativa.op_id != op_id:
            return
        self._ativa.fracao = fracao
        self._ativa.mensagem = mensagem
        self._ativa.atual = atual
        self._ativa.total = total
        self._ativa.decorrido = decorrido
        self._ativa.restante = restante

    def finalizar(self, op_id: str) -> OperacaoEmExecucao | None:
        if self._ativa is None or self._ativa.op_id != op_id:
            return None
        concluida = self._ativa
        self._ativa = None
        return concluida
