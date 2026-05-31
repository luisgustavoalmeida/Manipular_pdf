# -*- coding: utf-8 -*-
"""
Programa principal para manipulação de arquivos PDF.
Interface gráfica por padrão; use --console para o menu em terminal.
"""

import argparse
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

import interface_console as ui
import navegacao as nav
from constantes import (
    IDIOMAS_DISPONIVEIS,
    linha_versao,
    titulo_com_versao,
    normalizar_idioma_origem,
    resolver_idioma_destino,
)
from converter_para_pdf import (
    formatos_suportados_texto,
    libreoffice_disponivel,
    MSG_LIBREOFFICE,
)
from configuracoes import nucleos_disponiveis, threads_sugeridas_traducao
from editar_pdf import obter_total_paginas
from navegacao import OperacaoCancelada
from operacoes import (
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


def _finalizar_operacao() -> None:
    ui.aguardar_enter()


def _mostrar_resultado(resultado) -> None:
    nav.mostrar_resultado(
        resultado.titulo,
        resultado.pasta,
        resultado.arquivos,
        mensagem_vazio=resultado.detalhes,
        oferecer_abrir_pasta=resultado.sucesso,
    )
    if not resultado.sucesso and resultado.detalhes:
        ui.mensagem_erro(resultado.detalhes)
    elif resultado.mensagem and resultado.sucesso:
        ui.mensagem_ok(resultado.mensagem)


def _escolher_idiomas() -> list[tuple[str, str]] | None:
    opcao = ui.menu_opcoes(
        "Traduzir para qual(is) idioma(s)?",
        [
            ("1", "Um idioma"),
            ("2", "Vários idiomas"),
            ("3", "Todos os disponíveis"),
        ],
        padrao="1",
    )
    if opcao == "1":
        print("  Idiomas disponíveis (número ou código):")
        for i, (cod, nome) in enumerate(IDIOMAS_DISPONIVEIS, 1):
            print(f"    {ui.C_OPCAO}{i}.{ui.C_RESET} {nome} ({cod})")
        codigo = ui.pergunta("Idioma de destino", "pt").strip()
        idioma = resolver_idioma_destino(codigo)
        if idioma:
            return [idioma]
        return [(codigo, codigo)]
    if opcao == "2":
        print("  Idiomas disponíveis:")
        for i, (cod, nome) in enumerate(IDIOMAS_DISPONIVEIS, 1):
            print(f"    {i}. {nome} ({cod})")
        escolha = ui.pergunta("Números separados por vírgula (ex: 1,3,5)")
        indices = []
        for s in escolha.replace(" ", "").split(","):
            try:
                n = int(s)
                if 1 <= n <= len(IDIOMAS_DISPONIVEIS):
                    indices.append(n - 1)
            except ValueError:
                pass
        if not indices:
            ui.mensagem_aviso("Nenhum idioma válido informado.")
            return None
        return resolver_idiomas_por_indices(indices)
    return IDIOMAS_DISPONIVEIS.copy()


def _escolher_um_idioma() -> tuple[str, str] | None:
    print("  Idiomas disponíveis (número ou código):")
    for i, (cod, nome) in enumerate(IDIOMAS_DISPONIVEIS, 1):
        print(f"    {ui.C_OPCAO}{i}.{ui.C_RESET} {nome} ({cod})")
    codigo = ui.pergunta("Idioma de destino", "pt").strip()
    idioma = resolver_idioma_destino(codigo)
    if idioma is None:
        ui.mensagem_aviso("Idioma não reconhecido.")
    return idioma


def executar_dividir_por_paginas() -> None:
    ui.secao("Dividir PDF — a cada N páginas")
    try:
        ui.passo(1, 3, "Selecionar o PDF")
        arquivo = nav.solicitar_arquivo_pdf("Selecione o PDF para dividir")
        ui.passo(2, 3, "Definir tamanho de cada parte")
        paginas = nav.solicitar_inteiro("Quantas páginas por parte?", minimo=1, padrao=10)
        ui.passo(3, 3, "Escolher pasta de saída")
        pasta = nav.solicitar_pasta_saida("Mesma pasta do PDF", diretorio_inicial=Path(arquivo).parent)
        ui.info("Dividindo...")
        _mostrar_resultado(operacao_dividir_por_paginas(arquivo, paginas, pasta))
    except OperacaoCancelada:
        ui.mensagem_aviso("Operação cancelada.")
    except Exception as e:
        ui.mensagem_erro(str(e))
    finally:
        _finalizar_operacao()


def executar_dividir_em_partes() -> None:
    ui.secao("Dividir PDF — em N partes iguais")
    try:
        ui.passo(1, 3, "Selecionar o PDF")
        arquivo = nav.solicitar_arquivo_pdf("Selecione o PDF para dividir")
        ui.passo(2, 3, "Definir quantidade de partes")
        partes = nav.solicitar_inteiro("Em quantas partes dividir?", minimo=2, padrao=2)
        ui.passo(3, 3, "Escolher pasta de saída")
        pasta = nav.solicitar_pasta_saida("Mesma pasta do PDF", diretorio_inicial=Path(arquivo).parent)
        ui.info("Dividindo...")
        _mostrar_resultado(operacao_dividir_em_partes(arquivo, partes, pasta))
    except OperacaoCancelada:
        ui.mensagem_aviso("Operação cancelada.")
    except Exception as e:
        ui.mensagem_erro(str(e))
    finally:
        _finalizar_operacao()


def executar_juntar() -> None:
    ui.secao("Juntar PDFs")
    try:
        ui.passo(1, 2, "Selecionar os PDFs")
        lista = nav.solicitar_arquivos_pdf("Selecione PDFs para juntar")
        ui.passo(2, 2, "Definir arquivo de saída")
        saida = nav.solicitar_salvar_pdf(
            "Salvar PDF juntado como",
            nome_sugerido="documento_juntado.pdf",
            diretorio_inicial=Path(lista[0]).parent,
        )
        if not saida:
            ui.mensagem_aviso("Operação cancelada — destino não informado.")
            return
        ui.info("Juntando...")
        _mostrar_resultado(operacao_juntar(lista, saida))
    except OperacaoCancelada:
        ui.mensagem_aviso("Operação cancelada.")
    except Exception as e:
        ui.mensagem_erro(str(e))
    finally:
        _finalizar_operacao()


def _escolher_threads_traducao() -> int:
    nucleos = nucleos_disponiveis()
    sugestao = threads_sugeridas_traducao()
    ui.info(
        f"Seu computador tem {nucleos} núcleo(s) lógico(s). "
        f"Recomendado: {sugestao} thread(s) para tradução em paralelo."
    )
    return nav.solicitar_inteiro(
        "Quantas threads usar na tradução?",
        minimo=1,
        maximo=nucleos,
        padrao=sugestao,
    )


def executar_traduzir() -> None:
    ui.secao("Traduzir PDF (Google Translate)")
    pasta_origem: Path | None = None
    try:
        ui.passo(1, 4, "Selecionar o PDF")
        arquivo = nav.solicitar_arquivo_pdf("Selecione o PDF para traduzir")
        pasta_origem = Path(arquivo).parent
        ui.mensagem_ok(f"Traduções serão salvas em: {pasta_origem}")
        ui.passo(2, 4, "Escolher idioma(s) de destino")
        idiomas = _escolher_idiomas()
        if not idiomas:
            return
        ui.passo(3, 4, "Confirmar idioma de origem")
        idioma_origem = normalizar_idioma_origem(ui.pergunta("Idioma de origem (Enter = detectar automaticamente)"))
        ui.passo(4, 4, "Threads de tradução")
        threads = _escolher_threads_traducao()
        ui.info(f"Traduzindo {len(idiomas)} arquivo(s) com {threads} thread(s)...")
        _mostrar_resultado(operacao_traduzir(arquivo, idiomas, idioma_origem, numero_workers=threads))
    except OperacaoCancelada:
        ui.mensagem_aviso("Operação cancelada.")
    except Exception as e:
        ui.mensagem_erro(str(e))
        if pasta_origem:
            nav.mostrar_resultado("Tradução (erro)", pasta_origem, [], oferecer_abrir_pasta=False)
    finally:
        _finalizar_operacao()


def executar_traduzir_2colunas() -> None:
    ui.secao("Traduzir PDF — Original + Tradução em 2 colunas")
    ui.info("Gera um PDF lado a lado: original à esquerda, tradução à direita.")
    pasta_origem: Path | None = None
    try:
        ui.passo(1, 4, "Selecionar o PDF")
        arquivo = nav.solicitar_arquivo_pdf("Selecione o PDF para traduzir")
        pasta_origem = Path(arquivo).parent
        ui.passo(2, 4, "Escolher idioma de destino")
        idioma = _escolher_um_idioma()
        if not idioma:
            return
        ui.passo(3, 4, "Confirmar idioma de origem")
        idioma_origem = normalizar_idioma_origem(ui.pergunta("Idioma de origem (Enter = detectar automaticamente)"))
        ui.passo(4, 4, "Threads de tradução")
        threads = _escolher_threads_traducao()
        ui.info(f"Traduzindo e montando PDF em 2 colunas com {threads} thread(s)...")
        _mostrar_resultado(
            operacao_traduzir_2colunas(arquivo, idioma[0], idioma_origem, numero_workers=threads)
        )
    except OperacaoCancelada:
        ui.mensagem_aviso("Operação cancelada.")
    except Exception as e:
        ui.mensagem_erro(str(e))
        if pasta_origem:
            nav.mostrar_resultado("PDF 2 colunas (erro)", pasta_origem, [], oferecer_abrir_pasta=False)
    finally:
        _finalizar_operacao()


def executar_converter_para_pdf() -> None:
    ui.secao("Converter arquivos para PDF")
    ui.info(formatos_suportados_texto())
    if not libreoffice_disponivel():
        ui.mensagem_aviso(
            "Word/Excel/PowerPoint exigem LibreOffice instalado. "
            "Imagens, texto e HTML funcionam sem instalação extra."
        )
    try:
        modo = ui.menu_opcoes(
            "O que deseja converter?",
            [
                ("1", "Um ou mais arquivos"),
                ("2", "Todos os arquivos de uma pasta"),
            ],
            padrao="1",
        )
        if modo == "1":
            ui.passo(1, 3, "Selecionar arquivo(s)")
            arquivos = nav.solicitar_arquivos_convertiveis(
                "Selecione os arquivos para converter (ordem = ordem no PDF)"
            )
            ui.passo(2, 3, "Como gerar os PDFs")
            juntar = ui.menu_opcoes(
                "Como converter os arquivos selecionados?",
                [
                    ("1", "Unir todos em um único PDF"),
                    ("2", "Gerar um PDF separado para cada arquivo"),
                ],
                padrao="1",
            ) == "1"
            if juntar:
                ui.passo(3, 3, "Definir PDF de saída")
                if len(arquivos) == 1:
                    nome_padrao = f"{Path(arquivos[0]).stem}.pdf"
                    rotulo_padrao = f"Salvar como {nome_padrao} na mesma pasta"
                else:
                    nome_padrao = "documento_convertido.pdf"
                    rotulo_padrao = f"Salvar como {nome_padrao} na pasta do 1º arquivo"
                saida = nav.solicitar_salvar_pdf(
                    "Salvar PDF como",
                    nome_sugerido=nome_padrao,
                    diretorio_inicial=Path(arquivos[0]).parent,
                    permitir_padrao=True,
                    rotulo_padrao=rotulo_padrao,
                )
                if saida is None:
                    saida = str(Path(arquivos[0]).parent / nome_padrao)
            else:
                ui.passo(3, 3, "Escolher pasta de saída")
                saida = nav.solicitar_pasta_saida(
                    "Pasta do 1º arquivo",
                    diretorio_inicial=Path(arquivos[0]).parent,
                )
            ui.info("Convertendo...")
            _mostrar_resultado(operacao_converter_arquivos(arquivos, saida, juntar_em_um=juntar))
        else:
            ui.passo(1, 3, "Selecionar pasta com os arquivos")
            pasta = nav.solicitar_pasta("Selecione a pasta com os arquivos")
            ui.passo(2, 3, "Escolher pasta de saída")
            pasta_saida = nav.solicitar_pasta_saida("Mesma pasta dos arquivos", diretorio_inicial=pasta)
            ui.passo(3, 3, "Opções para imagens")
            juntar = ui.menu_opcoes(
                "Como converter imagens encontradas na pasta?",
                [
                    ("1", "Unir todas em um único PDF (imagens.pdf)"),
                    ("2", "Gerar um PDF separado para cada imagem"),
                ],
                padrao="1",
            ) == "1"
            ui.info("Convertendo arquivos...")
            _mostrar_resultado(operacao_converter_pasta(pasta, pasta_saida, juntar))
    except OperacaoCancelada:
        ui.mensagem_aviso("Operação cancelada.")
    except RuntimeError as e:
        ui.mensagem_erro(str(e))
        if MSG_LIBREOFFICE.split(".")[0] in str(e):
            ui.info(MSG_LIBREOFFICE)
    except Exception as e:
        ui.mensagem_erro(str(e))
    finally:
        _finalizar_operacao()


def executar_extrair_paginas() -> None:
    ui.secao("Extrair páginas específicas")
    ui.info("Informe páginas como: 1,3,5-10 (a ordem informada será mantida).")
    try:
        ui.passo(1, 3, "Selecionar o PDF")
        arquivo = nav.solicitar_arquivo_pdf("Selecione o PDF de origem")
        total = obter_total_paginas(arquivo)
        ui.passo(2, 3, "Informar páginas a extrair")
        paginas = nav.solicitar_intervalo_paginas(total, permitir_todas=False)
        ui.passo(3, 3, "Definir PDF de saída")
        stem = Path(arquivo).stem
        saida = nav.solicitar_salvar_pdf(
            "Salvar páginas extraídas como",
            nome_sugerido=f"{stem}_paginas.pdf",
            diretorio_inicial=Path(arquivo).parent,
            permitir_padrao=True,
            rotulo_padrao=f"Salvar como {stem}_paginas.pdf na mesma pasta",
        )
        if saida is None:
            saida = str(Path(arquivo).parent / f"{stem}_paginas.pdf")
        ui.info("Extraindo páginas...")
        _mostrar_resultado(operacao_extrair_paginas(arquivo, paginas, saida))
    except OperacaoCancelada:
        ui.mensagem_aviso("Operação cancelada.")
    except Exception as e:
        ui.mensagem_erro(str(e))
    finally:
        _finalizar_operacao()


def executar_rotacionar_paginas() -> None:
    ui.secao("Rotacionar páginas")
    try:
        ui.passo(1, 4, "Selecionar o PDF")
        arquivo = nav.solicitar_arquivo_pdf("Selecione o PDF")
        total = obter_total_paginas(arquivo)
        ui.passo(2, 4, "Escolher páginas")
        paginas = nav.solicitar_intervalo_paginas(total, permitir_todas=True)
        ui.passo(3, 4, "Escolher rotação")
        opcao = ui.menu_opcoes(
            "Girar em qual sentido?",
            [("1", "90° horário"), ("2", "90° anti-horário"), ("3", "180°")],
            padrao="1",
        )
        angulos = {"1": 90, "2": -90, "3": 180}
        ui.passo(4, 4, "Definir PDF de saída")
        stem = Path(arquivo).stem
        saida = nav.solicitar_salvar_pdf(
            "Salvar PDF rotacionado como",
            nome_sugerido=f"{stem}_rotacionado.pdf",
            diretorio_inicial=Path(arquivo).parent,
            permitir_padrao=True,
            rotulo_padrao=f"Salvar como {stem}_rotacionado.pdf na mesma pasta",
        )
        if saida is None:
            saida = str(Path(arquivo).parent / f"{stem}_rotacionado.pdf")
        ui.info("Rotacionando...")
        _mostrar_resultado(operacao_rotacionar(arquivo, angulos[opcao], saida, paginas))
    except OperacaoCancelada:
        ui.mensagem_aviso("Operação cancelada.")
    except Exception as e:
        ui.mensagem_erro(str(e))
    finally:
        _finalizar_operacao()


def executar_comprimir_pdf() -> None:
    ui.secao("Comprimir / reduzir tamanho do PDF")
    try:
        ui.passo(1, 3, "Selecionar o PDF")
        arquivo = nav.solicitar_arquivo_pdf("Selecione o PDF para comprimir")
        ui.passo(2, 3, "Escolher nível de compressão")
        nivel_opcao = ui.menu_opcoes(
            "Nível de compressão",
            [
                ("1", "Leve — menor redução, melhor qualidade"),
                ("2", "Médio — equilíbrio (recomendado)"),
                ("3", "Forte — maior redução, pode afetar imagens"),
            ],
            padrao="2",
        )
        niveis = {"1": "leve", "2": "medio", "3": "forte"}
        ui.passo(3, 3, "Definir PDF de saída")
        stem = Path(arquivo).stem
        saida = nav.solicitar_salvar_pdf(
            "Salvar PDF comprimido como",
            nome_sugerido=f"{stem}_comprimido.pdf",
            diretorio_inicial=Path(arquivo).parent,
            permitir_padrao=True,
            rotulo_padrao=f"Salvar como {stem}_comprimido.pdf na mesma pasta",
        )
        if saida is None:
            saida = str(Path(arquivo).parent / f"{stem}_comprimido.pdf")
        ui.info("Comprimindo...")
        _mostrar_resultado(operacao_comprimir(arquivo, saida, nivel=niveis[nivel_opcao]))
    except OperacaoCancelada:
        ui.mensagem_aviso("Operação cancelada.")
    except Exception as e:
        ui.mensagem_erro(str(e))
    finally:
        _finalizar_operacao()


def menu_console() -> None:
    opcoes = [
        ("1", "Dividir PDF (a cada N páginas)", executar_dividir_por_paginas),
        ("2", "Dividir PDF (em N partes iguais)", executar_dividir_em_partes),
        ("3", "Juntar PDFs", executar_juntar),
        ("4", "Traduzir PDF (Google Translate)", executar_traduzir),
        ("5", "Traduzir PDF (original + tradução, 2 colunas)", executar_traduzir_2colunas),
        ("6", "Converter arquivos para PDF", executar_converter_para_pdf),
        ("7", "Extrair páginas específicas", executar_extrair_paginas),
        ("8", "Rotacionar páginas", executar_rotacionar_paginas),
        ("9", "Comprimir / reduzir tamanho", executar_comprimir_pdf),
        ("0", "Sair", None),
    ]
    ui.definir_titulo_janela(titulo_com_versao())
    while True:
        ui.caixa_titulo(titulo_com_versao())
        print(f"  {ui.C_SUBTIL}Escolha uma operação:{ui.C_RESET}")
        print()
        for codigo, texto, _ in opcoes:
            print(f"    {ui.C_OPCAO}{codigo}.{ui.C_RESET} {texto}")
        print()
        escolha = input(f"  Opção [{ui.C_OPCAO}0{ui.C_RESET}-{ui.C_OPCAO}9{ui.C_RESET}]: ").strip()
        for codigo, _, funcao in opcoes:
            if escolha == codigo:
                if funcao is None:
                    print()
                    ui.mensagem_ok("Até logo!")
                    print()
                    return
                funcao()
                break
        else:
            ui.mensagem_aviso("Opção inválida. Escolha um número de 0 a 9.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manipulador de arquivos PDF")
    parser.add_argument(
        "--version",
        action="version",
        version=linha_versao(),
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Usar interface em terminal em vez da interface gráfica",
    )
    args = parser.parse_args()

    if args.console:
        menu_console()
    else:
        from interface_grafica import iniciar_aplicacao
        iniciar_aplicacao()


if __name__ == "__main__":
    main()
