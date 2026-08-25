"""
PDF-Translator-Pro | Enterprise AI Translation Suite
Executive Streamlit Interface for high-fidelity, layout-preserving document translation.
Author: Luca Rodrigues Gomes de Sant'Anna
"""

import os
import sys
import time
from pathlib import Path
import streamlit as st

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.config import config
from core.pdf_analyzer import analyze_pdf
from core.llm_router import router
from core.translator import TranslationJob
from core.glossary import glossary_manager

# Page Configuration
st.set_page_config(
    page_title="PDF-Translator-Pro | Enterprise Suite",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Corporate Dark Slate & Cyan Executive Palette)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(165deg, #090d16 0%, #0f172a 50%, #090d16 100%);
        color: #f1f5f9;
    }
    
    .executive-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 18px 24px;
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(14, 165, 233, 0.2);
        border-radius: 14px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
    }
    
    .brand-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.4rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #38bdf8 0%, #34d399 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .author-badge {
        background: rgba(14, 165, 233, 0.12);
        border: 1px solid rgba(14, 165, 233, 0.35);
        color: #38bdf8;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    .stMetric {
        background: rgba(30, 41, 59, 0.65) !important;
        border: 1px solid rgba(51, 65, 85, 0.8) !important;
        padding: 14px 18px !important;
        border-radius: 12px !important;
        backdrop-filter: blur(8px);
    }
    
    .card-box {
        background: rgba(30, 41, 59, 0.55);
        padding: 18px 22px;
        border-radius: 12px;
        border: 1px solid rgba(51, 65, 85, 0.7);
        margin-bottom: 14px;
        backdrop-filter: blur(8px);
        transition: border-color 0.25s ease;
    }
    .card-box:hover {
        border-color: rgba(14, 165, 233, 0.4);
    }
    
    .badge-ready {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34d399;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.78rem;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .badge-pending {
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.4);
        color: #fbbf24;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.78rem;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid rgba(51, 65, 85, 0.6);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(51, 65, 85, 0.4);
        border-radius: 8px 8px 0 0;
        color: #94a3b8;
        font-weight: 600;
        padding: 8px 18px;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(14, 165, 233, 0.15) !important;
        border-color: rgba(14, 165, 233, 0.5) !important;
        color: #38bdf8 !important;
        border-bottom: 2px solid #0ea5e9 !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: #ffffff;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        transition: all 0.2s ease;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.25);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# Executive Branding Header
st.markdown("""
<div class="executive-header">
    <div>
        <div class="brand-title">📄 PDF-Translator-Pro</div>
        <div style="color: #94a3b8; font-size: 0.88rem; margin-top: 2px;">
            Suíte de Tradução Técnica com Preservação Vetorial de Layout &amp; Roteamento Multi-LLM
        </div>
    </div>
    <div class="author-badge">
        Luca Rodrigues · Engenharia &amp; IA v1.0.0
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/38bdf8/pdf-2.png", width=56)
    st.markdown("### ⚙️ Painel de Controle")
    st.caption("Configurações do Roteador de Modelos &amp; Motor")
    st.divider()

    st.subheader("🤖 Modelo de Tradução")
    available_models = router.get_available_models()
    model_options = {f"{m['name']} ({m['provider']})": m for m in available_models}
    
    selected_model_label = st.selectbox(
        "Selecione a IA:",
        options=list(model_options.keys()),
        index=0
    )
    selected_model_info = model_options[selected_model_label]
    provider_name = selected_model_info["provider"]
    model_id = selected_model_info["model_id"]

    # Test API connection
    if st.button("🔌 Testar Conexão com a IA", use_container_width=True):
        with st.spinner("Testando latência da API..."):
            success, msg, elapsed = router.test_connection(provider_name, model_id)
            if success:
                st.success(f"✅ Conectado em {elapsed}s!")
                st.caption(msg)
            else:
                st.error("❌ Falha na conexão:")
                st.caption(msg)

    st.divider()
    st.subheader("🛠️ Parâmetros Operacionais")
    concurrency = st.slider("Threads Concorrentes (Páginas Paralelas):", min_value=1, max_value=16, value=config.concurrency)
    
    glossaries = list(glossary_manager._cache.keys()) or ["aviation"]
    selected_domain = st.selectbox("Glossário Técnico de Domínio:", options=glossaries, index=0)
    
    output_format = st.radio("Formato de Saída do PDF:", options=["both", "mono", "dual"], format_func=lambda x: {
        "both": "Ambos (Mono 100% PT + Dual Bilíngue)",
        "mono": "Apenas Traduzido (Mono)",
        "dual": "Apenas Bilíngue Lado a Lado (Dual)"
    }[x])

# Main Tabs
tab_trans, tab_diag, tab_viewer, tab_glossary, tab_doctor = st.tabs([
    "🚀 Central de Tradução", 
    "📊 Diagnóstico & Custos", 
    "📂 Repositório de Documentos", 
    "📖 Glossários Técnicos",
    "🩺 Diagnóstico do Sistema (Doctor)"
])

# ------------------------------------------------------------------------------
# TAB 1: Central de Tradução
# ------------------------------------------------------------------------------
with tab_trans:
    col_up, col_queue = st.columns([1, 1], gap="large")

    with col_up:
        st.markdown("### 📤 Upload de Documentos")
        uploaded_files = st.file_uploader(
            "Arraste arquivos PDF para a fila:",
            type=["pdf"],
            accept_multiple_files=True
        )
        if uploaded_files:
            for uf in uploaded_files:
                save_path = config.input_dir / uf.name
                if not save_path.exists():
                    with open(save_path, "wb") as f:
                        f.write(uf.getbuffer())
                    st.success(f"Documento '{uf.name}' pronto para processamento!")

    with col_queue:
        st.markdown("### 📋 Fila de Entrada (`input_pdfs/`)")
        pdf_files = list(config.input_dir.glob("*.pdf"))
        
        if not pdf_files:
            st.info("Nenhum arquivo PDF na fila. Faça o upload ao lado.")
        else:
            for pdf in pdf_files:
                analysis = analyze_pdf(pdf)
                mono_exists = (config.output_dir / f"{pdf.stem}.mono.pdf").exists() or (config.output_dir / f"{pdf.stem}-mono.pdf").exists()
                status_html = "<span class='badge-ready'>CONCLUÍDO</span>" if mono_exists else "<span class='badge-pending'>PENDENTE</span>"
                
                st.markdown(f"""
                <div class="card-box">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #f1f5f9; font-size: 0.95rem;">📄 {pdf.name}</strong><br>
                            <span style="color: #94a3b8; font-size: 0.8rem; font-family: 'JetBrains Mono', monospace;">
                                {analysis.file_size_mb} MB · {analysis.total_pages} pág · ~{analysis.total_words:,} palavras
                            </span>
                        </div>
                        <div>{status_html}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🎯 Iniciar Processamento")
    
    if pdf_files:
        selected_file_name = st.selectbox("Selecione o arquivo:", options=[p.name for p in pdf_files])
        selected_file_path = config.input_dir / selected_file_name
        
        col_opt1, col_opt2 = st.columns([1, 2])
        with col_opt1:
            all_pages = st.checkbox("Processar documento completo", value=True)
            custom_pages = None
            if not all_pages:
                custom_pages = st.text_input("Intervalo de páginas (ex: 1-10 ou 50-70):", value="1-5")

        with col_opt2:
            st.markdown(f"**Motor / Provedor:** `{provider_name}` (`{model_id}`)")
            st.markdown(f"**Domínio:** `{selected_domain}` | **Threads:** `{concurrency}`")

        if st.button("🚀 Iniciar Tradução com Preservação de Layout", type="primary", use_container_width=True):
            st.markdown("---")
            st.markdown("#### ⏳ Execução em Tempo Real")
            
            prog_bar = st.progress(0, text="Iniciando engine vetorial...")
            log_container = st.empty()
            log_lines = []

            def handle_progress(data):
                pct = int(data.get("progress_pct", 0))
                curr = data.get("current_page", 0)
                tot = data.get("total_pages", 0)
                prog_bar.progress(min(max(pct, 0), 100), text=f"Traduzindo página {curr} de {tot} ({pct}% concluído)...")

            def handle_log(msg):
                log_lines.append(msg)
                log_container.code("\n".join(log_lines[-12:]), language="bash")

            job = TranslationJob(
                input_pdf=selected_file_path,
                provider=provider_name,
                model_id=model_id,
                pages=custom_pages,
                concurrency=concurrency,
                output_format=output_format,
                domain=selected_domain,
                on_progress=handle_progress,
                on_log=handle_log
            )

            with st.spinner("Processando páginas e reconstruindo diagramação..."):
                success = job.run()

            if success:
                st.success("🎉 Tradução finalizada com layout original preservado!")
                st.balloons()
            else:
                st.error(f"❌ Erro na execução: {job.error_message}")

# ------------------------------------------------------------------------------
# TAB 2: Diagnóstico & Custos
# ------------------------------------------------------------------------------
with tab_diag:
    st.markdown("### 📊 Análise de Volume & Estimativas de Custo")
    pdf_files = list(config.input_dir.glob("*.pdf"))
    if pdf_files:
        diag_file = st.selectbox("Selecione o documento para análise:", options=[p.name for p in pdf_files], key="diag_sel")
        analysis = analyze_pdf(config.input_dir / diag_file)

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total de Páginas", f"{analysis.total_pages}")
        col_m2.metric("Tamanho do Arquivo", f"{analysis.file_size_mb} MB")
        col_m3.metric("Contagem de Palavras", f"{analysis.total_words:,}")
        col_m4.metric("Tokens de IA Estimados", f"~{analysis.estimated_tokens:,}")

        st.markdown("#### 💰 Matriz Comparativa de Custo por Modelo")
        cost_data = []
        for m in available_models:
            costs = analysis.calculate_cost(m["cost_in"], m["cost_out"])
            cost_data.append({
                "Modelo": m["name"],
                "Provedor": m["provider"],
                "Input / 1k Tok": f"${m['cost_in']:.6f}",
                "Output / 1k Tok": f"${m['cost_out']:.6f}",
                "Custo Total (USD)": f"${costs['total_cost_usd']:.4f}",
                "Custo Estimado (BRL)": f"R$ {costs['total_cost_usd'] * 5.8:.2f}"
            })
        st.dataframe(cost_data, use_container_width=True)
    else:
        st.info("Adicione arquivos em `input_pdfs/` para exibir as métricas de diagnóstico.")

# ------------------------------------------------------------------------------
# TAB 3: Repositório de Documentos
# ------------------------------------------------------------------------------
with tab_viewer:
    st.markdown("### 📂 Documentos Traduzidos (`output_translated/`)")
    output_files = list(config.output_dir.glob("*.pdf"))
    
    if not output_files:
        st.info("Nenhum documento traduzido no repositório. Execute a tradução na primeira aba.")
    else:
        for out_pdf in output_files:
            file_size = round(out_pdf.stat().st_size / (1024 * 1024), 2)
            is_dual = "dual" in out_pdf.name.lower()
            tag = "<span class='badge-pending'>DUAL (BILÍNGUE)</span>" if is_dual else "<span class='badge-ready'>MONO (100% PT)</span>"
            
            st.markdown(f"""
            <div class="card-box">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>📄 {out_pdf.name}</strong><br>
                        <span style="color: #94a3b8; font-size: 0.82rem; font-family: 'JetBrains Mono', monospace;">
                            Tamanho: {file_size} MB · Destino: output_translated/
                        </span>
                    </div>
                    <div>{tag}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with open(out_pdf, "rb") as f:
                st.download_button(
                    label=f"⬇️ Baixar {out_pdf.name}",
                    data=f,
                    file_name=out_pdf.name,
                    mime="application/pdf",
                    key=f"dl_{out_pdf.name}"
                )
            st.divider()

# ------------------------------------------------------------------------------
# TAB 4: Glossários Técnicos
# ------------------------------------------------------------------------------
with tab_glossary:
    st.markdown("### 📖 Glossários Técnicos e Terminologia Padronizada")
    st.caption("Termos técnicos preservados e injetados nos prompts de tradução para fidelidade normativa.")
    
    glossary_data = glossary_manager.get_glossary("aviation")
    if glossary_data:
        st.info(f"**Diretriz Aplicada:** {glossary_data.get('instructions')}")
        terms = glossary_data.get("terms", {})
        
        table_terms = [{"Termo Original (Inglês)": k, "Tradução Técnica Padronizada (pt-BR)": v} for k, v in terms.items()]
        st.dataframe(table_terms, use_container_width=True, height=420)

# ------------------------------------------------------------------------------
# TAB 5: Diagnóstico do Sistema (Doctor)
# ------------------------------------------------------------------------------
with tab_doctor:
    st.markdown("### 🩺 Subsystem Doctor & Integridade Operacional")
    st.caption("Auditoria em tempo real de dependências, pastas, permissões de gravação e conectividade.")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("#### 📁 Status dos Diretórios de Armazenamento")
        for folder in ["input_pdfs", "output_translated", "config", "logs", "temp"]:
            p = BASE_DIR / folder
            exists = p.exists()
            writable = os.access(p, os.W_OK) if exists else False
            status = "✅ OK (Gravável)" if (exists and writable) else "❌ Erro"
            st.markdown(f"- **`{folder}/`**: {status}")

    with col_d2:
        st.markdown("#### 🔑 Provedores de IA Configurados")
        keys = {
            "OpenRouter": bool(os.getenv("OPENROUTER_API_KEY", "").strip()),
            "DeepSeek Direct": bool(os.getenv("DEEPSEEK_API_KEY", "").strip()),
            "Google Gemini": bool(os.getenv("GEMINI_API_KEY", "").strip()),
            "Groq Whisper/Llama": bool(os.getenv("GROQ_API_KEY", "").strip()),
            "FreeLLM Local": True
        }
        for prov, active in keys.items():
            st.markdown(f"- **{prov}**: {'🟢 Ativo' if active else '⚪ Não configurado'}")
