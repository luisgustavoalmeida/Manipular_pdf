# Manipulador PDF

Ferramenta em Python para **dividir**, **juntar**, **traduzir**, **converter**, **extrair**, **rotacionar** e **comprimir** arquivos PDF. Interface gráfica moderna por padrão; menu em terminal disponível com `--console`.

---

## Sobre o projeto

O **Manipulador PDF** (v2.0) permite trabalhar com documentos PDF de forma simples e visual. Ideal para manuais, apostilas e documentos técnicos.

- **Interface gráfica:** janela com barra lateral, painéis por operação, barra de progresso e cancelamento (CustomTkinter).
- **Interface em terminal:** menu interativo com cores e caixas (`python main.py --console`).
- **Biblioteca:** funções importáveis para uso em scripts e automações.
- **Tradução:** Google Translate com preservação de **formatação e imagens** (PyMuPDF).

---

## Funcionalidades

| Categoria | Função | Descrição |
|-----------|--------|-----------|
| **Dividir** | Por páginas | Gera vários PDFs com um número fixo de páginas (ex.: a cada 10 páginas). |
| **Dividir** | Em N partes | Divide o PDF em N arquivos com quantidade de páginas equilibrada. |
| **Juntar** | Juntar PDFs | Concatena vários PDFs em um único arquivo. |
| **Traduzir** | Tradução completa | Gera PDF(s) traduzido(s), mantendo layout e imagens. Suporta um, vários ou todos os idiomas disponíveis. |
| **Traduzir** | 2 colunas | Gera PDF com original e tradução lado a lado. |
| **Converter** | Para PDF | Converte imagens, texto, HTML e documentos Office para PDF. |
| **Editar** | Extrair páginas | Extrai páginas específicas (ex.: `1,3,5-10`). |
| **Editar** | Rotacionar | Gira páginas selecionadas em 90° ou 180°. |
| **Editar** | Comprimir | Reduz o tamanho do PDF (níveis leve, médio ou forte). |

### Formatos aceitos na conversão

| Tipo | Extensões |
|------|-----------|
| Imagens | JPG, PNG, GIF, BMP, TIFF, WEBP |
| Texto | TXT, MD, CSV, LOG, JSON, XML |
| Web | HTML, HTM |
| Office | DOC, DOCX, XLS, XLSX, PPT, PPTX, ODT, ODS, ODP, RTF |

> **Word, Excel e PowerPoint** exigem o [LibreOffice](https://www.libreoffice.org/download/download/) instalado. Imagens, texto e HTML funcionam sem instalação extra.

### Idiomas de tradução

Português, Inglês, Espanhol, Francês, Alemão, Italiano, Japonês, Chinês, Coreano, Russo, Árabe e Hindi.

---

## Requisitos

- **Python** 3.10 ou superior
- **Conexão com a internet** (apenas para tradução)
- **LibreOffice** (opcional — apenas para conversão de documentos Office)

---

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/luisgustavoalmeida/Manipular_pdf.git
cd Manipular_pdf
```

### 2. Criar ambiente virtual (recomendado)

**Windows (PowerShell ou CMD):**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

---

## Uso

### Interface gráfica (padrão)

```bash
python main.py
```

**Windows:** você também pode usar o atalho `executar.bat` (usa o Python do ambiente virtual `venv` na pasta do projeto).

A janela organiza as operações em categorias na barra lateral. Cada painel permite selecionar arquivos, configurar opções e acompanhar o progresso. Ao concluir, os arquivos gerados podem ser abertos ou a pasta de saída pode ser exibida no explorador.

### Menu em terminal

```bash
python main.py --console
```

| Opção | Ação |
|-------|------|
| **1** | Dividir PDF (a cada N páginas) |
| **2** | Dividir PDF (em N partes iguais) |
| **3** | Juntar PDFs |
| **4** | Traduzir PDF (Google Translate) |
| **5** | Traduzir PDF (original + tradução, 2 colunas) |
| **6** | Converter arquivos para PDF |
| **7** | Extrair páginas específicas |
| **8** | Rotacionar páginas |
| **9** | Comprimir / reduzir tamanho |
| **0** | Sair |

### Uso como biblioteca

Importe as funções nos seus scripts:

```python
from dividir_pdf import dividir_por_paginas, dividir_em_partes
from juntar_pdf import juntar_pdfs
from traduzir_pdf import traduzir_pdf, criar_pdf_duas_colunas
from editar_pdf import extrair_paginas, rotacionar_paginas, comprimir_pdf
from converter_para_pdf import converter_arquivos_para_pdf

# Dividir a cada 10 páginas
dividir_por_paginas("documento.pdf", 10, pasta_saida="saida")

# Dividir em 3 partes
dividir_em_partes("documento.pdf", 3, pasta_saida="saida")

# Juntar arquivos
juntar_pdfs(["parte_01.pdf", "parte_02.pdf"], "completo.pdf")

# Traduzir para português (mantém layout e imagens)
traduzir_pdf("manual.pdf", "manual_pt.pdf", idioma_destino="pt")

# Traduzir e gerar PDF em duas colunas (original + tradução)
criar_pdf_duas_colunas("manual.pdf", "manual_2colunas.pdf", idioma_destino="pt")

# Extrair páginas, rotacionar e comprimir
extrair_paginas("doc.pdf", "1,3,5-10", "paginas.pdf")
rotacionar_paginas("doc.pdf", 90, "rotacionado.pdf", paginas="1-5")
comprimir_pdf("doc.pdf", "comprimido.pdf", nivel="medio")
```

Para integração com retorno estruturado (sucesso, arquivos gerados, mensagens), use o módulo `operacoes`:

```python
from operacoes import operacao_traduzir, operacao_juntar

resultado = operacao_traduzir("manual.pdf", [("pt", "Português")])
if resultado.sucesso:
    print(resultado.arquivos)
```

---

## Configuração

As opções gerais ficam em `configuracoes.py`:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `IDIOMA_TRADUCAO_PADRAO` | Idioma de destino padrão (ISO 639-1) | `"pt"`, `"en"` |
| `TAMANHO_MINIMO_TEXTO_TRADUCAO` | Mínimo de caracteres para traduzir (evita números soltos) | `2` |
| `NUMERO_WORKERS_TRADUCAO` | Threads para tradução em paralelo | `7` |
| `MARGEM_ESQUERDA_TRADUCAO` / `MARGEM_DIREITA_TRADUCAO` | Margens do PDF traduzido (pontos) | `18`, `5` |

A tradução usa **Google Translate** (biblioteca `deep-translator`). Para manuais grandes, a operação pode demorar e está sujeita a limites do serviço. O número de threads é ajustável na interface e limitado ao número de núcleos do processador.

---

## Estrutura do projeto

```
Manipular_pdf/
├── main.py                    # Ponto de entrada (GUI ou --console)
├── operacoes.py               # Lógica de negócio unificada (ResultadoOperacao)
├── constantes.py              # Título, versão, idiomas disponíveis
├── configuracoes.py           # Configurações (idioma, margens, workers)
├── dividir_pdf.py             # Divisão (por páginas ou em N partes)
├── juntar_pdf.py              # Junção de múltiplos PDFs
├── traduzir_pdf.py            # Tradução com preservação de layout
├── editar_pdf.py              # Extrair, rotacionar e comprimir
├── converter_para_pdf.py      # Conversão de diversos formatos para PDF
├── progresso.py               # Barras de progresso e cancelamento
├── navegacao.py               # Diálogos e entrada no modo console
├── interface_console.py       # Componentes visuais do terminal
├── interface_grafica/         # Interface gráfica (CustomTkinter)
│   ├── app.py                 # Janela principal
│   ├── paineis.py             # Painéis por operação
│   ├── componentes.py         # Widgets reutilizáveis
│   └── tema.py                # Cores, fontes e dimensões
├── requirements.txt
├── executar.bat                 # Atalho Windows
└── README.md
```

### Dependências principais

| Biblioteca | Uso |
|------------|-----|
| **pypdf** | Divisão, junção e operações por página |
| **PyMuPDF** | Tradução, compressão, conversão e layout avançado |
| **deep-translator** | Tradução via Google Translate |
| **customtkinter** | Interface gráfica |
| **tqdm** | Barra de progresso (modo console e scripts) |

---

## Arquitetura

O projeto separa **lógica de negócio**, **interfaces** e **módulos especializados**:

- **`operacoes.py`** — camada intermediária que chama os módulos de PDF e retorna `ResultadoOperacao` padronizado. Usada tanto pela GUI quanto pelo console.
- **`dividir_pdf` / `juntar_pdf`** — operações baseadas em cópia de páginas inteiras (pypdf).
- **`traduzir_pdf`** — extrai blocos de texto com posição e fonte, traduz em paralelo e recoloca o texto na mesma região (PyMuPDF).
- **`editar_pdf`** — extrair, rotacionar e comprimir páginas.
- **`converter_para_pdf`** — converte imagens, texto, HTML e Office para PDF.
- **`interface_grafica`** — janela com sidebar, painéis dinâmicos, execução em thread e cancelamento.
- **`interface_console`** — menu interativo com cores ANSI e diálogos de arquivo nativos.

### Decisões técnicas

- **pypdf para dividir/juntar:** copia páginas sem interpretar conteúdo; leve e suficiente para essas tarefas.
- **PyMuPDF para tradução e edição avançada:** acesso a posição, fonte e redação de texto na mesma área, preservando imagens e desenhos.
- **Tradução em threads:** a lentidão está na API (I/O); um pool de threads envia vários trechos em paralelo.
- **Duas interfaces, uma lógica:** `operacoes.py` evita duplicar regras de negócio entre GUI e terminal.

---
