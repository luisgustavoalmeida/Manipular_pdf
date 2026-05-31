# -*- coding: utf-8 -*-
"""Relatório de progresso unificado (terminal tqdm ou interface gráfica)."""

from __future__ import annotations

import threading
import time
from typing import Callable, Iterable, Protocol, TypeVar, runtime_checkable

from tqdm import tqdm

T = TypeVar("T")


class OperacaoCancelada(Exception):
    """Sinaliza que o usuário solicitou interromper a operação em andamento."""


class ControleCancelamento:
    """Flag thread-safe para cancelamento cooperativo."""

    def __init__(self) -> None:
        self._evento = threading.Event()

    @property
    def cancelado(self) -> bool:
        return self._evento.is_set()

    def solicitar(self) -> None:
        self._evento.set()

    def verificar(self) -> None:
        if self.cancelado:
            raise OperacaoCancelada()

    def reiniciar(self) -> None:
        self._evento.clear()


def verificar_cancelamento(progresso: RelatorioProgresso | None) -> None:
    """Propaga verificação de cancelamento para qualquer implementação de progresso."""
    if progresso is None:
        return
    progresso.verificar_cancelamento()


def formatar_duracao(segundos: float | None) -> str:
    """Formata segundos em texto legível (ex.: 1m 05s)."""
    if segundos is None:
        return "—"
    segundos = max(0, int(segundos))
    if segundos < 60:
        return f"{segundos}s"
    minutos, seg = divmod(segundos, 60)
    if minutos < 60:
        return f"{minutos}m {seg:02d}s"
    horas, minutos = divmod(minutos, 60)
    return f"{horas}h {minutos:02d}m"


def estimar_restante(decorrido: float, fracao: float) -> float | None:
    """Estima segundos restantes com base no ritmo atual."""
    if fracao <= 0.01 or decorrido <= 0:
        return None
    if fracao >= 1.0:
        return 0.0
    return decorrido * (1.0 - fracao) / fracao


@runtime_checkable
class RelatorioProgresso(Protocol):
    def iniciar(self, total: int, descricao: str = "") -> None: ...
    def avancar(self, quantidade: int = 1, mensagem: str = "") -> None: ...
    def concluir(self) -> None: ...
    def verificar_cancelamento(self) -> None: ...


class ProgressoNulo:
    def iniciar(self, total: int, descricao: str = "") -> None:
        pass

    def avancar(self, quantidade: int = 1, mensagem: str = "") -> None:
        pass

    def concluir(self) -> None:
        pass

    def verificar_cancelamento(self) -> None:
        pass


PROGRESSO_NULO = ProgressoNulo()


class ProgressoInterface(ProgressoNulo):
    """Progresso com callback (ex.: atualizar barra na GUI)."""

    def __init__(
        self,
        ao_atualizar: Callable[[float, str, int, int, float, float | None], None],
        controle: ControleCancelamento | None = None,
    ) -> None:
        self._ao_atualizar = ao_atualizar
        self._controle = controle
        self._total = 1
        self._atual = 0
        self._descricao = ""
        self._inicio: float | None = None

    @property
    def controle_cancelamento(self) -> ControleCancelamento | None:
        return self._controle

    def verificar_cancelamento(self) -> None:
        if self._controle:
            self._controle.verificar()

    def iniciar(self, total: int, descricao: str = "") -> None:
        self.verificar_cancelamento()
        self._total = max(1, total)
        self._atual = 0
        self._descricao = descricao
        self._inicio = time.monotonic()
        self._emitir()

    def avancar(self, quantidade: int = 1, mensagem: str = "") -> None:
        self.verificar_cancelamento()
        if mensagem:
            self._descricao = mensagem
        self._atual = min(self._total, self._atual + quantidade)
        self._emitir()

    def definir(self, atual: int, mensagem: str = "") -> None:
        self.verificar_cancelamento()
        if mensagem:
            self._descricao = mensagem
        self._atual = min(self._total, max(0, atual))
        if self._inicio is None:
            self._inicio = time.monotonic()
        self._emitir()

    def concluir(self) -> None:
        self.verificar_cancelamento()
        self._atual = self._total
        self._emitir()

    def _emitir(self) -> None:
        fracao = self._atual / self._total
        decorrido = time.monotonic() - self._inicio if self._inicio is not None else 0.0
        restante = estimar_restante(decorrido, fracao)
        self._ao_atualizar(fracao, self._descricao, self._atual, self._total, decorrido, restante)


class ProgressoParcial(ProgressoNulo):
    """Reporta progresso dentro de uma faixa de um progresso pai."""

    def __init__(self, pai: RelatorioProgresso, offset: int, total: int) -> None:
        self._pai = pai
        self._offset = offset
        self._total = max(1, total)
        self._local = 0
        self._descricao = ""

    def iniciar(self, total: int, descricao: str = "") -> None:
        self.verificar_cancelamento()
        self._total = max(1, total)
        self._local = 0
        self._descricao = descricao

    def avancar(self, quantidade: int = 1, mensagem: str = "") -> None:
        self.verificar_cancelamento()
        self._local = min(self._total, self._local + quantidade)
        texto = mensagem or self._descricao
        if isinstance(self._pai, ProgressoInterface):
            self._pai.definir(self._offset + self._local, texto)
        else:
            self._pai.avancar(quantidade, texto)

    def concluir(self) -> None:
        self.verificar_cancelamento()
        if isinstance(self._pai, ProgressoInterface):
            self._pai.definir(self._offset + self._total, self._descricao)
        else:
            self._pai.concluir()

    def verificar_cancelamento(self) -> None:
        if isinstance(self._pai, (ProgressoInterface, ProgressoParcial)):
            self._pai.verificar_cancelamento()


def percorrer(
    sequencia: Iterable[T],
    *,
    descricao: str = "",
    progresso: RelatorioProgresso | None = None,
    unit: str = "item",
    gerencia_ciclo: bool = True,
) -> Iterable[T]:
    """Itera com tqdm (terminal) ou avanço manual (interface)."""
    if progresso is None:
        yield from tqdm(sequencia, desc=descricao, unit=unit)
        return

    itens = list(sequencia)
    if gerencia_ciclo:
        progresso.iniciar(len(itens), descricao)
    for item in itens:
        verificar_cancelamento(progresso)
        yield item
        progresso.avancar(1, descricao if not gerencia_ciclo else "")
    if gerencia_ciclo:
        progresso.concluir()
