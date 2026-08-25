# PDF-Translator-Pro

> Professional PDF translation suite with layout preservation and multi-provider AI model routing.

`PDF-Translator-Pro` translates complex technical documents, scientific papers, manuals, and books from any language (defaulting to English to Brazilian Portuguese) while preserving original visual layout, typography, tables, images, formulas, and page flow.

---

## Key Features

- **Layout-Preserving Translation:** Powered by advanced vector parsing and text replacement (`pdf2zh`), maintaining column positions, graphics, and formulas intact.
- **Multi-Provider LLM Router:** Native support for:
  - **OpenRouter:** Universal gateway to DeepSeek V3, Claude 3.5/3.7 Sonnet, GPT-4o, and Llama 3.3.
  - **Google Gemini API:** Fast, high-context translation via Gemini 2.5 / 3.7 Flash.
  - **DeepSeek API:** Cost-efficient direct endpoint.
  - **Groq:** Ultra low-latency inference.
  - **FreeLLM Local Proxy:** Compatible with OpenAI-standard local endpoints (`http://127.0.0.1:31415/v1`).
- **Domain-Specific Technical Glossaries:** Dynamic glossary injection (e.g. aerospace, medical, legal, engineering) to preserve acronyms and standardized industry terms.
- **Modern Web GUI (Streamlit):** Drag-and-drop file upload, real-time page-by-page progress tracking, and direct preview/download.
- **Rich CLI Suite:** Terminal-based structural analyzer, token count & cost estimation, and batch processing.
- **Dual Output Formats:** Generates both **Mono** (translated document) and **Dual** (side-by-side bilingual comparison).

---

## Project Structure

```text
PDF-Translator-Pro/
├── config/
│   ├── settings.yaml         # Provider & model configuration
│   ├── glossaries/           # Domain-specific terminology JSON files
│   └── prompts/              # System translation prompts
├── core/
│   ├── batch_runner.py       # Queue management and batch orchestrator
│   ├── config.py             # Configuration loader & environment validator
│   ├── glossary.py           # Dynamic glossary term injector
│   ├── llm_router.py         # Multi-provider LLM API client
│   ├── pdf_analyzer.py       # Structural inspection & token cost estimator
│   └── translator.py         # Engine wrapper and execution pipeline
├── gui/
│   └── app.py                # Streamlit Web Dashboard
├── input_pdfs/               # Input folder for source PDF files
├── output_translated/        # Destination folder for translated outputs
├── cli.py                    # Command-line interface with Rich formatting
├── requirements.txt          # Python dependencies
└── .env.example              # Environment variables template
```

---

## Installation & Setup

### 1. Clone the repository and install dependencies

```bash
git clone https://github.com/lucasantannaeng/PDF-Translator-Pro.git
cd PDF-Translator-Pro

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and set your API keys:

```bash
cp .env.example .env
```

```ini
OPENROUTER_API_KEY=your_openrouter_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

---

## Usage

### Web Interface

Launch the interactive dashboard:

```bash
streamlit run gui/app.py
# Or on Windows: run_gui.bat
```

Access `http://localhost:8501` to upload files, configure translation parameters, and monitor progress.

### Command Line Interface (CLI)

```bash
# List all pending PDF files in input directory
python cli.py list

# Analyze PDF structure and estimate translation cost
python cli.py analyze document.pdf

# Test API connection to configured LLM providers
python cli.py test-api

# Translate specific page range (e.g. pages 1 to 10)
python cli.py translate document.pdf --pages 1-10

# Translate full document
python cli.py translate document.pdf

# Process all PDFs in batch mode
python cli.py batch
```

---

## Customizing Glossaries

To enforce specific terminology, add a JSON mapping file in `config/glossaries/`:

```json
{
  "MTOW": "MTOW (Maximum Takeoff Weight)",
  "FADEC": "FADEC",
  "OEI": "OEI (One Engine Inoperative)"
}
```

Specify the active glossary in `config/settings.yaml` or pass it via CLI:

```bash
python cli.py translate document.pdf --glossary aviation
```

---

## License

This project is licensed under the MIT License.
