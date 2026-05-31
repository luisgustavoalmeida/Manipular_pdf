# -*- coding: utf-8 -*-
"""
Configurações centralizadas do projeto de manipulação de PDF.
"""

import os

# Idioma padrão de destino para tradução (código ISO 639-1)
IDIOMA_TRADUCAO_PADRAO = "pt"

# Tamanho mínimo de texto (caracteres) para enviar à tradução (evita traduzir números isolados)
TAMANHO_MINIMO_TEXTO_TRADUCAO = 2

# Número de threads para tradução em paralelo (melhor desempenho sem perder qualidade).
# Valores altos podem causar rate limit no provedor; 4–8 é um bom equilíbrio.
NUMERO_WORKERS_TRADUCAO = 7

# Margens laterais (em pontos) no PDF traduzido — pequenas para aproveitar melhor a página.
MARGEM_ESQUERDA_TRADUCAO = 18
MARGEM_DIREITA_TRADUCAO = 5


def nucleos_disponiveis() -> int:
    """Quantidade de núcleos lógicos detectados no sistema."""
    return os.cpu_count() or 4


def threads_sugeridas_traducao() -> int:
    """Sugestão equilibrada de threads com base no hardware e na configuração padrão."""
    nucleos = nucleos_disponiveis()
    reserva_sistema = 1 if nucleos > 2 else 0
    candidato = min(NUMERO_WORKERS_TRADUCAO, max(1, nucleos - reserva_sistema))
    return max(1, candidato)


def limitar_threads_traducao(valor: int) -> int:
    """Garante valor entre 1 e o número de núcleos lógicos disponíveis."""
    return max(1, min(int(valor), nucleos_disponiveis()))
