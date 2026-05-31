# -*- coding: utf-8 -*-
"""Navegação padronizada: diálogos do Windows, menus e validação de caminhos."""

from pathlib import Path

import interface_console as ui
from seletor_arquivos import (
    abrir_pasta_explorador,
    dialogos_disponiveis,
    salvar_arquivo_pdf,
    selecionar_arquivo_convertivel,
    selecionar_arquivos_convertiveis,
    selecionar_arquivo_pdf,
    selecionar_arquivos_pdf,
    selecionar_pasta,
)


class OperacaoCancelada(Exception):
    """Levantada quando o usuário cancela uma operação."""


def _caminho_manual(mensagem: str, deve_existir: bool = True) -> str:
    while True:
        valor = ui.pergunta(mensagem)
        if not valor:
            ui.mensagem_aviso("O caminho não pode ficar vazio.")
            continue
        caminho = Path(valor)
        if deve_existir and not caminho.exists():
            ui.mensagem_erro(f"Caminho não encontrado: {caminho}")
            continue
        return str(caminho.resolve())


def _validar_pdf(caminho_str: str) -> str | None:
    caminho = Path(caminho_str)
    if caminho.is_dir():
        ui.mensagem_aviso("Selecione um arquivo PDF, não uma pasta.")
        return None
    if not caminho.is_file():
        ui.mensagem_erro("Informe um arquivo PDF válido.")
        return None
    if caminho.suffix.lower() != ".pdf":
        alternativo = caminho.with_suffix(".pdf")
        if alternativo.exists():
            return str(alternativo.resolve())
    return str(caminho.resolve())


def _dialogo_ou_manual(
    abrir_dialogo,
    rotulo_manual: str,
    titulo_dialogo: str,
) -> str | None:
    """Abre diálogo repetidamente; permite digitação manual ou cancelamento."""
    while True:
        ui.info("Abrindo janela de seleção do Windows...")
        resultado = abrir_dialogo()
        if resultado:
            return resultado

        acao = ui.acoes_cancelamento_dialogo()
        if acao == "1":
            continue
        if acao == "2":
            return _caminho_manual(rotulo_manual)
        return None


def solicitar_arquivos_convertiveis(
    titulo_dialogo: str = "Selecione os arquivos para converter",
    diretorio_inicial: str | Path | None = None,
) -> list[str]:
    """Solicita um ou mais arquivos convertíveis, preservando a ordem de seleção."""
    from converter_para_pdf import arquivo_e_convertivel

    lista: list[str] = []

    if dialogos_disponiveis():
        ui.info("Dica: selecione na ordem desejada (Ctrl+clique). A ordem define o PDF final.")
        while True:
            ui.info("Abrindo janela de seleção do Windows...")
            novos = selecionar_arquivos_convertiveis(titulo_dialogo, diretorio_inicial)
            if novos:
                for caminho in novos:
                    p = Path(caminho).resolve()
                    if not arquivo_e_convertivel(p):
                        ui.mensagem_aviso(f"Ignorado (formato não suportado): {p.name}")
                        continue
                    caminho_str = str(p)
                    if caminho_str not in lista:
                        lista.append(caminho_str)
                if lista:
                    _mostrar_ordem_selecao(lista)
                    if ui.confirmar("Adicionar mais arquivos ao final da lista?", padrao_sim=False):
                        continue
                break

            if lista:
                break

            acao = ui.acoes_cancelamento_dialogo()
            if acao == "1":
                continue
            if acao == "2":
                manual = _caminho_manual("Digite o caminho de um arquivo")
                p = Path(manual).resolve()
                if p.is_file() and arquivo_e_convertivel(p):
                    lista.append(str(p))
                    break
                ui.mensagem_erro("Arquivo inválido ou formato não suportado.")
                continue
            raise OperacaoCancelada()

        if not lista:
            raise OperacaoCancelada()
        return lista

    ui.info("Informe um caminho por vez. Linha vazia para concluir. A ordem informada será mantida.")
    while True:
        caminho = ui.pergunta(f"Arquivo #{len(lista) + 1} (Enter para concluir)")
        if not caminho:
            break
        p = Path(caminho).resolve()
        if p.is_file() and arquivo_e_convertivel(p):
            caminho_str = str(p)
            if caminho_str not in lista:
                lista.append(caminho_str)
                ui.mensagem_ok(f"Adicionado ({len(lista)}): {p.name}")
        else:
            ui.mensagem_erro("Arquivo inválido ou formato não suportado.")

    if not lista:
        raise OperacaoCancelada()
    _mostrar_ordem_selecao(lista)
    return lista


def _mostrar_ordem_selecao(arquivos: list[str]) -> None:
    print()
    print(f"  {ui.C_DESTAQUE}Ordem no PDF final:{ui.C_RESET}")
    for i, caminho in enumerate(arquivos, 1):
        print(f"    {ui.C_OPCAO}{i}.{ui.C_RESET} {Path(caminho).name}")
    print()


def solicitar_arquivo_convertivel(
    titulo_dialogo: str = "Selecione o arquivo para converter",
    diretorio_inicial: str | Path | None = None,
) -> str:
    """Solicita um arquivo convertível para PDF."""
    from converter_para_pdf import arquivo_e_convertivel

    if dialogos_disponiveis():
        caminho = _dialogo_ou_manual(
            lambda: selecionar_arquivo_convertivel(titulo_dialogo, diretorio_inicial),
            "Digite o caminho completo do arquivo",
            titulo_dialogo,
        )
    else:
        caminho = _caminho_manual("Caminho do arquivo")

    if not caminho:
        raise OperacaoCancelada()

    arquivo = Path(caminho)
    if not arquivo.is_file():
        ui.mensagem_erro("Informe um arquivo válido.")
        raise OperacaoCancelada()
    if not arquivo_e_convertivel(arquivo):
        ui.mensagem_erro(f"Formato não suportado: {arquivo.suffix}")
        raise OperacaoCancelada()

    ui.mensagem_ok(f"Arquivo: {arquivo.name}")
    return str(arquivo.resolve())


def solicitar_arquivo_pdf(
    titulo_dialogo: str = "Selecione um arquivo PDF",
    diretorio_inicial: str | Path | None = None,
) -> str:
    """Solicita um PDF. Levanta OperacaoCancelada se o usuário desistir."""
    if dialogos_disponiveis():
        caminho = _dialogo_ou_manual(
            lambda: selecionar_arquivo_pdf(titulo_dialogo, diretorio_inicial),
            "Digite o caminho completo do PDF",
            titulo_dialogo,
        )
    else:
        caminho = _caminho_manual("Caminho do PDF")

    if not caminho:
        raise OperacaoCancelada()

    validado = _validar_pdf(caminho)
    if not validado:
        raise OperacaoCancelada()

    ui.mensagem_ok(f"Arquivo: {Path(validado).name}")
    return validado


def solicitar_pasta(
    titulo_dialogo: str = "Selecione uma pasta",
    diretorio_inicial: str | Path | None = None,
) -> str:
    """Solicita uma pasta existente."""
    if dialogos_disponiveis():
        caminho = _dialogo_ou_manual(
            lambda: selecionar_pasta(titulo_dialogo, diretorio_inicial),
            "Digite o caminho completo da pasta",
            titulo_dialogo,
        )
    else:
        caminho = _caminho_manual("Caminho da pasta")

    if not caminho:
        raise OperacaoCancelada()

    pasta = Path(caminho)
    if not pasta.is_dir():
        ui.mensagem_erro("Informe uma pasta válida.")
        raise OperacaoCancelada()

    ui.mensagem_ok(f"Pasta: {pasta.name}")
    return str(pasta.resolve())


def solicitar_pasta_saida(
    rotulo_padrao: str = "Mesma pasta do arquivo original",
    diretorio_inicial: str | Path | None = None,
) -> str | None:
    """Retorna pasta de saída ou None para usar o padrão."""
    if dialogos_disponiveis():
        opcao = ui.menu_opcoes(
            "Onde salvar os arquivos gerados?",
            [
                ("1", rotulo_padrao),
                ("2", "Escolher outra pasta..."),
            ],
            padrao="1",
        )
        if opcao == "1":
            ui.mensagem_ok(rotulo_padrao)
            return None

        while True:
            ui.info("Abrindo janela de seleção de pasta...")
            pasta = selecionar_pasta("Selecione a pasta de saída", diretorio_inicial)
            if pasta:
                ui.mensagem_ok(f"Pasta de saída: {Path(pasta).name}")
                return str(Path(pasta).resolve())
            acao = ui.acoes_cancelamento_dialogo()
            if acao == "1":
                continue
            if acao == "2":
                manual = _caminho_manual("Digite o caminho da pasta de saída")
                if Path(manual).is_dir():
                    return manual
                ui.mensagem_erro("A pasta informada não é válida.")
                continue
            ui.mensagem_ok(rotulo_padrao)
            return None

    pasta = ui.pergunta(f"Pasta de saída (Enter = {rotulo_padrao.lower()})", "")
    return str(Path(pasta).resolve()) if pasta else None


def solicitar_salvar_pdf(
    titulo: str,
    nome_sugerido: str = "documento.pdf",
    diretorio_inicial: str | Path | None = None,
    permitir_padrao: bool = False,
    rotulo_padrao: str = "",
) -> str | None:
    """Solicita destino para salvar PDF. None = usar padrão ou cancelado."""
    if dialogos_disponiveis():
        if permitir_padrao:
            opcao = ui.menu_opcoes(
                titulo,
                [
                    ("1", rotulo_padrao),
                    ("2", "Escolher nome e pasta..."),
                ],
                padrao="1",
            )
            if opcao == "1":
                ui.mensagem_ok(rotulo_padrao)
                return None

        while True:
            ui.info("Abrindo janela 'Salvar como'...")
            caminho = salvar_arquivo_pdf(titulo, nome_sugerido, diretorio_inicial)
            if caminho:
                ui.mensagem_ok(f"Salvar em: {Path(caminho).name}")
                return str(Path(caminho).resolve())
            acao = ui.acoes_cancelamento_dialogo()
            if acao == "1":
                continue
            if acao == "2":
                manual = ui.pergunta("Digite o caminho completo do PDF de saída")
                if manual:
                    destino = Path(manual)
                    if destino.suffix.lower() != ".pdf":
                        destino = destino.with_suffix(".pdf")
                    return str(destino.resolve())
                continue
            return None

    caminho = ui.pergunta(titulo)
    if not caminho:
        return None if permitir_padrao else None
    destino = Path(caminho)
    if destino.suffix.lower() != ".pdf":
        destino = destino.with_suffix(".pdf")
    return str(destino.resolve())


def solicitar_arquivos_pdf(
    titulo_dialogo: str = "Selecione PDFs para juntar",
    diretorio_inicial: str | Path | None = None,
) -> list[str]:
    """Solicita um ou mais PDFs. Levanta OperacaoCancelada se desistir."""
    lista: list[str] = []

    if dialogos_disponiveis():
        ui.info("Dica: use Ctrl+clique para selecionar vários arquivos.")
        while True:
            ui.info("Abrindo janela de seleção do Windows...")
            novos = selecionar_arquivos_pdf(titulo_dialogo, diretorio_inicial)
            if novos:
                for caminho in novos:
                    p = Path(caminho)
                    if p.suffix.lower() != ".pdf":
                        ui.mensagem_aviso(f"Ignorado (não é PDF): {p.name}")
                        continue
                    if str(p.resolve()) not in lista:
                        lista.append(str(p.resolve()))
                ui.resumo_selecao(f"PDFs selecionados ({len(lista)})", lista)
                if ui.confirmar("Adicionar mais arquivos?", padrao_sim=False):
                    continue
                break

            if lista:
                break

            acao = ui.acoes_cancelamento_dialogo()
            if acao == "1":
                continue
            if acao == "2":
                manual = _caminho_manual("Digite o caminho de um PDF")
                validado = _validar_pdf(manual)
                if validado and validado not in lista:
                    lista.append(validado)
                    break
                continue
            raise OperacaoCancelada()

        return lista

    ui.info("Informe um caminho por vez. Linha vazia para concluir.")
    while True:
        caminho = ui.pergunta(f"PDF #{len(lista) + 1} (Enter para concluir)")
        if not caminho:
            break
        validado = _validar_pdf(caminho)
        if validado and validado not in lista:
            lista.append(validado)
            ui.mensagem_ok(f"Adicionado: {Path(validado).name}")

    if not lista:
        raise OperacaoCancelada()
    return lista


def solicitar_inteiro(
    mensagem: str,
    minimo: int = 1,
    maximo: int | None = None,
    padrao: int | None = None,
) -> int:
    rotulo = mensagem
    if padrao is not None:
        rotulo = f"{mensagem} [{padrao}]"
    while True:
        try:
            entrada = input(f"  {rotulo}: ").strip()
            valor = padrao if not entrada and padrao is not None else int(entrada)
            if valor < minimo:
                ui.mensagem_aviso(f"Informe um número >= {minimo}.")
                continue
            if maximo is not None and valor > maximo:
                ui.mensagem_aviso(f"Informe um número <= {maximo}.")
                continue
            return valor
        except ValueError:
            ui.mensagem_aviso("Digite um número inteiro válido.")


def solicitar_intervalo_paginas(
    total_paginas: int,
    permitir_todas: bool = False,
) -> list[int] | None:
    """
    Solicita páginas ao usuário (ex: 1,3,5-8).
    Retorna índices 0-based ou None se todas as páginas (quando permitido).
    """
    from editar_pdf import interpretar_paginas

    dica = f"O PDF tem {total_paginas} página(s)."
    if permitir_todas:
        ui.info(f"{dica} Informe páginas (ex: 1,3,5-8) ou Enter para todas.")
        entrada = ui.pergunta("Páginas")
        if not entrada.strip():
            return None
    else:
        ui.info(f"{dica} Informe páginas (ex: 1,3,5-8).")
        entrada = ui.pergunta("Páginas")

    while True:
        try:
            return interpretar_paginas(entrada, total_paginas)
        except ValueError as e:
            ui.mensagem_erro(str(e))
            entrada = ui.pergunta("Páginas")


def mostrar_resultado(
    titulo: str,
    pasta: Path,
    arquivos: list[str],
    mensagem_vazio: str = "",
    oferecer_abrir_pasta: bool = True,
) -> None:
    """Exibe resultado e pergunta se deseja abrir a pasta no Explorador."""
    ui.caixa_resultado(titulo, pasta.resolve(), arquivos, mensagem_vazio)
    if oferecer_abrir_pasta and arquivos and dialogos_disponiveis():
        escolha = ui.menu_opcoes(
            "Deseja abrir a pasta dos arquivos gerados?",
            [
                ("1", "Abrir pasta no Explorador"),
                ("2", "Não abrir — continuar"),
            ],
            padrao="2",
        )
        if escolha == "1":
            try:
                abrir_pasta_explorador(pasta)
            except Exception as e:
                ui.mensagem_erro(f"Não foi possível abrir a pasta: {e}")
