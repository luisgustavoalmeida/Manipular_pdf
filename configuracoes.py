# -*- coding: utf-8 -*-
"""
Configurações centralizadas do projeto de manipulação de PDF.
"""

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
