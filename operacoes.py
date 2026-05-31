# -*- coding: utf-8 -*-
"""Lógica de negócio das operações PDF — sem dependência de interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from constantes import IDIOMAS_DISPONIVEIS, MOTOR_TRADUCAO_GOOGLE
from converter_para_pdf import (
    converter_arquivos_para_pdf,
    converter_arquivos_para_pdfs_individuais,
    converter_pasta_para_pdf,
)
from dividir_pdf import dividir_em_partes, dividir_por_paginas
from editar_pdf import (
    comprimir_pdf,
    extrair_paginas,
    obter_total_paginas,
    resumo_compressao,
    rotacionar_paginas,
)
from juntar_pdf import juntar_pdfs
from progresso import OperacaoCancelada, ProgressoParcial, RelatorioProgresso
from traduzir_pdf import criar_pdf_duas_colunas, traduzir_pdf


@dataclass
class ResultadoOperacao:
    """Resultado padronizado de uma operação PDF."""

    sucesso: bool
    titulo: str
    pasta: Path
    arquivos: list[str] = field(default_factory=list)
    mensagem: str = ""
    detalhes: str = ""
    cancelado: bool = False


def _resultado_ok(titulo: str, pasta: Path, arquivos: list[str], mensagem: str = "") -> ResultadoOperacao:
    return ResultadoOperacao(True, titulo, pasta, arquivos, mensagem)


def _resultado_erro(titulo: str, pasta: Path, erro: str) -> ResultadoOperacao:
    return ResultadoOperacao(False, titulo, pasta, [], erro, erro)


def _resultado_cancelado(titulo: str, pasta: Path) -> ResultadoOperacao:
    msg = "Operação cancelada pelo usuário."
    return ResultadoOperacao(
        sucesso=False,
        titulo=titulo,
        pasta=pasta,
        mensagem=msg,
        detalhes=msg,
        cancelado=True,
    )


def operacao_dividir_por_paginas(
    arquivo: str,
    paginas_por_parte: int,
    pasta_saida: str | None = None,
    progresso: RelatorioProgresso | None = None,
) -> ResultadoOperacao:
    from nomes_saida import prefixo_dividir

    pasta = Path(pasta_saida) if pasta_saida else Path(arquivo).parent
    try:
        lista = dividir_por_paginas(
            arquivo,
            paginas_por_parte,
            pasta_saida=pasta_saida,
            prefixo_nome=prefixo_dividir(arquivo),
            progresso=progresso,
        )
        pasta_final = Path(lista[0]).parent if lista else pasta
        return _resultado_ok("Divisão concluída", pasta_final, lista, f"{len(lista)} arquivo(s) gerado(s).")
    except OperacaoCancelada:
        raise
    except Exception as e:
        return _resultado_erro("Divisão", pasta, str(e))


def operacao_dividir_em_partes(
    arquivo: str,
    num_partes: int,
    pasta_saida: str | None = None,
    progresso: RelatorioProgresso | None = None,
) -> ResultadoOperacao:
    from nomes_saida import prefixo_dividir

    pasta = Path(pasta_saida) if pasta_saida else Path(arquivo).parent
    try:
        lista = dividir_em_partes(
            arquivo,
            num_partes,
            pasta_saida=pasta_saida,
            prefixo_nome=prefixo_dividir(arquivo),
            progresso=progresso,
        )
        pasta_final = Path(lista[0]).parent if lista else pasta
        return _resultado_ok("Divisão concluída", pasta_final, lista, f"{len(lista)} parte(s) gerada(s).")
    except OperacaoCancelada:
        raise
    except Exception as e:
        return _resultado_erro("Divisão", pasta, str(e))


def operacao_juntar(
    arquivos: list[str],
    saida: str,
    progresso: RelatorioProgresso | None = None,
) -> ResultadoOperacao:
    pasta = Path(saida).parent
    try:
        resultado = juntar_pdfs(arquivos, saida, progresso=progresso)
        return _resultado_ok("PDF juntado", Path(resultado).parent, [resultado])
    except OperacaoCancelada:
        raise
    except Exception as e:
        return _resultado_erro("Junção", pasta, str(e))


def operacao_traduzir(
    arquivo: str,
    idiomas: list[tuple[str, str]],
    idioma_origem: str | None = None,
    numero_workers: int | None = None,
    progresso: RelatorioProgresso | None = None,
) -> ResultadoOperacao:
    path_entrada = Path(arquivo)
    pasta_origem = path_entrada.parent
    stem, sufixo = path_entrada.stem, path_entrada.suffix
    codigo_motor, _ = MOTOR_TRADUCAO_GOOGLE
    gerados: list[str] = []
    erros: list[str] = []

    paginas = obter_total_paginas(arquivo)
    if progresso:
        progresso.iniciar(paginas * len(idiomas), "Traduzindo PDF")

    for indice, (codigo_idioma, nome_idioma) in enumerate(idiomas):
        caminho_saida = pasta_origem / f"{stem}_{codigo_motor}_{codigo_idioma}{sufixo}"
        parcial = (
            ProgressoParcial(progresso, indice * paginas, paginas)
            if progresso
            else None
        )
        try:
            resultado = traduzir_pdf(
                arquivo,
                str(caminho_saida),
                idioma_destino=codigo_idioma,
                idioma_origem=idioma_origem,
                provedor=codigo_motor,
                numero_workers=numero_workers,
                progresso=parcial,
            )
            gerados.append(resultado)
        except OperacaoCancelada:
            raise
        except Exception as e:
            erros.append(f"{nome_idioma}: {e}")

    if progresso:
        progresso.concluir()

    if gerados:
        msg = f"{len(gerados)} tradução(ões) concluída(s)."
        if erros:
            msg += f" Erros: {'; '.join(erros)}"
        return ResultadoOperacao(
            sucesso=not erros,
            titulo="Tradução concluída",
            pasta=pasta_origem,
            arquivos=gerados,
            mensagem=msg,
            detalhes="; ".join(erros) if erros else "",
        )
    return _resultado_erro("Tradução", pasta_origem, "; ".join(erros) or "Nenhum arquivo gerado.")


def operacao_traduzir_2colunas(
    arquivo: str,
    codigo_idioma: str,
    idioma_origem: str | None = None,
    numero_workers: int | None = None,
    progresso: RelatorioProgresso | None = None,
) -> ResultadoOperacao:
    path_entrada = Path(arquivo)
    pasta_origem = path_entrada.parent
    stem, sufixo = path_entrada.stem, path_entrada.suffix
    codigo_motor = MOTOR_TRADUCAO_GOOGLE[0]
    caminho_traduzido = pasta_origem / f"{stem}_{codigo_motor}_{codigo_idioma}{sufixo}"
    caminho_2colunas = pasta_origem / f"{stem}_2colunas_{codigo_idioma}{sufixo}"

    try:
        paginas = obter_total_paginas(arquivo)
        if progresso:
            progresso.iniciar(paginas * 2, "Traduzindo em 2 colunas")

        traduzir_pdf(
            arquivo,
            str(caminho_traduzido),
            idioma_destino=codigo_idioma,
            idioma_origem=idioma_origem,
            numero_workers=numero_workers,
            progresso=ProgressoParcial(progresso, 0, paginas) if progresso else None,
        )
        criar_pdf_duas_colunas(
            arquivo,
            str(caminho_traduzido),
            str(caminho_2colunas),
            progresso=ProgressoParcial(progresso, paginas, paginas) if progresso else None,
        )
        if progresso:
            progresso.concluir()
        return _resultado_ok(
            "PDF 2 colunas gerado",
            pasta_origem,
            [str(caminho_2colunas)],
            "Original à esquerda, tradução à direita.",
        )
    except OperacaoCancelada:
        raise
    except Exception as e:
        return _resultado_erro("PDF 2 colunas", pasta_origem, str(e))


def operacao_converter_arquivos(
    arquivos: list[str],
    saida: str,
    juntar_em_um: bool = True,
    progresso: RelatorioProgresso | None = None,
) -> ResultadoOperacao:
    pasta = Path(saida).parent if juntar_em_um else Path(saida)
    try:
        if juntar_em_um:
            resultado = converter_arquivos_para_pdf(arquivos, saida, progresso=progresso)
            return _resultado_ok("Conversão concluída", Path(resultado).parent, [resultado])
        resultados = converter_arquivos_para_pdfs_individuais(
            arquivos, pasta_saida=saida, progresso=progresso
        )
        pasta_resultado = Path(resultados[0]).parent if resultados else pasta
        return _resultado_ok(
            "Conversão concluída",
            pasta_resultado,
            resultados,
            f"{len(resultados)} PDF(s) gerado(s).",
        )
    except OperacaoCancelada:
        raise
    except Exception as e:
        return _resultado_erro("Conversão", pasta, str(e))


def operacao_converter_pasta(
    pasta: str,
    pasta_saida: str | None,
    juntar_imagens: bool,
    progresso: RelatorioProgresso | None = None,
) -> ResultadoOperacao:
    pasta_path = Path(pasta)
    try:
        resultados = converter_pasta_para_pdf(
            pasta,
            pasta_saida=pasta_saida,
            juntar_imagens=juntar_imagens,
            progresso=progresso,
        )
        pasta_resultado = Path(resultados[0]).parent if resultados else pasta_path
        return _resultado_ok(
            "Conversão concluída",
            pasta_resultado,
            resultados,
            f"{len(resultados)} arquivo(s) gerado(s).",
        )
    except OperacaoCancelada:
        raise
    except Exception as e:
        return _resultado_erro("Conversão", pasta_path, str(e))


def operacao_extrair_paginas(
    arquivo: str,
    paginas: list[int],
    saida: str,
    progresso: RelatorioProgresso | None = None,
) -> ResultadoOperacao:
    pasta = Path(saida).parent
    try:
        resultado = extrair_paginas(arquivo, paginas, saida, progresso=progresso)
        return _resultado_ok("Extração concluída", Path(resultado).parent, [resultado])
    except OperacaoCancelada:
        raise
    except Exception as e:
        return _resultado_erro("Extração", pasta, str(e))


def operacao_rotacionar(
    arquivo: str,
    angulo: int,
    saida: str,
    paginas: list[int] | None = None,
    progresso: RelatorioProgresso | None = None,
) -> ResultadoOperacao:
    pasta = Path(saida).parent
    try:
        resultado = rotacionar_paginas(arquivo, angulo, saida, paginas=paginas, progresso=progresso)
        return _resultado_ok("Rotação concluída", Path(resultado).parent, [resultado])
    except OperacaoCancelada:
        raise
    except Exception as e:
        return _resultado_erro("Rotação", pasta, str(e))


def operacao_comprimir(
    arquivo: str,
    saida: str,
    nivel: str = "medio",
    progresso: RelatorioProgresso | None = None,
) -> ResultadoOperacao:
    pasta = Path(saida).parent
    try:
        resultado = comprimir_pdf(arquivo, saida, nivel=nivel, progresso=progresso)
        resumo = resumo_compressao(arquivo, resultado)
        return _resultado_ok("Compressão concluída", Path(resultado).parent, [resultado], resumo)
    except OperacaoCancelada:
        raise
    except Exception as e:
        return _resultado_erro("Compressão", pasta, str(e))


def resolver_idiomas_por_indices(indices: list[int]) -> list[tuple[str, str]]:
    """Converte índices 0-based em tuplas (código, nome)."""
    return [IDIOMAS_DISPONIVEIS[i] for i in sorted(set(indices)) if 0 <= i < len(IDIOMAS_DISPONIVEIS)]
