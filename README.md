# Manipulador PDF · v2.0
<!-- versao:2.0 -->

Aplicação desktop para **Windows** que reúne, em uma única interface, as operações mais comuns sobre documentos PDF: dividir, juntar, traduzir, converter, extrair, rotacionar e comprimir. Disponível como **executável autônomo** (`ManipuladorPDF.exe`) ou como projeto Python para desenvolvimento e automação.

**Versão compilada atual:** [v2.0](https://github.com/luisgustavoalmeida/Manipular_pdf/releases/tag/v2.0) — baixe `ManipuladorPDF.exe` (Windows 64 bits, sem instalar Python).

**Repositório:** [github.com/luisgustavoalmeida/Manipular_pdf](https://github.com/luisgustavoalmeida/Manipular_pdf) · **Releases:** [github.com/luisgustavoalmeida/Manipular_pdf/releases](https://github.com/luisgustavoalmeida/Manipular_pdf/releases)

---

## Índice

- [Visão geral](#visão-geral)
- [Capturas de tela](#capturas-de-tela)
- [Recursos da interface](#recursos-da-interface)
- [Operações disponíveis](#operações-disponíveis)
- [Conversão de formatos](#conversão-de-formatos)
- [Tradução de PDFs](#tradução-de-pdfs)
- [Requisitos](#requisitos)
- [Instalação e uso rápido (executável)](#instalação-e-uso-rápido-executável)
- [Instalação para desenvolvimento](#instalação-para-desenvolvimento)
- [Uso](#uso)
- [Gerar o executável (PyInstaller)](#gerar-o-executável-pyinstaller)
- [Configuração](#configuração)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Arquitetura](#arquitetura)
- [Dependências](#dependências)
- [Solução de problemas](#solução-de-problemas)
- [Versão e histórico](#versão-e-histórico)

---

## Visão geral

O **Manipulador PDF** foi pensado para fluxos do dia a dia com manuais, apostilas, relatórios e documentos técnicos. A versão 2.0 oferece interface gráfica moderna (CustomTkinter), execução em segundo plano com barra de progresso, cancelamento seguro e distribuição em um único arquivo `.exe` que **não exige Python instalado**.

| Público | Como usar |
|---------|-----------|
| **Usuário final** | Baixe a [release v2.0](https://github.com/luisgustavoalmeida/Manipular_pdf/releases/tag/v2.0) (`ManipuladorPDF.exe`) e execute com duplo clique |
| **Desenvolvedor** | Clone o repositório, instale dependências e execute `python main.py` |
| **Automação** | Importe os módulos Python ou a camada `operacoes.py` em scripts |

---

## Capturas de tela

Interface gráfica com barra lateral, painéis por operação e alternância entre tema claro e escuro.

| Tema claro | Tema escuro |
|:--:|:--:|
| ![Tela inicial — tema claro](Imagens/Tela%20inicial%20tema%20claro.png) | ![Tela inicial — tema escuro](Imagens/Tela%20inicial%20tema%20escuro.png) |
| *Painel «Dividir PDF — a cada N páginas»* | *Mesma operação no tema escuro* |

---

## Recursos da interface

| Recurso | Descrição |
|---------|-----------|
| **Barra lateral** | Nove operações agrupadas em cinco categorias (Dividir, Juntar, Traduzir, Converter, Editar) |
| **Painéis por operação** | Seleção de arquivos e pastas, opções específicas e sugestão automática de nomes de saída |
| **Progresso em tempo real** | Barra de status com etapa atual, tempo decorrido e estimativa restante |
| **Cancelamento** | Interrompe operações longas; arquivos parciais gerados na execução cancelada são removidos automaticamente |
| **Resultado** | Exibe arquivos gerados e permite abrir a pasta de saída no Explorador |
| **Tema claro / escuro** | Alternância na barra lateral; preferência persistida automaticamente |
| **Diálogo Sobre** | Informações do programa carregadas de `sobre.json` (botão ⓘ ao lado do tema) |
| **Operação em segundo plano** | Ao trocar de painel durante uma execução, um banner indica o progresso e permite voltar ou cancelar |
| **Diálogos nativos** | Seleção de arquivos e pastas com lembrança da última pasta utilizada |

Preferências do usuário (tema, última pasta) são salvas em `%LOCALAPPDATA%\ManipuladorPDF\` quando executado como `.exe`, sem criar arquivos ao lado do executável.

---

## Operações disponíveis

| Categoria | Operação | Descrição |
|-----------|----------|-----------|
| **Dividir** | A cada N páginas | Gera vários PDFs com tamanho fixo (ex.: 10 páginas por arquivo) |
| **Dividir** | Em N partes iguais | Divide o documento em N arquivos com distribuição equilibrada de páginas |
| **Juntar** | Juntar PDFs | Concatena múltiplos PDFs em um único arquivo, com ordenação por nome |
| **Traduzir** | Traduzir PDF | Traduz o texto preservando layout, imagens e formatação (Google Translate) |
| **Traduzir** | Original + tradução (2 col.) | Gera PDF com original à esquerda e tradução à direita, página a página |
| **Converter** | Converter para PDF | Converte arquivos ou pastas inteiras para PDF (unir ou arquivos individuais) |
| **Editar** | Extrair páginas | Extrai intervalos e páginas avulsas (ex.: `1,3,5-10`) |
| **Editar** | Rotacionar páginas | Gira páginas selecionadas em 90° ou 180° |
| **Editar** | Comprimir PDF | Reduz o tamanho do arquivo (níveis leve, médio ou forte) |

---

## Conversão de formatos

| Tipo | Extensões suportadas |
|------|----------------------|
| Imagens | JPG, JPEG, PNG, GIF, BMP, TIFF, TIF, WEBP |
| Texto | TXT, MD, CSV, LOG, JSON, XML |
| Web | HTML, HTM |
| Office | DOC, DOCX, XLS, XLSX, PPT, PPTX, ODT, ODS, ODP, RTF |

**Conversão de pasta:** imagens podem ser unidas em um único PDF ou convertidas individualmente; demais formatos geram um PDF por arquivo.

> **Documentos Office** (Word, Excel, PowerPoint) dependem do [LibreOffice](https://www.libreoffice.org/download/download/) instalado no sistema. Imagens, texto e HTML funcionam sem software adicional.

---

## Tradução de PDFs

- **Motor:** Google Translate via biblioteca `deep-translator`
- **Preservação:** posição, fonte e layout original mantidos com PyMuPDF
- **Paralelismo:** tradução em múltiplas threads (ajustável na interface, limitado aos núcleos do processador)
- **Idiomas disponíveis:** Português, Inglês, Espanhol, Francês, Alemão, Italiano, Japonês, Chinês, Coreano, Russo, Árabe e Hindi
- **Modos:** um idioma, vários idiomas ou todos os idiomas da lista
- **Requisito:** conexão com a internet durante a tradução

---

## Requisitos

### Executável (`ManipuladorPDF.exe`)

| Item | Obrigatório |
|------|-------------|
| Windows 10 ou superior (64 bits) | Sim |
| Python instalado | Não |
| Conexão com a internet | Apenas para tradução |
| LibreOffice | Opcional (conversão Office) |

### Desenvolvimento (código-fonte)

| Item | Obrigatório |
|------|-------------|
| Python 3.10 ou superior | Sim |
| Conexão com a internet | Apenas para tradução |

---

## Instalação e uso rápido (executável)

A versão compilada oficial é a **v2.0** (`ManipuladorPDF.exe`, Windows 10+ 64 bits).

1. Baixe o executável na página de releases:  
   **[Manipulador PDF v2.0 — Download](https://github.com/luisgustavoalmeida/Manipular_pdf/releases/tag/v2.0)**  
   (arquivo `ManipuladorPDF.exe` nos Assets; opcionalmente o `.rar` compactado)
2. Copie o arquivo para a pasta desejada.
3. Execute com duplo clique — não há instalador nem dependência de Python.

> **Nota:** se o Windows SmartScreen exibir um aviso, escolha «Mais informações» → «Executar assim mesmo» (build local sem assinatura de código).

As preferências ficam em `%LOCALAPPDATA%\ManipuladorPDF\config_usuario.json`.

Para gerar o `.exe` localmente a partir do código-fonte, veja [Gerar o executável (PyInstaller)](#gerar-o-executável-pyinstaller).

---

## Instalação para desenvolvimento

```bash
git clone https://github.com/luisgustavoalmeida/Manipular_pdf.git
cd Manipular_pdf
```

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Linux / macOS** (interface gráfica e diálogos nativos foram projetados para Windows; o modo console pode funcionar):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Atalho alternativo no Windows: `executar.bat` (espera ambiente virtual `venv` ou `.venv` na pasta do projeto).

---

## Uso

### Interface gráfica (padrão)

```bash
python main.py
```

### Versão instalada

```bash
python main.py --version
```

### Menu em terminal

```bash
python main.py --console
```

| Opção | Operação |
|-------|----------|
| 1 | Dividir PDF (a cada N páginas) |
| 2 | Dividir PDF (em N partes iguais) |
| 3 | Juntar PDFs |
| 4 | Traduzir PDF |
| 5 | Traduzir PDF (2 colunas) |
| 6 | Converter arquivos para PDF |
| 7 | Extrair páginas |
| 8 | Rotacionar páginas |
| 9 | Comprimir PDF |
| 0 | Sair |

> O executável `.exe` abre apenas a interface gráfica. O modo terminal está disponível ao rodar a partir do código-fonte.

### Uso como biblioteca

```python
from dividir_pdf import dividir_por_paginas, dividir_em_partes
from juntar_pdf import juntar_pdfs
from traduzir_pdf import traduzir_pdf, criar_pdf_duas_colunas
from editar_pdf import extrair_paginas, rotacionar_paginas, comprimir_pdf, interpretar_paginas, obter_total_paginas
from converter_para_pdf import converter_arquivos_para_pdf, converter_arquivos_para_pdfs_individuais

# Dividir a cada 10 páginas
dividir_por_paginas("documento.pdf", 10, pasta_saida="saida")

# Juntar arquivos
juntar_pdfs(["parte_01.pdf", "parte_02.pdf"], "completo.pdf")

# Traduzir para português
traduzir_pdf("manual.pdf", "manual_pt.pdf", idioma_destino="pt")

# Extrair páginas (interpretar_paginas converte "1,3,5-10" em índices 0-based)
total = obter_total_paginas("doc.pdf")
indices = interpretar_paginas("1,3,5-10", total)
extrair_paginas("doc.pdf", indices, "paginas.pdf")

# Comprimir
comprimir_pdf("doc.pdf", "comprimido.pdf", nivel="medio")
```

Camada unificada com retorno estruturado (`ResultadoOperacao`):

```python
from operacoes import operacao_traduzir, operacao_juntar

resultado = operacao_traduzir("manual.pdf", [("pt", "Português")])
if resultado.sucesso:
    print(resultado.arquivos)
```

---

## Gerar o executável (PyInstaller)

```bash
build_exe.bat
```

Ou manualmente:

```bash
pip install -r requirements-build.txt
python -m PyInstaller --noconfirm --clean manipular_pdf.spec
```

**Saída:** `dist\ManipuladorPDF.exe` (~35 MB, arquivo único, sem janela de console).

Arquivos relacionados:

| Arquivo | Função |
|---------|--------|
| `manipular_pdf.spec` | Configuração do PyInstaller |
| `build_exe.bat` | Script de build para Windows |
| `requirements-build.txt` | Dependências de compilação |
| `recursos.py` | Caminhos de recursos e configuração no modo empacotado |

---

## Configuração

### Código (`configuracoes.py`)

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `IDIOMA_TRADUCAO_PADRAO` | Idioma de destino padrão (ISO 639-1) | `"pt"` |
| `TAMANHO_MINIMO_TEXTO_TRADUCAO` | Mínimo de caracteres para traduzir | `2` |
| `NUMERO_WORKERS_TRADUCAO` | Threads padrão na tradução | `7` |
| `MARGEM_ESQUERDA_TRADUCAO` / `MARGEM_DIREITA_TRADUCAO` | Margens do PDF traduzido (pt) | `18` / `5` |

### Usuário (`config_usuario.json`)

Criado automaticamente. Armazena tema (claro/escuro) e última pasta usada nos diálogos de arquivo.

| Modo | Localização |
|------|-------------|
| Executável | `%LOCALAPPDATA%\ManipuladorPDF\` |
| Desenvolvimento | Raiz do projeto (ignorado pelo Git) |

### Versão

Definida em [`constantes.py`](constantes.py) (`VERSAO_APLICACAO`). Para sincronizar a versão neste README:

```bash
python constantes.py
```

---

## Estrutura do projeto

```
Manipular_pdf/
├── main.py                      # Entrada: GUI, --console ou --version
├── operacoes.py                 # Camada de negócio (ResultadoOperacao)
├── constantes.py                # Versão, idiomas, metadados da GUI
├── configuracoes.py             # Parâmetros de tradução e workers
├── recursos.py                  # Caminhos (projeto, AppData, recursos empacotados)
├── dividir_pdf.py               # Divisão por páginas ou em N partes
├── juntar_pdf.py                # Junção de PDFs
├── traduzir_pdf.py              # Tradução e PDF em 2 colunas
├── editar_pdf.py                # Extrair, rotacionar, comprimir
├── converter_para_pdf.py        # Conversão multi-formato
├── progresso.py                 # Progresso, cancelamento e limpeza de parciais
├── seletor_arquivos.py          # Diálogos nativos Windows
├── navegacao.py                 # Fluxo do modo console
├── interface_console.py         # UI do terminal
├── interface_grafica/
│   ├── app.py                   # Janela principal
│   ├── paineis.py               # Painéis das nove operações
│   ├── componentes.py           # Widgets reutilizáveis
│   ├── tema.py                  # Tema claro/escuro
│   ├── sobre.py                 # Diálogo Sobre (sobre.json)
│   └── operacao_ativa.py        # Controle de execução em thread
├── sobre.json                   # Conteúdo do diálogo Sobre
├── Imagens/                     # Capturas de tela (README)
├── manipular_pdf.spec           # PyInstaller
├── build_exe.bat                # Build do .exe
├── requirements.txt
├── requirements-build.txt
├── executar.bat
└── README.md
```

---

## Arquitetura

O projeto separa **lógica de negócio**, **interfaces** e **módulos especializados**:

```
┌─────────────────┐     ┌─────────────────┐
│ interface_grafica│     │ interface_console│
│   (CustomTkinter)│     │   (menu terminal)│
└────────┬────────┘     └────────┬────────┘
         │                         │
         └──────────┬──────────────┘
                    ▼
            ┌───────────────┐
            │  operacoes.py │  ← ResultadoOperacao
            └───────┬───────┘
                    │
    ┌───────────────┼───────────────┬──────────────────┐
    ▼               ▼               ▼                  ▼
dividir_pdf    juntar_pdf     traduzir_pdf      converter_para_pdf
               editar_pdf     progresso.py
```

| Módulo | Responsabilidade |
|--------|------------------|
| `operacoes.py` | Orquestra operações e padroniza retorno para GUI e console |
| `dividir_pdf` / `juntar_pdf` | Cópia de páginas inteiras com pypdf |
| `traduzir_pdf` | Extração posicional de texto, tradução paralela e reposicionamento (PyMuPDF) |
| `editar_pdf` | Extração, rotação e compressão; gravação atômica via arquivo temporário |
| `converter_para_pdf` | Pipeline por tipo de arquivo; merge ou PDFs individuais |
| `progresso.py` | Barra de progresso unificada, cancelamento cooperativo e limpeza de arquivos parciais |

### Decisões técnicas

- **pypdf** para dividir e juntar: operações leves sobre páginas completas, sem reinterpretar o conteúdo.
- **PyMuPDF** para tradução, compressão e conversão avançada: acesso fino a layout, fontes e imagens.
- **Tradução em threads:** gargalo na API externa (I/O); pool de threads acelera sem alterar qualidade.
- **Gravação atômica:** junção, edição e conversão usam arquivo temporário + `replace` para evitar PDFs corrompidos.
- **Uma lógica, duas interfaces:** regras de negócio centralizadas em `operacoes.py`.

---

## Dependências

| Biblioteca | Uso |
|------------|-----|
| [pypdf](https://pypi.org/project/pypdf/) | Divisão, junção e manipulação por página |
| [PyMuPDF](https://pypi.org/project/PyMuPDF/) | Tradução, compressão, conversão e layout |
| [deep-translator](https://pypi.org/project/deep-translator/) | Tradução via Google Translate |
| [customtkinter](https://pypi.org/project/customtkinter/) | Interface gráfica |
| [tqdm](https://pypi.org/project/tqdm/) | Progresso no modo console |

**Externo (opcional):** [LibreOffice](https://www.libreoffice.org/download/download/) — conversão de documentos Office.

---

## Solução de problemas

| Situação | O que fazer |
|----------|-------------|
| Windows SmartScreen ao abrir o `.exe` | Normal em builds locais; confirme a origem do arquivo ou assine o executável em produção |
| Tradução falha ou demora muito | Verifique a internet; reduza threads; documentos muito grandes podem atingir limites do Google Translate |
| Conversão Office não funciona | Instale o LibreOffice e verifique se `soffice.exe` está no PATH ou nos caminhos padrão do Windows |
| Preferências não salvam | Confirme permissão de escrita em `%LOCALAPPDATA%\ManipuladorPDF\` |
| Erro ao compilar com PyInstaller | Use `requirements-build.txt`; execute o build dentro do ambiente virtual do projeto |

---

## Versão e histórico

Versão atual: **2.0**  
Release compilada: **[v2.0](https://github.com/luisgustavoalmeida/Manipular_pdf/releases/tag/v2.0)** · [Todas as releases](https://github.com/luisgustavoalmeida/Manipular_pdf/releases)

| Versão | Tipo | Destaques |
|--------|------|-----------|
| **2.0** | [Release](https://github.com/luisgustavoalmeida/Manipular_pdf/releases/tag/v2.0) + código | Interface gráfica, nove operações, `ManipuladorPDF.exe` para Windows, tema claro/escuro, diálogo Sobre, cancelamento com limpeza de parciais, conversão ampliada |
| **1.0** | Código | Versão inicial: dividir, juntar e traduzir (modo terminal) |

---

## Autor

**Luís Gustavo de Almeida** — Engenheiro Eletricista, Engenheiro de Software  
[LinkedIn](https://www.linkedin.com/in/luís-gustavo-de-almeida)

Programa gratuito. Contribuições e feedback via [Issues](https://github.com/luisgustavoalmeida/Manipular_pdf/issues) no GitHub.
