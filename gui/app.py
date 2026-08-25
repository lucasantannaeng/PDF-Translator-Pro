"""
Streamlit Web Interface for PDF-Translator-Pro
Modern dark-themed UI for PDF layout-preserving AI translation suite.
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
    page_title="PDF-Translator-Pro | IA Translation Suite",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Slate & Cyan High-Density Interface)
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stMetric {
        background-color: #1e293b;
        padding: 12px 18px;
        border-radius: 10px;
        border: 1px solid #334155;
    }
    .card-box {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-bottom: 16px;
    }
    .badge-ready {
        background-color: #064e3b;
        color: #34d399;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-pending {
        background-color: #78350f;
        color: #fbbf24;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    h1, h2, h3 {
        color: #38bdf8 !important;
        font-family: 'Inter', sans-serif;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
    }
</style>
""", unsafe_allow_html=True)


# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/38bdf8/pdf-2.png", width=64)
    st.title("PDF-Translator-Pro")
    st.caption("Suíte de Tradução com Preservação de Layout")
    st.divider()

    st.subheader("⚙️ Configurações da IA")
    
    available_models = router.get_available_models()
    model_options = {f"{m['name']} ({m['provider']})": m for m in available_models}
    
    selected_model_label = st.selectbox(
        "Modelo de Tradução:",
        options=list(model_options.keys()),
        index=0
    )
    selected_model_info = model_options[selected_model_label]
    
    provider_name = selected_model_info["provider"]
    model_id = selected_model_info["model_id"]

    # Test API button
    if st.button("🔌 Testar Conexão com API", use_container_width=True):
        with st.spinner("Testando..."):
            success, msg, elapsed = router.test_connection(provider_name, model_id)
            if success:
                st.success(f"✅ Conectado em {elapsed}s!")
                st.caption(msg)
            else:
                st.error("❌ Falha na conexão:")
                st.caption(msg)

    st.divider()
    st.subheader("🛠️ Parâmetros Operacionais")
    concurrency = st.slider("Threads Concorrentes:", min_value=1, max_value=16, value=config.concurrency)
    
    glossaries = list(glossary_manager._cache.keys()) or ["aviation"]
    selected_domain = st.selectbox("Glossário Técnico de Domínio:", options=glossaries, index=0)
    
    output_format = st.radio("Formato de Saída:", options=["both", "mono", "dual"], format_func=lambda x: {
        "both": "Ambos (Mono traduzido + Dual bilíngue)",
        "mono": "Apenas Traduzido (Mono)",
        "dual": "Apenas Bilíngue Lado a Lado (Dual)"
    }[x])


# Header
st.title("📑 Central de Tradução de PDFs")
st.markdown("Tradução técnica de alta fidelidade mantendo **layout, diagramação, tabelas e fórmulas** intactas.")

# Tabs
tab_trans, tab_diag, tab_viewer, tab_glossary = st.tabs([
    "🚀 Traduzir Arquivos", 
    "📊 Diagnóstico & Custos", 
    "📂 Documentos Traduzidos", 
    "📖 Glossário Aeronáutico & Domínio"
])

# ------------------------------------------------------------------------------
# TAB 1: Traduzir Arquivos
# ------------------------------------------------------------------------------
with tab_trans:
    col_up, col_queue = st.columns([1, 1], gap="medium")

    with col_up:
        st.markdown("### 📤 Upload de Novos PDFs")
        uploaded_files = st.file_uploader(
            "Arraste qualquer PDF para adicionar à fila de tradução:",
            type=["pdf"],
            accept_multiple_files=True
        )
        if uploaded_files:
            for uf in uploaded_files:
                save_path = config.input_dir / uf.name
                if not save_path.exists():
                    with open(save_path, "wb") as f:
                        f.write(uf.getbuffer())
                    st.success(f"Arquivo '{uf.name}' adicionado à fila!")

    with col_queue:
        st.markdown("### 📋 Fila de Entrada (`input_pdfs/`)")
        pdf_files = list(config.input_dir.glob("*.pdf"))
        
        if not pdf_files:
            st.info("Nenhum PDF encontrado em `input_pdfs/`. Faça upload ao lado.")
        else:
            for pdf in pdf_files:
                analysis = analyze_pdf(pdf)
                mono_exists = (config.output_dir / f"{pdf.stem}.mono.pdf").exists() or (config.output_dir / f"{pdf.stem}-mono.pdf").exists()
                status_html = "<span class='badge-ready'>PRONTO</span>" if mono_exists else "<span class='badge-pending'>PENDENTE</span>"
                
                st.markdown(f"""
                <div class="card-box" style="padding: 12px 16px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>📄 {pdf.name}</strong><br>
                            <small style="color: #94a3b8;">{analysis.file_size_mb} MB | {analysis.total_pages} páginas | ~{analysis.total_words:,} palavras</small>
                        </div>
                        <div>{status_html}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### 🎯 Executar Tradução")
    
    if pdf_files:
        selected_file_name = st.selectbox("Selecione o PDF para traduzir:", options=[p.name for p in pdf_files])
        selected_file_path = config.input_dir / selected_file_name
        
        col_opt1, col_opt2 = st.columns([1, 2])
        with col_opt1:
            all_pages = st.checkbox("Traduzir documento completo", value=True)
            custom_pages = None
            if not all_pages:
                custom_pages = st.text_input("Intervalo de páginas (ex: 1-10 ou 50-70):", value="1-5")

        with col_opt2:
            st.markdown(f"**Provedor Selecionado:** `{provider_name}` ({model_id})")
            st.markdown(f"**Glossário:** `{selected_domain}` | **Threads:** `{concurrency}`")

        if st.button("🚀 Iniciar Tradução Agora", type="primary", use_container_width=True):
            st.markdown("---")
            st.markdown("#### ⏳ Progresso em Tempo Real")
            
            prog_bar = st.progress(0, text="Iniciando motor de tradução...")
            status_text = st.empty()
            log_container = st.empty()
            log_lines = []

            def handle_progress(data):
                pct = int(data.get("progress_pct", 0))
                curr = data.get("current_page", 0)
                tot = data.get("total_pages", 0)
                prog_bar.progress(min(max(pct, 0), 100), text=f"Traduzindo página {curr} de {tot} ({pct}%)...")

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

            with st.spinner("Processando páginas e remontando layout..."):
                success = job.run()

            if success:
                st.success("🎉 Tradução concluída com sucesso!")
                st.balloons()
            else:
                st.error(f"❌ Ocorreu um erro durante a tradução: {job.error_message}")


# ------------------------------------------------------------------------------
# TAB 2: Diagnóstico & Custos
# ------------------------------------------------------------------------------
with tab_diag:
    st.markdown("### 📊 Análise Estrutural e Estimativas de Custo")
    pdf_files = list(config.input_dir.glob("*.pdf"))
    if pdf_files:
        diag_file = st.selectbox("Escolha o arquivo para analisar:", options=[p.name for p in pdf_files], key="diag_sel")
        analysis = analyze_pdf(config.input_dir / diag_file)

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Páginas", analysis.total_pages)
        col_m2.metric("Tamanho", f"{analysis.file_size_mb} MB")
        col_m3.metric("Total de Palavras", f"{analysis.total_words:,}")
        col_m4.metric("Tokens Estimados", f"~{analysis.estimated_tokens:,}")

        st.markdown("#### 💰 Estimativa de Custo por Modelo de IA")
        cost_data = []
        for m in available_models:
            costs = analysis.calculate_cost(m["cost_in"], m["cost_out"])
            cost_data.append({
                "Modelo": m["name"],
                "Provedor": m["provider"],
                "Custo Entrada/1k": f"${m['cost_in']:.6f}",
                "Custo Saída/1k": f"${m['cost_out']:.6f}",
                "Custo Total (USD)": f"${costs['total_cost_usd']:.4f}",
                "Custo Estimado (BRL)": f"R$ {costs['total_cost_usd'] * 5.8:.2f}"
            })
        st.dataframe(cost_data, use_container_width=True)
    else:
        st.info("Adicione PDFs em `input_pdfs/` para visualizar o diagnóstico.")


# ------------------------------------------------------------------------------
# TAB 3: Documentos Traduzidos
# ------------------------------------------------------------------------------
with tab_viewer:
    st.markdown("### 📂 Arquivos Traduzidos Prontos (`output_translated/`)")
    output_files = list(config.output_dir.glob("*.pdf"))
    
    if not output_files:
        st.info("Nenhum PDF traduzido gerado ainda. Execute uma tradução na primeira aba.")
    else:
        for out_pdf in output_files:
            file_size = round(out_pdf.stat().st_size / (1024 * 1024), 2)
            col_f1, col_f2 = st.columns([3, 1])
            with col_f1:
                st.markdown(f"📄 **{out_pdf.name}** ({file_size} MB)")
            with col_f2:
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
# TAB 4: Glossário Técnico
# ------------------------------------------------------------------------------
with tab_glossary:
    st.markdown("### 📖 Glossário de Engenharia e Aviação (OM-B)")
    st.caption("Terminologias padronizadas aplicadas automaticamente nas instruções de prompt.")
    
    glossary_data = glossary_manager.get_glossary("aviation")
    if glossary_data:
        st.info(f"**Diretriz:** {glossary_data.get('instructions')}")
        terms = glossary_data.get("terms", {})
        
        table_terms = [{"Termo Original (Inglês)": k, "Tradução Técnica Padronizada (Português pt-BR)": v} for k, v in terms.items()]
        st.dataframe(table_terms, use_container_width=True, height=400)
