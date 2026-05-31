# -*- coding: utf-8 -*-
"""Constantes compartilhadas entre interface console, gráfica e lógica de negócio."""

from dataclasses import dataclass
from typing import Callable

TITULO_APLICACAO = "Manipulador PDF"
VERSAO_APLICACAO = "2.0"

MOTOR_TRADUCAO_GOOGLE = ("google", "Google Translate")

IDIOMAS_DISPONIVEIS: list[tuple[str, str]] = [
    ("pt", "Português"),
    ("en", "Inglês"),
    ("es", "Espanhol"),
    ("fr", "Francês"),
    ("de", "Alemão"),
    ("it", "Italiano"),
    ("ja", "Japonês"),
    ("zh", "Chinês"),
    ("ko", "Coreano"),
    ("ru", "Russo"),
    ("ar", "Árabe"),
    ("hi", "Hindi"),
]

NOMES_IDIOMAS = {cod: nome for cod, nome in IDIOMAS_DISPONIVEIS}


def normalizar_idioma_origem(entrada: str) -> str | None:
    """Converte número ou código em código ISO; None = detecção automática."""
    entrada = entrada.strip()
    if not entrada:
        return None
    try:
        idx = int(entrada)
        if 1 <= idx <= len(IDIOMAS_DISPONIVEIS):
            return IDIOMAS_DISPONIVEIS[idx - 1][0]
    except ValueError:
        pass
    codigo = next((c for c, _ in IDIOMAS_DISPONIVEIS if c == entrada.lower()), None)
    return codigo


def resolver_idioma_destino(entrada: str) -> tuple[str, str] | None:
    """Resolve um idioma de destino a partir de número ou código."""
    entrada = entrada.strip()
    try:
        idx = int(entrada)
        if 1 <= idx <= len(IDIOMAS_DISPONIVEIS):
            return IDIOMAS_DISPONIVEIS[idx - 1]
    except ValueError:
        pass
    for cod, nome in IDIOMAS_DISPONIVEIS:
        if cod == entrada.lower():
            return (cod, nome)
    return None


@dataclass(frozen=True)
class CategoriaOperacao:
    """Agrupa operações na barra lateral da interface gráfica."""

    id: str
    titulo: str
    icone: str


@dataclass(frozen=True)
class DefinicaoOperacao:
    """Metadados de uma operação disponível no aplicativo."""

    id: str
    titulo: str
    descricao: str
    categoria_id: str
    icone: str = "📄"
    # Referência preenchida em runtime pela interface gráfica
    criar_painel: Callable | None = None
