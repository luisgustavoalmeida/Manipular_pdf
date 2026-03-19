# Manipulação de PDF

Projeto em Python para **dividir**, **juntar** e **traduzir** arquivos PDF. Todo o código está em português (BR).

## Recursos

- **Dividir PDF**
  - **Por páginas**: você informa de quantas em quantas páginas dividir (ex.: a cada 5 páginas).
  - **Em N partes**: você informa em quantas partes quer dividir e o programa distribui as páginas de forma homogênea.
- **Juntar PDFs**: junta vários PDFs (por exemplo, os que foram divididos) em um único arquivo.
- **Traduzir PDF**: gera um novo PDF com todo o texto traduzido, **mantendo formatação e imagens** (ideal para manuais).

## Requisitos

- Python 3.10 ou superior
- Conexão com a internet (apenas para a função de tradução)

## Instalação

1. Crie um ambiente virtual (recomendado):

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

## Uso

Execute o programa principal para abrir o menu interativo:

```bash
python main.py
```

No menu você pode:

1. **Dividir PDF (a cada N páginas)** – informar o arquivo e quantas páginas por parte.
2. **Dividir PDF (em N partes iguais)** – informar o arquivo e em quantas partes dividir.
3. **Juntar PDFs** – informar vários arquivos e o nome do PDF de saída.
4. **Traduzir PDF** – informar o arquivo, o idioma de destino (ex.: `pt`, `en`) e o caminho de saída. O texto é traduzido e as imagens e o layout são mantidos.

## Uso como biblioteca

Você pode importar as funções em seus próprios scripts:

```python
from dividir_pdf import dividir_por_paginas, dividir_em_partes
from juntar_pdf import juntar_pdfs
from traduzir_pdf import traduzir_pdf

# Dividir a cada 10 páginas
dividir_por_paginas("documento.pdf", 10, pasta_saida="saida")

# Dividir em 3 partes
dividir_em_partes("documento.pdf", 3, pasta_saida="saida")

# Juntar arquivos
juntar_pdfs(["parte_01.pdf", "parte_02.pdf"], "completo.pdf")

# Traduzir para português
traduzir_pdf("manual.pdf", "manual_pt.pdf", idioma_destino="pt")
```

## Configuração da tradução

No arquivo `configuracoes.py` você pode alterar:

- `IDIOMA_TRADUCAO_PADRAO`: idioma de destino padrão (ex.: `"pt"`).
- `PROVEDOR_TRADUCAO`: provedor usado — **`"google"`** (padrão) ou **`"libre"`** (IA gratuita/open source).
- `TAMANHO_MINIMO_TEXTO_TRADUCAO`: trechos menores que isso não são enviados à tradução.
- Para **LibreTranslate** (tradutor com IA gratuito):
  - `LIBRE_TRADUCAO_URL`: URL da API (ex.: `https://libretranslate.com` ou `https://libretranslate.de`).
  - `LIBRE_TRADUCAO_API_KEY`: chave opcional; deixe vazio para uso sem chave (algumas instâncias têm limite de uso).

**Tradutor com IA gratuito:** use `PROVEDOR_TRADUCAO = "libre"` para tradução via **LibreTranslate** (open source, neural). Não exige chave na maioria das instâncias públicas. Para manuais com muitas páginas, a operação pode demorar e está sujeita a limites do serviço.

## Estrutura do projeto

```
Manipular_pdf/
├── main.py           # Menu principal
├── dividir_pdf.py    # Divisão (por páginas ou em partes)
├── juntar_pdf.py     # Junção de PDFs
├── traduzir_pdf.py   # Tradução mantendo layout e imagens
├── configuracoes.py  # Configurações (idioma, provedor, etc.)
├── requirements.txt
└── README.md
```

## Publicar no GitHub

1. Crie um repositório novo no GitHub (sem README, sem .gitignore).
2. Na pasta do projeto, adicione o remote e envie:

   ```bash
   git remote add origin https://github.com/SEU_USUARIO/Manipular_pdf.git
   git branch -M main
   git push -u origin main
   ```

   (Substitua `SEU_USUARIO` pelo seu usuário do GitHub.)

## Licença

Uso livre para fins pessoais e educacionais. Veja o arquivo [LICENSE](LICENSE) (MIT).
