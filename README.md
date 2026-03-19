<p align="center">
  <img src="imagem ilustrativa/Automação de tradução de manuais técnicos.png" alt="Automação na tradução de manuais técnicos" width="100%">
</p>

# Manipulador de PDF

Ferramenta em Python para **dividir**, **juntar** e **traduzir** arquivos PDF com interface em terminal e uso como biblioteca. Código e documentação em português (BR).

---

## Sobre o projeto

O **Manipulador de PDF** permite trabalhar com documentos PDF de forma simples: dividir por número de páginas ou em partes iguais, unir vários arquivos em um só e traduzir o conteúdo preservando **formatação e imagens**. Ideal para manuais, apostilas e documentos técnicos.

- **Interface:** menu interativo no terminal (Windows e Linux/macOS) com cores e caixas.
- **Biblioteca:** funções importáveis para uso em scripts e automações.
- **Tradução:** Google Translate (padrão); layout e imagens mantidos com PyMuPDF.

---

## Funcionalidades

| Função | Descrição |
|--------|-----------|
| **Dividir por páginas** | Gera vários PDFs com um número fixo de páginas (ex.: a cada 5 páginas). |
| **Dividir em N partes** | Divide o PDF em N arquivos com quantidade de páginas equilibrada. |
| **Juntar PDFs** | Concatena vários PDFs em um único arquivo (com ordenação opcional por nome). |
| **Traduzir PDF** | Gera um novo PDF com o texto traduzido, mantendo layout e imagens. |
| **Traduzir em 2 colunas** | Gera um PDF com original e tradução lado a lado (duas colunas). |

---

## Requisitos

- **Python** 3.10 ou superior  
- **Conexão com a internet** (apenas para tradução)

---

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/SEU_USUARIO/Manipular_pdf.git
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

### Menu interativo

Execute o programa principal para abrir o menu:

```bash
python main.py
```

**Windows:** você também pode usar o atalho `executar.bat` (usa o `python` do ambiente virtual na pasta do projeto).

Opções do menu:

| Opção | Ação |
|-------|------|
| **1** | Dividir PDF (a cada N páginas) |
| **2** | Dividir PDF (em N partes iguais) |
| **3** | Juntar PDFs |
| **4** | Traduzir PDF (Google Translate) |
| **5** | Traduzir PDF (original + tradução, 2 colunas) |
| **0** | Sair |

### Uso como biblioteca

Importe as funções nos seus scripts:

```python
from dividir_pdf import dividir_por_paginas, dividir_em_partes
from juntar_pdf import juntar_pdfs
from traduzir_pdf import traduzir_pdf, criar_pdf_duas_colunas

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

A tradução usa **Google Translate** (biblioteca `deep-translator`). Para manuais grandes, a operação pode demorar e está sujeita a limites do serviço.

---

## Estrutura do projeto

```
Manipular_pdf/
├── main.py              # Menu principal e interface em terminal
├── dividir_pdf.py       # Divisão (por páginas ou em N partes)
├── juntar_pdf.py        # Junção de múltiplos PDFs
├── traduzir_pdf.py      # Tradução com preservação de layout e imagens
├── configuracoes.py     # Configurações (idioma, margens, workers)
├── requirements.txt    # Dependências Python
├── executar.bat        # Atalho de execução no Windows
├── LICENSE
└── README.md
```

### Dependências principais

- **pypdf** — divisão e junção de PDFs  
- **PyMuPDF** — leitura/escrita avançada (layout e imagens na tradução)  
- **deep-translator** — tradução (Google Translate)  
- **tqdm** — barra de progresso  

---

## Como o projeto foi feito

Resumo da arquitetura, dos recursos utilizados e do papel de cada biblioteca no projeto.

### Arquitetura

O projeto é organizado em **módulos por função**: `dividir_pdf`, `juntar_pdf` e `traduzir_pdf` expõem funções puras (entrada/saída bem definida), e o `main.py` cuida da **interface em terminal** (menu, caixas, cores, leitura de caminhos) e chama essas funções. Assim, o mesmo código serve tanto para uso interativo quanto para importação em outros scripts.

- **Dividir e juntar:** operações baseadas em páginas inteiras (copiar referências de páginas), sem interpretar texto ou imagens.
- **Traduzir:** fluxo em etapas: extrair blocos de texto com posição e fonte → traduzir em paralelo → recolocar o texto traduzido na mesma região do original, preservando imagens e layout.

### Recursos e uso de cada biblioteca

| Recurso | Uso no projeto |
|--------|-----------------|
| **pypdf** (`PdfReader`, `PdfWriter`) | **Dividir:** lê o PDF, cria um `PdfWriter` por parte e adiciona as páginas correspondentes com `add_page()`. **Juntar:** um único `PdfWriter` que faz `append()` de cada `PdfReader`. Leve e suficiente para copiar páginas sem alterar conteúdo. |
| **PyMuPDF** (`fitz`) | **Traduzir:** abre o PDF e, por página, usa `get_text("dict")` para obter blocos de texto com **posição (bbox), tamanho da fonte e nome da fonte**. Traduz os blocos (em paralelo), depois usa **redação** (`add_redact_annot` + `apply_redactions`) para substituir o texto no mesmo retângulo, mantendo imagens e layout. **Duas colunas:** cria uma página com largura dupla e desenha original e traduzido lado a lado com `show_pdf_page()`. |
| **deep-translator** (`GoogleTranslator`) | Envio de trechos de texto para o **Google Translate**. Detecção automática de idioma de origem quando não informada. Uso com **até 3 tentativas** em caso de falha de rede. |
| **tqdm** | **Barras de progresso** em todas as operações: número de partes ao dividir, número de arquivos ao juntar, número de páginas ao traduzir. |
| **ThreadPoolExecutor** (biblioteca padrão) | Na tradução, **vários blocos de texto da mesma página** são enviados ao Google em paralelo (até `NUMERO_WORKERS_TRADUCAO` threads), aproveitando o tempo de espera da API e reduzindo o tempo total. |

### Decisões técnicas

- **pypdf para dividir/juntar:** não é necessário acessar texto ou gráficos por elemento; apenas copiar páginas. O pypdf é simples e evita dependência pesada para essas tarefas.
- **PyMuPDF para tradução:** é preciso **posição e estilo de cada trecho** para recolocar o texto traduzido no mesmo lugar. O PyMuPDF oferece extração de texto com bbox e fonte e o mecanismo de redação para “pintar” o texto novo na mesma área, mantendo o restante da página (imagens, desenhos) intacto.
- **Tradução em threads:** a lentidão está no acesso à API (I/O), não no processamento local. Usar um pool de threads permite enviar vários trechos ao mesmo tempo e manter a ordem dos resultados por índice para não alterar o layout.
- **Interface no terminal:** uso de **Path** para caminhos (cross-platform), **UTF-8** no Windows para acentos, e **códigos ANSI** para cores e caixas, com fallback se o terminal não suportar.

---

## Publicar no GitHub

1. Crie um repositório novo no GitHub (sem README, sem .gitignore).
2. Na pasta do projeto:

```bash
git remote add origin https://github.com/SEU_USUARIO/Manipular_pdf.git
git branch -M main
git push -u origin main
```

Substitua `SEU_USUARIO` pelo seu usuário do GitHub.

---

