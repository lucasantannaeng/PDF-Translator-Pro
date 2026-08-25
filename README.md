# 🚀 PDF-Translator-Pro

**Suíte de Tradução Profissional de PDFs com Preservação de Layout & Motores de IA de Ponta**

O **PDF-Translator-Pro** é uma ferramenta desenvolvida para traduzir documentos técnicos complexos, manuais de operações aeronáuticas (OM-B, RFM), artigos científicos e livros em PDF do **Inglês para o Português do Brasil (pt-BR)** mantendo rigorosamente a **diagramação visual, tabelas, imagens, fórmulas matemáticas e paginação originais**.

---

## 🌟 Principais Funcionalidades

- **Preservação Visual Absoluta:** Utiliza o motor avançado de parsing e reconstrução vetorial do `pdf2zh` (PDFMathTranslate), mantendo fontes, posições de colunas, fotos e diagramas no mesmo lugar.
- **Múltiplos Motores de IA:** Integração nativa e configurada com:
  - **FreeLLM Local (100% Grátis | Sem Limites de Saldo):** Roteador inteligente local em `http://127.0.0.1:31415/v1` com acesso a mais de 160 modelos livres.
  - **DeepSeek V3** (`deepseek/deepseek-chat`): Tradução técnica de altíssima fidelidade com o menor custo do mercado.
  - **Gemini 2.5 & 3.7 Flash** (`google/gemini-2.5-flash`): Janela de contexto massiva e velocidade ultrarrápida.
  - **Claude 3.5 Sonnet** (`anthropic/claude-3.5-sonnet`): Máxima precisão e refinamento sintático.
  - **Groq Llama 3.3 70B** (`llama-3.3-70b-versatile`): Tradução com latência ultra-baixa.
- **Glossário Técnico Aeronáutico Integrado:** Injeção automática de diretrizes para manuais de helicópteros (Leonardo AW139, AW189, etc.) respeitando os padrões **ANAC, DECEA e ICAO** (mantendo siglas consagradas como *MTOW, OEI, AEO, FADEC, FLI, VNE, TDP, LDP*).
- **Interface Web Moderna (Streamlit):** Upload por arrastar e soltar (drag & drop), seletor visual de páginas, barra de progresso em tempo real e visualizador/download direto.
- **Terminal CLI Rico (Rich Console):** Diagnóstico estrutural completo, estimativa prévia de custos em USD/BRL e processamento em lote com 1 comando.
- **Formatos de Saída Flexíveis:** Gera tanto o documento **Mono** (100% em Português) quanto o documento **Dual** (Bilíngue espelhado lado a lado).

---

## 📁 Estrutura do Projeto

```text
D:\Projetos\1.Autorais\PDF-Translator-Pro\
│
├── .venv/                      # Ambiente virtual Python 3.11 isolado
├── config/
│   ├── settings.yaml           # Configurações gerais, modelos e provedores
│   ├── glossaries/
│   │   └── aviation.json       # Glossário técnico aeroespacial (OM-B / Helicópteros)
│   └── prompts/
│       └── system_pt_br.txt    # Prompt mestre de tradução técnica para pt-BR
│
├── input_pdfs/                 # 📂 Pasta onde você coloca os PDFs para traduzir
│   ├── OM-B AW139.pdf          # (621 páginas - Manual Leonardo AW139)
│   └── OM-B AW189.pdf          # (388 páginas - Manual Leonardo AW189)
│
├── output_translated/          # 📄 Pasta onde os PDFs traduzidos são gerados
│   ├── *.mono.pdf              # Versão traduzida em Português
│   └── *.dual.pdf              # Versão bilíngue lado a lado
│
├── core/                       # Núcleo de processamento e inteligência
│   ├── config.py               # Carregador de configurações e variáveis de ambiente
│   ├── pdf_analyzer.py         # Análise estrutural, contagem de tokens e cálculo de custo
│   ├── glossary.py             # Injeção dinâmica de terminologias nos prompts
│   ├── llm_router.py           # Gerenciador de rotas de IA (OpenRouter, DeepSeek, Gemini)
│   ├── translator.py           # Wrapper do motor de tradução e controle de execução
│   └── batch_runner.py         # Orquestrador de fila e geração de relatórios
│
├── gui/
│   └── app.py                  # Dashboard Web moderno em Streamlit
│
├── cli.py                      # Interface de linha de comando com visual Rich
├── translate_batch.py          # Script direto para tradução da fila completa
├── run_gui.bat                 # 🟢 Executável 1-clique para abrir a Interface Web
├── run_cli.bat                 # 🟢 Executável 1-clique para abrir o Terminal CLI
├── .env                        # Chaves de API configuradas com segurança
└── requirements.txt            # Dependências do ecossistema
```

---

## ⚡ Como Usar (Passo a Passo)

### Opção 1: Pela Interface Web (Recomendado)
1. Dê um duplo clique no arquivo **`run_gui.bat`**.
2. A interface abrirá automaticamente no seu navegador (`http://localhost:8501`).
3. Arraste qualquer novo PDF para a área de upload.
4. Escolha o modelo de IA desejado (padrão: **DeepSeek V3** ou **Gemini Flash**).
5. Clique no botão **🚀 Iniciar Tradução Agora** e acompanhe o progresso página por página.
6. Na aba **📂 Documentos Traduzidos**, clique em **⬇️ Baixar** para salvar seu PDF pronto.

---

### Opção 2: Pelo Terminal CLI Interativo
Dê um duplo clique em **`run_cli.bat`** ou use os comandos abaixo:

```powershell
# 1. Listar arquivos na fila de entrada:
python cli.py list

# 2. Diagnosticar um PDF e ver estimativa de custo de todos os modelos de IA:
python cli.py analyze "OM-B AW139.pdf"

# 3. Testar a conexão com a API:
python cli.py test-api

# 4. Traduzir um arquivo específico (ex: páginas 1 a 10 para teste rápido):
python cli.py translate "OM-B AW139.pdf" --pages 1-10

# 5. Traduzir o documento completo:
python cli.py translate "OM-B AW139.pdf"

# 6. Traduzir TODOS os PDFs da pasta input_pdfs/ em lote:
python cli.py batch
```

---

## 💰 Estimativa Real de Custos por Documento

Estimativas calculadas com base no volume de texto real dos manuais:

| Documento | Páginas | Palavras / Tokens | Custo no DeepSeek V3 | Custo no Gemini Flash | Custo no Claude 3.5 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **OM-B AW139** | 621 | ~99.189 pal. (~128k tok.) | **\$0.05 USD (~R\$ 0,34)** | **\$0.05 USD (~R\$ 0,30)** | \$2.51 USD (~R\$ 14,50) |
| **OM-B AW189** | 388 | ~67.585 pal. (~87k tok.) | **\$0.03 USD (~R\$ 0,23)** | **\$0.03 USD (~R\$ 0,21)** | \$1.71 USD (~R\$ 9,90) |

> **Conclusão:** O custo para traduzir um manual técnico de mais de 600 páginas com IA de última geração é de **menos de 40 centavos de Real**.

---

## 🔄 Como Traduzir Qualquer Outro PDF no Futuro

O sistema foi arquitetado para ser 100% reutilizável para qualquer arquivo futuro:
1. Basta arrastar seu novo arquivo `.pdf` pela Interface Web ou copiá-lo para a pasta **`input_pdfs/`**.
2. Execute a tradução normalmente.
3. Se o novo PDF for de outra área (ex: Medicina, Direito, TI, Engenharia Civil), você pode criar um novo arquivo JSON na pasta `config/glossaries/` para injetar termos específicos da sua nova área.

---

## 🛡️ Segurança & Chaves de API

As chaves de API estão salvas de forma segura no arquivo `.env` na raiz do projeto. Para alterar ou adicionar novas chaves:
- `OPENROUTER_API_KEY`: Acesso unificado a dezenas de modelos (DeepSeek, Gemini, Claude, Llama).
- `DEEPSEEK_API_KEY`: Acesso direto ao endpoint oficial da DeepSeek.
- `GEMINI_API_KEY`: Acesso direto ao Google AI Studio.
- `GROQ_API_KEY`: Acesso para inferência ultra rápida.
