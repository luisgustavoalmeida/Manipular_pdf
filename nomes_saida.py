# -*- coding: utf-8 -*-
"""Nomes e pastas sugeridos para arquivos de saída, por tipo de operação."""

from __future__ import annotations

from pathlib import Path


def pasta_de(caminho: str | Path) -> Path:
    """Retorna a pasta do arquivo ou a própria pasta informada."""
    p = Path(caminho).resolve()
    if p.exists():
        return p.parent if p.is_file() else p
    return p.parent if p.suffix else p


def caminho_pdf_completo(pasta: Path | str, nome_arquivo: str) -> str:
    """Monta caminho completo garantindo extensão .pdf."""
    nome = nome_arquivo if nome_arquivo.lower().endswith(".pdf") else f"{nome_arquivo}.pdf"
    return str(Path(pasta) / nome)


def prefixo_dividir(arquivo: str | Path) -> str:
    """Prefixo intuitivo para partes ao dividir PDF."""
    return f"{Path(arquivo).stem}_parte"


def sugestao_juntar(arquivos: list[str]) -> tuple[Path, str]:
    pasta = pasta_de(arquivos[0])
    stems = {Path(a).stem for a in arquivos}
    if len(stems) == 1:
        nome = f"{Path(arquivos[0]).stem}_juntado.pdf"
    elif len(arquivos) == 2:
        a, b = Path(arquivos[0]).stem, Path(arquivos[1]).stem
        nome = f"{a}_e_{b}.pdf"
    else:
        nome = f"{Path(arquivos[0]).stem}_juntado_{len(arquivos)}arquivos.pdf"
    return pasta, nome


def sugestao_converter(arquivos: list[str]) -> tuple[Path, str]:
    pasta = pasta_de(arquivos[0])
    if len(arquivos) == 1:
        return pasta, f"{Path(arquivos[0]).stem}.pdf"
    return pasta, "documento_convertido.pdf"


def sugestao_extrair(arquivo: str, paginas: str = "") -> tuple[Path, str]:
    stem = Path(arquivo).stem
    if paginas.strip():
        slug = paginas.strip().replace(" ", "").replace(",", "-")[:40]
        nome = f"{stem}_paginas_{slug}.pdf"
    else:
        nome = f"{stem}_paginas.pdf"
    return pasta_de(arquivo), nome


def sugestao_rotacionar(arquivo: str, rotacao: str = "") -> tuple[Path, str]:
    stem = Path(arquivo).stem
    sufixos = {
        "90° horário": "rotacionado_90h",
        "90° anti-horário": "rotacionado_90ah",
        "180°": "rotacionado_180",
    }
    sufixo = sufixos.get(rotacao, "rotacionado")
    return pasta_de(arquivo), f"{stem}_{sufixo}.pdf"


def sugestao_comprimir(arquivo: str, nivel: str = "") -> tuple[Path, str]:
    stem = Path(arquivo).stem
    niveis = {
        "Leve — melhor qualidade": "comprimido_leve",
        "Médio — recomendado": "comprimido",
        "Forte — maior redução": "comprimido_forte",
    }
    sufixo = niveis.get(nivel, "comprimido")
    return pasta_de(arquivo), f"{stem}_{sufixo}.pdf"


def sugestao_traducao(arquivo: str, codigo_idioma: str) -> tuple[Path, str]:
    stem = Path(arquivo).stem
    return pasta_de(arquivo), f"{stem}_google_{codigo_idioma}.pdf"


def sugestao_traducao_2colunas(arquivo: str, codigo_idioma: str) -> tuple[Path, str]:
    stem = Path(arquivo).stem
    return pasta_de(arquivo), f"{stem}_2colunas_{codigo_idioma}.pdf"
