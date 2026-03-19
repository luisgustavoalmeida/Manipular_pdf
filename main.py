# -*- coding: utf-8 -*-
"""
Programa principal para manipulação de arquivos PDF.
Permite: dividir (por páginas ou em N partes), juntar e traduzir PDFs.
"""

import json
import os
import sys
from pathlib import Path

# Ajusta encoding do console no Windows para exibir acentos corretamente
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        # Habilita cores ANSI no terminal do Windows (10+)
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

# Permite importar módulos do projeto quando executado como script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dividir_pdf import dividir_em_partes, dividir_por_paginas
from juntar_pdf import juntar_pdfs
from traduzir_pdf import criar_pdf_duas_colunas, traduzir_pdf

# --- Interface amigável (caixas, cores, ícones) ---
TITULO_APLICACAO = " --- Manipulador PDF --- "
LARGURA_MIN = 60
LARGURA_MAX = 120
C_RESET = "\033[0m"
C_TITULO = "\033[1;36m"   # negrito ciano
C_SUCESSO = "\033[1;32m"  # negrito verde
C_AVISO = "\033[1;33m"    # negrito amarelo
C_ERRO = "\033[1;31m"     # negrito vermelho
C_DESTAQUE = "\033[1;37m" # negrito branco
C_OPCAO = "\033[1;93m"    # amarelo claro — destaque para números das opções


def _definir_titulo_janela(titulo: str) -> None:
    """Define o texto da barra de título do CMD/terminal."""
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(titulo)
        except Exception:
            pass
    else:
        try:
            print(f"\033]0;{titulo}\007", end="", flush=True)
        except Exception:
            pass


def _largura_tela() -> int:
    """Retorna a largura interior da caixa (entre ║ e ║). Cada linha = '  ' + '║' + w + '║' = cols."""
    try:
        cols = os.get_terminal_size().columns
        # 2 (indent) + 1 (║) + w + 1 (║) = cols  =>  w = cols - 4
        w = cols - 4
        return max(LARGURA_MIN, min(LARGURA_MAX, w))
    except Exception:
        return 70


def _linha(simbolo: str = "═", largura: int | None = None) -> str:
    w = largura if largura is not None else _largura_tela()
    return simbolo * w


def _caixa_titulo(titulo: str) -> None:
    """Imprime cabeçalho em caixa ocupando toda a largura útil do terminal."""
    w = _largura_tela()
    print()
    print(f"{C_TITULO}╔{_linha('═', w)}╗{C_RESET}")
    # Largura interior da caixa = w (entre ║ e ║). Título centralizado nesse espaço.
    espacos = w - len(titulo)
    esq = max(0, espacos // 2)
    dir_ = max(0, espacos - esq)
    print(f"{C_TITULO}║{C_RESET}{' ' * esq}{C_DESTAQUE}{titulo}{C_RESET}{' ' * dir_}{C_TITULO}║{C_RESET}")
    print(f"{C_TITULO}╚{_linha('═', w)}╝{C_RESET}")
    print()


def _secao(titulo: str) -> None:
    """Imprime o título de uma seção (submenu) com estilo simples."""
    print()
    print(f"  {C_TITULO}▸ {titulo}{C_RESET}")
    print(f"  {_linha('─', _largura_tela())}")
    print()


def _mensagem_ok(texto: str) -> None:
    print(f"  {C_SUCESSO}✓{C_RESET} {texto}")


def _mensagem_aviso(texto: str) -> None:
    print(f"  {C_AVISO}⚠{C_RESET} {texto}")


def _mensagem_erro(texto: str) -> None:
    print(f"  {C_ERRO}✗{C_RESET} {texto}")


def _pergunta(rotulo: str, default: str = "") -> str:
    """Retorna o texto digitado; se default, mostra entre colchetes."""
    if default:
        return input(f"  {rotulo} [{default}]: ").strip().strip('"') or default
    return input(f"  {rotulo}: ").strip().strip('"')


def _caixa_resultado(titulo: str, pasta: Path, arquivos: list[str], mensagem_vazio: str = "") -> None:
    """Mostra resultado em caixa: título, pasta e lista de arquivos. Cada linha tem largura interior = w."""
    w = _largura_tela()

    def linha_interior(texto: str) -> str:
        """Preenche com espaços à direita até completar w caracteres."""
        if len(texto) >= w:
            return texto[:w]
        return texto + " " * (w - len(texto))

    print()
    print(f"  {C_SUCESSO}╔{_linha('═', w)}╗{C_RESET}")
    espacos = w - len(titulo)
    esq, dir_ = max(0, espacos // 2), max(0, espacos - espacos // 2)
    print(f"  {C_SUCESSO}║{C_RESET}{' ' * esq}{C_DESTAQUE}{titulo}{C_RESET}{' ' * dir_}{C_SUCESSO}║{C_RESET}")
    print(f"  {C_SUCESSO}╠{_linha('═', w)}╣{C_RESET}")
    path_str = str(pasta.resolve())
    max_path = w - 2
    path_display = (path_str[: max_path - 3] + "...") if len(path_str) > max_path else path_str
    print(f"  {C_SUCESSO}║{C_RESET}{linha_interior('  ' + path_display)}{C_SUCESSO}║{C_RESET}")
    print(f"  {C_SUCESSO}║{C_RESET}{linha_interior('')}{C_SUCESSO}║{C_RESET}")
    if arquivos:
        print(f"  {C_SUCESSO}║{C_RESET}{linha_interior('  Arquivos gerados (' + str(len(arquivos)) + '):')}{C_SUCESSO}║{C_RESET}")
        for p in arquivos:
            nome = Path(p).name
            if len(nome) > w - 6:
                nome = "..." + nome[-(w - 9) :]
            print(f"  {C_SUCESSO}║{C_RESET}{linha_interior('    • ' + nome)}{C_SUCESSO}║{C_RESET}")
    else:
        print(f"  {C_SUCESSO}║{C_RESET}{linha_interior('  ' + (mensagem_vazio or 'Nenhum arquivo gerado.'))}{C_SUCESSO}║{C_RESET}")
    print(f"  {C_SUCESSO}╚{_linha('═', w)}╝{C_RESET}")
    print()

# Arquivo onde as preferências do usuário são salvas (mesma pasta do programa)
ARQUIVO_CONFIG_USUARIO = Path(__file__).resolve().parent / "config_usuario.json"

# Tradução usa apenas Google Translate.
MOTOR_TRADUCAO_GOOGLE = ("google", "Google Translate")

# Idiomas disponíveis para tradução (código ISO, nome). Um arquivo por idioma na pasta do PDF de origem.
IDIOMAS_DISPONIVEIS = [
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


def _solicitar_caminho(mensagem: str, deve_existir: bool = True) -> str:
    """Solicita um caminho ao usuário até ser válido."""
    while True:
        valor = input(f"  {mensagem} ").strip().strip('"')
        if not valor:
            _mensagem_aviso("Caminho não pode ser vazio.")
            continue
        caminho = Path(valor)
        if deve_existir and not caminho.exists():
            com_pdf = caminho if caminho.suffix.lower() == ".pdf" else caminho.with_suffix(caminho.suffix or ".pdf")
            if com_pdf.exists() and com_pdf.is_file():
                _mensagem_ok(f"Usando arquivo: {com_pdf.name}")
                return str(com_pdf.resolve())
            _mensagem_erro(f"Caminho não encontrado: {caminho}")
            continue
        return str(caminho.resolve())


def _solicitar_arquivo_pdf(mensagem: str) -> str:
    """Solicita o caminho de um arquivo PDF (não aceita pasta)."""
    while True:
        caminho_str = _solicitar_caminho(mensagem)
        caminho = Path(caminho_str)
        if caminho.is_dir():
            _mensagem_aviso("Informe o caminho de um arquivo PDF (ex: arquivo.pdf), não de uma pasta.")
            continue
        if not caminho.is_file():
            _mensagem_erro("O caminho não é um arquivo. Informe um arquivo PDF.")
            continue
        if caminho.suffix.lower() != ".pdf":
            tentar = caminho.with_suffix(".pdf")
            if tentar.exists():
                _mensagem_ok(f"Arquivo encontrado: {tentar.name}")
                return str(tentar.resolve())
            _mensagem_aviso("Arquivo sem extensão .pdf. Continuando mesmo assim.")
        return caminho_str


def _solicitar_inteiro(mensagem: str, minimo: int = 1, maximo: int | None = None) -> int:
    """Solicita um número inteiro dentro do intervalo."""
    while True:
        try:
            valor = int(input(f"  {mensagem} ").strip())
            if valor < minimo:
                _mensagem_aviso(f"Digite um número >= {minimo}.")
                continue
            if maximo is not None and valor > maximo:
                _mensagem_aviso(f"Digite um número <= {maximo}.")
                continue
            return valor
        except ValueError:
            _mensagem_aviso("Digite um número inteiro válido.")


def _carregar_config_usuario() -> dict:
    """Carrega configurações salvas pelo usuário (motor de tradução, etc.)."""
    if ARQUIVO_CONFIG_USUARIO.exists():
        try:
            with open(ARQUIVO_CONFIG_USUARIO, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _salvar_config_usuario(config: dict) -> None:
    """Salva configurações do usuário em config_usuario.json."""
    try:
        with open(ARQUIVO_CONFIG_USUARIO, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Aviso: não foi possível salvar configurações: {e}")


def _mostrar_resumo_pasta_saida(pasta: Path, arquivos_gerados: list[str], titulo: str = "Resultado") -> None:
    """Mostra claramente onde os arquivos foram salvos (evita procurar na pasta errada)."""
    pasta_abs = pasta.resolve()
    msg_vazio = "Nenhum arquivo gerado. Verifique erros acima (rede, etc.)."
    _caixa_resultado(titulo, pasta_abs, arquivos_gerados, msg_vazio)
    if sys.platform == "win32" and arquivos_gerados:
        abrir = _pergunta("Abrir esta pasta no Explorador de Arquivos?", "N")
        if abrir.lower() in ("s", "sim", "y", "yes"):
            try:
                os.startfile(str(pasta_abs))
            except Exception as e:
                _mensagem_erro(f"Não foi possível abrir: {e}")


def executar_dividir_por_paginas() -> None:
    """Fluxo: dividir PDF a cada N páginas."""
    _secao("Dividir PDF — a cada N páginas")
    arquivo = _solicitar_arquivo_pdf("Caminho do PDF")
    paginas = _solicitar_inteiro("Quantas páginas por parte?", minimo=1)
    pasta = _pergunta("Pasta de saída (Enter = mesma pasta do PDF)", "")
    if pasta:
        pasta = str(Path(pasta).resolve())
    else:
        pasta = None
    try:
        lista = dividir_por_paginas(arquivo, paginas, pasta_saida=pasta)
        pasta_saida = Path(lista[0]).parent if lista else Path(arquivo).parent
        _mostrar_resumo_pasta_saida(pasta_saida, lista, "Divisão concluída")
    except Exception as e:
        _mensagem_erro(str(e))


def executar_dividir_em_partes() -> None:
    """Fluxo: dividir PDF em N partes homogêneas."""
    _secao("Dividir PDF — em N partes iguais")
    arquivo = _solicitar_arquivo_pdf("Caminho do PDF")
    partes = _solicitar_inteiro("Em quantas partes dividir?", minimo=1)
    pasta = _pergunta("Pasta de saída (Enter = mesma pasta do PDF)", "")
    if pasta:
        pasta = str(Path(pasta).resolve())
    else:
        pasta = None
    try:
        lista = dividir_em_partes(arquivo, partes, pasta_saida=pasta)
        pasta_saida = Path(lista[0]).parent if lista else Path(arquivo).parent
        _mostrar_resumo_pasta_saida(pasta_saida, lista, "Divisão concluída")
    except Exception as e:
        _mensagem_erro(str(e))


def executar_juntar() -> None:
    """Fluxo: juntar vários PDFs em um."""
    _secao("Juntar PDFs")
    print("  Informe os caminhos dos PDFs (um por linha). Linha vazia para encerrar.")
    print()
    lista = []
    while True:
        caminho = input(f"  PDF #{len(lista) + 1}: ").strip().strip('"')
        if not caminho:
            break
        p = Path(caminho)
        if not p.exists():
            _mensagem_erro(f"Arquivo não encontrado: {p}")
            continue
        lista.append(str(p.resolve()))
        _mensagem_ok(f"Adicionado: {p.name}")
    if not lista:
        _mensagem_aviso("Nenhum arquivo informado.")
        return
    saida = _pergunta("Caminho do PDF de saída", "")
    if not saida:
        _mensagem_aviso("Caminho de saída não informado.")
        return
    saida = str(Path(saida).resolve())
    try:
        resultado = juntar_pdfs(lista, saida)
        print()
        _mensagem_ok(f"Arquivo gerado: {Path(resultado).name}")
        print(f"  {resultado}")
    except Exception as e:
        _mensagem_erro(str(e))


def _traduzir_para_idiomas(
    arquivo: str,
    idiomas: list[tuple[str, str]],
    idioma_origem: str | None,
) -> list[str]:
    """Traduz o PDF para cada idioma usando Google Translate. Salva na mesma pasta do origem. Retorna lista de caminhos gerados."""
    path_entrada = Path(arquivo)
    pasta_origem = path_entrada.parent
    stem = path_entrada.stem
    sufixo = path_entrada.suffix
    codigo_motor, nome_motor = MOTOR_TRADUCAO_GOOGLE
    gerados = []
    for codigo_idioma, nome_idioma in idiomas:
        caminho_saida = pasta_origem / f"{stem}_{codigo_motor}_{codigo_idioma}{sufixo}"
        try:
            resultado = traduzir_pdf(
                arquivo,
                str(caminho_saida),
                idioma_destino=codigo_idioma,
                idioma_origem=idioma_origem,
                provedor=codigo_motor,
            )
            gerados.append(resultado)
            _mensagem_ok(f"{nome_idioma} → {caminho_saida.name}")
        except Exception as e:
            _mensagem_erro(f"{nome_idioma}: {e}")
    return gerados


def _escolher_idiomas() -> list[tuple[str, str]] | None:
    """Pergunta ao usuário: um, vários ou todos os idiomas. Retorna lista de (código, nome) ou None se cancelar."""
    print("  Traduzir para qual(is) idioma(s)?")
    print("    1. Um idioma")
    print("    2. Vários idiomas")
    print("    3. Todos os disponíveis")
    opcao = input("  Opção (1/2/3): ").strip()
    if opcao == "1":
        print("  Idiomas disponíveis (digite o número ou o código):")
        for i, (cod, nome) in enumerate(IDIOMAS_DISPONIVEIS, 1):
            print(f"    {C_OPCAO}{i}.{C_RESET} {nome} ({cod})")
        codigo = _pergunta("Idioma de destino", "pt")
        codigo = codigo.strip()
        # Se digitou um número, converter para código do idioma
        try:
            idx = int(codigo)
            if 1 <= idx <= len(IDIOMAS_DISPONIVEIS):
                codigo, nome = IDIOMAS_DISPONIVEIS[idx - 1]
                return [(codigo, nome)]
        except ValueError:
            pass
        nome = next((n for c, n in IDIOMAS_DISPONIVEIS if c == codigo), codigo)
        return [(codigo, nome)]
    if opcao == "2":
        print("  Idiomas disponíveis:")
        for i, (cod, nome) in enumerate(IDIOMAS_DISPONIVEIS, 1):
            print(f"    {i}. {nome} ({cod})")
        escolha = input("  Números separados por vírgula (ex: 1,3,5): ").strip()
        indices = []
        for s in escolha.replace(" ", "").split(","):
            try:
                n = int(s)
                if 1 <= n <= len(IDIOMAS_DISPONIVEIS):
                    indices.append(n - 1)
            except ValueError:
                pass
        if not indices:
            _mensagem_aviso("Nenhum idioma válido informado.")
            return None
        return [IDIOMAS_DISPONIVEIS[i] for i in sorted(set(indices))]
    if opcao == "3":
        return IDIOMAS_DISPONIVEIS.copy()
    _mensagem_aviso("Opção inválida.")
    return None


def _normalizar_idioma_origem(entrada: str) -> str | None:
    """Converte a resposta do usuário (número ou código) no código do idioma para a API. Retorna None para detecção automática."""
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
    if not codigo and entrada:
        _mensagem_aviso("Idioma de origem não reconhecido; será detectado automaticamente.")
    return codigo if codigo else None


def _escolher_um_idioma() -> tuple[str, str] | None:
    """Pergunta um único idioma de destino. Retorna (código, nome) ou None."""
    print("  Idiomas disponíveis (digite o número ou o código):")
    for i, (cod, nome) in enumerate(IDIOMAS_DISPONIVEIS, 1):
        print(f"    {C_OPCAO}{i}.{C_RESET} {nome} ({cod})")
    codigo = _pergunta("Idioma de destino", "pt").strip()
    try:
        idx = int(codigo)
        if 1 <= idx <= len(IDIOMAS_DISPONIVEIS):
            return IDIOMAS_DISPONIVEIS[idx - 1]
    except ValueError:
        pass
    nome = next((n for c, n in IDIOMAS_DISPONIVEIS if c == codigo), None)
    if nome is None:
        _mensagem_aviso("Idioma não reconhecido.")
        return None
    return (codigo, nome)


def executar_traduzir() -> None:
    """Fluxo: traduzir PDF com Google Translate; escolher idioma(s); arquivos na pasta do origem."""
    _secao("Traduzir PDF (Google Translate)")
    print("  Informe o caminho completo do arquivo .pdf (ex: C:\\pasta\\arquivo.pdf).")
    print()
    arquivo = _solicitar_arquivo_pdf("Caminho do PDF")
    path_entrada = Path(arquivo)
    pasta_origem = path_entrada.parent
    _mensagem_ok(f"Os traduzidos serão salvos em: {pasta_origem.resolve()}")
    print()
    idiomas = _escolher_idiomas()
    if not idiomas:
        return
    entrada_origem = _pergunta("Idioma de origem (Enter = detectar automaticamente)", "")
    idioma_origem = _normalizar_idioma_origem(entrada_origem)
    total = len(idiomas)
    print()
    print(f"  {C_TITULO}Traduzindo {total} arquivo(s)...{C_RESET}")
    print()
    try:
        gerados = _traduzir_para_idiomas(arquivo, idiomas, idioma_origem)
        _mostrar_resumo_pasta_saida(pasta_origem, gerados, "Tradução concluída")
    except Exception as e:
        _mensagem_erro(str(e))
        _mostrar_resumo_pasta_saida(pasta_origem, [], "Tradução (erro)")


def executar_traduzir_2colunas() -> None:
    """Traduz o PDF e gera um novo PDF com 2 colunas: original (esquerda) e tradução (direita)."""
    _secao("Traduzir PDF — Original + Tradução em 2 colunas")
    print("  Gera um PDF para leitura lado a lado: coluna esquerda = original, direita = tradução.")
    print()
    arquivo = _solicitar_arquivo_pdf("Caminho do PDF")
    path_entrada = Path(arquivo)
    pasta_origem = path_entrada.parent
    stem, sufixo = path_entrada.stem, path_entrada.suffix
    codigo_motor = MOTOR_TRADUCAO_GOOGLE[0]

    idioma = _escolher_um_idioma()
    if not idioma:
        return
    codigo_idioma, nome_idioma = idioma

    entrada_origem = _pergunta("Idioma de origem (Enter = detectar automaticamente)", "")
    idioma_origem = _normalizar_idioma_origem(entrada_origem)

    caminho_traduzido = pasta_origem / f"{stem}_{codigo_motor}_{codigo_idioma}{sufixo}"
    caminho_2colunas = pasta_origem / f"{stem}_2colunas_{codigo_idioma}{sufixo}"

    print()
    print(f"  {C_TITULO}Traduzindo e montando PDF 2 colunas...{C_RESET}")
    print()
    try:
        traduzir_pdf(
            arquivo,
            str(caminho_traduzido),
            idioma_destino=codigo_idioma,
            idioma_origem=idioma_origem,
        )
        _mensagem_ok("Tradução concluída.")
        criar_pdf_duas_colunas(arquivo, str(caminho_traduzido), str(caminho_2colunas))
        _mensagem_ok(f"PDF 2 colunas gerado: {caminho_2colunas.name}")
        _mostrar_resumo_pasta_saida(pasta_origem, [str(caminho_2colunas)], "PDF 2 colunas (original + tradução)")
    except Exception as e:
        _mensagem_erro(str(e))
        _mostrar_resumo_pasta_saida(pasta_origem, [], "PDF 2 colunas (erro)")


def menu_principal() -> None:
    """Exibe o menu e executa a opção escolhida."""
    opcoes = [
        ("1", "Dividir PDF (a cada N páginas)", executar_dividir_por_paginas),
        ("2", "Dividir PDF (em N partes iguais)", executar_dividir_em_partes),
        ("3", "Juntar PDFs", executar_juntar),
        ("4", "Traduzir PDF (Google Translate)", executar_traduzir),
        ("5", "Traduzir PDF (original + tradução, 2 colunas)", executar_traduzir_2colunas),
        ("0", "Sair", None),
    ]
    _definir_titulo_janela(TITULO_APLICACAO)
    while True:
        _caixa_titulo(TITULO_APLICACAO)
        for codigo, texto, _ in opcoes:
            print(f"    {C_OPCAO}{codigo}.{C_RESET} {texto}")
        print()
        escolha = input(f"  Digite a opção ({C_OPCAO}0{C_RESET}-{C_OPCAO}5{C_RESET}): ").strip()
        for codigo, _, funcao in opcoes:
            if escolha == codigo:
                if funcao is None:
                    print()
                    print(f"  {C_SUCESSO}Até logo!{C_RESET}")
                    print()
                    return
                funcao()
                break
        else:
            _mensagem_aviso("Opção inválida. Escolha 0, 1, 2, 3, 4 ou 5.")


if __name__ == "__main__":
    menu_principal()
