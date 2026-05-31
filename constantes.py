# -*- coding: utf-8 -*-
"""Constantes compartilhadas entre interface console, gráfica e lógica de negócio."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

TITULO_APLICACAO = "Manipulador PDF"
# Fonte única da versão — ao alterar, execute: python constantes.py
VERSAO_APLICACAO = "2.0"
__version__ = VERSAO_APLICACAO


def texto_versao() -> str:
    """Rótulo curto da versão (ex.: v2.0)."""
    return f"v{VERSAO_APLICACAO}"


def titulo_com_versao() -> str:
    """Título do aplicativo com versão (ex.: Manipulador PDF v2.0)."""
    return f"{TITULO_APLICACAO} {texto_versao()}"


def linha_versao() -> str:
    """Linha para --version (ex.: Manipulador PDF 2.0)."""
    return f"{TITULO_APLICACAO} {VERSAO_APLICACAO}"


def sincronizar_versao_readme(caminho: Path | None = None) -> bool:
    """
    Atualiza marcadores de versão no README a partir de VERSAO_APLICACAO.
    Retorna True se o arquivo foi alterado.
    """
    readme = caminho or Path(__file__).resolve().parent / "README.md"
    if not readme.is_file():
        return False

    texto = readme.read_text(encoding="utf-8")
    versao = VERSAO_APLICACAO
    atualizado = texto

    substituicoes = [
        (r"<!-- versao:[\d.]+ -->", f"<!-- versao:{versao} -->"),
        (r"(# Manipulador PDF · )v[\d.]+", rf"\1v{versao}"),
        (r"(Versão atual: \*\*)[\d.]+(\*\*)", rf"\g<1>{versao}\2"),
    ]
    for padrao, substituicao in substituicoes:
        atualizado = re.sub(padrao, substituicao, atualizado)

    if atualizado == texto:
        return False

    readme.write_text(atualizado, encoding="utf-8")
    return True

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


if __name__ == "__main__":
    if sincronizar_versao_readme():
        print(f"README atualizado para a versão {VERSAO_APLICACAO}.")
    else:
        print(f"README já está em {VERSAO_APLICACAO}.")
