# -*- coding: utf-8 -*-
"""Componentes visuais padronizados para o terminal."""

import os
import sys
from pathlib import Path

from constantes import titulo_com_versao
LARGURA_MIN = 60
LARGURA_MAX = 120

C_RESET = "\033[0m"
C_TITULO = "\033[1;36m"
C_SUCESSO = "\033[1;32m"
C_AVISO = "\033[1;33m"
C_ERRO = "\033[1;31m"
C_DESTAQUE = "\033[1;37m"
C_OPCAO = "\033[1;93m"
C_SUBTIL = "\033[0;90m"


def definir_titulo_janela(titulo: str) -> None:
    """Define o texto da barra de título do terminal."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(titulo)
        except Exception:
            pass
    else:
        try:
            print(f"\033]0;{titulo}\007", end="", flush=True)
        except Exception:
            pass


def largura_tela() -> int:
    try:
        cols = os.get_terminal_size().columns
        return max(LARGURA_MIN, min(LARGURA_MAX, cols - 4))
    except Exception:
        return 70


def _linha(simbolo: str = "═", largura: int | None = None) -> str:
    w = largura if largura is not None else largura_tela()
    return simbolo * w


def caixa_titulo(titulo: str = titulo_com_versao()) -> None:
    w = largura_tela()
    texto = f" {titulo} "
    print()
    print(f"{C_TITULO}╔{_linha('═', w)}╗{C_RESET}")
    espacos = w - len(texto)
    esq, dir_ = max(0, espacos // 2), max(0, espacos - espacos // 2)
    print(f"{C_TITULO}║{C_RESET}{' ' * esq}{C_DESTAQUE}{texto.strip()}{C_RESET}{' ' * dir_}{C_TITULO}║{C_RESET}")
    print(f"{C_TITULO}╚{_linha('═', w)}╝{C_RESET}")
    print()


def secao(titulo: str) -> None:
    print()
    print(f"  {C_TITULO}▸ {titulo}{C_RESET}")
    print(f"  {_linha('─', largura_tela())}")
    print()


def passo(numero: int, total: int, descricao: str) -> None:
    """Exibe o indicador de progresso do fluxo atual."""
    print()
    print(f"  {C_SUBTIL}Passo {numero}/{total}{C_RESET}  {C_DESTAQUE}{descricao}{C_RESET}")


def info(texto: str) -> None:
    print(f"  {C_SUBTIL}{texto}{C_RESET}")


def mensagem_ok(texto: str) -> None:
    print(f"  {C_SUCESSO}✓{C_RESET} {texto}")


def mensagem_aviso(texto: str) -> None:
    print(f"  {C_AVISO}⚠{C_RESET} {texto}")


def mensagem_erro(texto: str) -> None:
    print(f"  {C_ERRO}✗{C_RESET} {texto}")


def pergunta(rotulo: str, default: str = "") -> str:
    if default:
        return input(f"  {rotulo} [{default}]: ").strip().strip('"') or default
    return input(f"  {rotulo}: ").strip().strip('"')


def menu_opcoes(
    titulo: str,
    opcoes: list[tuple[str, str]],
    padrao: str = "1",
    dica: str = "",
) -> str:
    """Exibe menu numerado padronizado e retorna o código escolhido."""
    print()
    print(f"  {C_DESTAQUE}{titulo}{C_RESET}")
    for codigo, texto in opcoes:
        destaque = f" {C_SUBTIL}(padrão){C_RESET}" if codigo == padrao else ""
        print(f"    {C_OPCAO}{codigo}.{C_RESET} {texto}{destaque}")
    if dica:
        print(f"  {C_SUBTIL}{dica}{C_RESET}")
    codigos = {c for c, _ in opcoes}
    while True:
        escolha = input(f"  Opção [{padrao}]: ").strip() or padrao
        if escolha in codigos:
            return escolha
        mensagem_aviso(f"Opção inválida. Escolha: {', '.join(sorted(codigos))}.")


def confirmar(pergunta_texto: str, padrao_sim: bool = False) -> bool:
    padrao = "S" if padrao_sim else "N"
    resposta = pergunta(pergunta_texto, padrao)
    return resposta.lower() in ("s", "sim", "y", "yes")


def acoes_cancelamento_dialogo() -> str:
    """
    Exibe opções após cancelamento de diálogo.
    Retorna: 'retry', 'manual' ou 'cancelar'.
    """
    print()
    mensagem_aviso("Seleção cancelada na janela do Windows.")
    return menu_opcoes(
        "O que deseja fazer?",
        [
            ("1", "Tentar novamente"),
            ("2", "Digitar caminho manualmente"),
            ("0", "Cancelar operação"),
        ],
        padrao="1",
    )


def aguardar_enter(mensagem: str = "Pressione Enter para voltar ao menu...") -> None:
    print()
    input(f"  {C_SUBTIL}{mensagem}{C_RESET}")


def _linha_interior(texto: str, w: int) -> str:
    if len(texto) >= w:
        return texto[:w]
    return texto + " " * (w - len(texto))


def caixa_resultado(titulo: str, pasta: Path, arquivos: list[str], mensagem_vazio: str = "") -> None:
    w = largura_tela()
    print()
    print(f"  {C_SUCESSO}╔{_linha('═', w)}╗{C_RESET}")
    espacos = w - len(titulo)
    esq, dir_ = max(0, espacos // 2), max(0, espacos - espacos // 2)
    print(f"  {C_SUCESSO}║{C_RESET}{' ' * esq}{C_DESTAQUE}{titulo}{C_RESET}{' ' * dir_}{C_SUCESSO}║{C_RESET}")
    print(f"  {C_SUCESSO}╠{_linha('═', w)}╣{C_RESET}")
    path_str = str(pasta.resolve())
    max_path = w - 2
    path_display = (path_str[: max_path - 3] + "...") if len(path_str) > max_path else path_str
    print(f"  {C_SUCESSO}║{C_RESET}{_linha_interior('  Pasta: ' + path_display, w)}{C_SUCESSO}║{C_RESET}")
    print(f"  {C_SUCESSO}║{C_RESET}{_linha_interior('', w)}{C_SUCESSO}║{C_RESET}")
    if arquivos:
        print(f"  {C_SUCESSO}║{C_RESET}{_linha_interior(f'  Arquivos ({len(arquivos)}):', w)}{C_SUCESSO}║{C_RESET}")
        for p in arquivos:
            nome = Path(p).name
            if len(nome) > w - 6:
                nome = "..." + nome[-(w - 9):]
            print(f"  {C_SUCESSO}║{C_RESET}{_linha_interior('    • ' + nome, w)}{C_SUCESSO}║{C_RESET}")
    else:
        msg = mensagem_vazio or "Nenhum arquivo gerado."
        print(f"  {C_SUCESSO}║{C_RESET}{_linha_interior('  ' + msg, w)}{C_SUCESSO}║{C_RESET}")
    print(f"  {C_SUCESSO}╚{_linha('═', w)}╝{C_RESET}")
    print()


def resumo_selecao(titulo: str, itens: list[str]) -> None:
    """Lista compacta de arquivos/pastas selecionados antes de continuar."""
    if not itens:
        return
    print()
    print(f"  {C_DESTAQUE}{titulo}{C_RESET}")
    for item in itens:
        nome = Path(item).name
        print(f"    {C_SUCESSO}•{C_RESET} {nome}")
    print()
