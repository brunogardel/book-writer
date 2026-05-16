"""
Análise do Livro Inteiro — visão editorial macro do manuscrito completo.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from utils.storage import (
    init_session_state,
    load_prompts,
    save_prompts,
    reset_prompt,
    get_chapters,
    get_full_text,
    load_book,
)
from utils.ai_client import call_ai, PROVIDER_NAMES
from utils.components import model_selector

st.set_page_config(page_title="Análise do Livro — Escritor", page_icon="📚", layout="wide")
init_session_state()

st.title("📚 Análise do Livro")
st.markdown(
    "Análise editorial completa do manuscrito: estrutura narrativa, temas, arcos de personagens, "
    "consistência, potencial de mercado e recomendações prioritárias de revisão."
)

prompts = load_prompts()
prompt_data = prompts.get("analise_livro", {})

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    provider, model, temperature = model_selector("al", default_temp=0.3)
    max_tokens = st.slider("Máx. tokens de resposta", 1024, 8192, 4096, 256, key="al_max_tokens")

    st.divider()
    st.subheader("Prompt do Editor")

    system_prompt = st.text_area(
        "System Prompt",
        value=prompt_data.get("system", ""),
        height=120,
        key="al_system",
    )

    user_template = st.text_area(
        "Template (use {texto})",
        value=prompt_data.get("user_template", ""),
        height=280,
        key="al_user_template",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Salvar Prompt", use_container_width=True):
            prompts["analise_livro"]["system"] = system_prompt
            prompts["analise_livro"]["user_template"] = user_template
            save_prompts(prompts)
            st.success("Salvo!")
    with col2:
        if st.button("Restaurar Padrão", use_container_width=True):
            reset_prompt("analise_livro")
            st.success("Restaurado!")
            st.rerun()

# ─── Área principal ───────────────────────────────────────────────────────────
book = load_book()
chapters = get_chapters()

# Estatísticas do manuscrito
total_words = sum(len(c.get("content", "").split()) for c in chapters)
total_chars = sum(len(c.get("content", "")) for c in chapters)
pages_est = max(1, total_words // 250)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Capítulos", len(chapters))
with col2:
    st.metric("Palavras", f"{total_words:,}")
with col3:
    st.metric("Páginas (~250 p/pág)", pages_est)

st.divider()

# Seleção: livro completo ou capítulos específicos
analysis_mode = st.radio(
    "O que analisar:",
    ["📚 Livro completo (todos os capítulos)", "🔀 Selecionar capítulos específicos"],
    horizontal=True,
)

text_to_analyze = ""

if analysis_mode.startswith("📚"):
    if not chapters:
        st.warning("Nenhum capítulo encontrado. Escreva seu livro no Editor primeiro.")
    else:
        full_text = get_full_text()
        word_count = len(full_text.split())
        st.info(
            f"Serão analisados **{len(chapters)} capítulos** ({word_count:,} palavras). "
            "Livros muito longos podem exceder o limite de contexto do modelo — "
            "nesse caso, use a análise por capítulos selecionados."
        )
        text_to_analyze = full_text
else:
    if not chapters:
        st.warning("Nenhum capítulo disponível.")
    else:
        selected_titles = st.multiselect(
            "Selecione os capítulos:",
            options=[ch["title"] for ch in chapters],
            default=[ch["title"] for ch in chapters],
        )
        selected_chapters = [c for c in chapters if c["title"] in selected_titles]
        parts = []
        for ch in selected_chapters:
            parts.append(f"# {ch['title']}\n\n{ch.get('content', '')}")
        text_to_analyze = "\n\n---\n\n".join(parts)

        if text_to_analyze:
            wc = len(text_to_analyze.split())
            st.caption(f"{len(selected_chapters)} capítulos selecionados · {wc:,} palavras")

# Contexto adicional (sinopse, gênero)
with st.expander("Contexto adicional para o editor (opcional mas recomendado)"):
    ctx_genre = st.text_input("Gênero literário:", value=book.get("genre", ""))
    ctx_synopsis = st.text_area(
        "Sinopse / intenção do livro:",
        value=book.get("synopsis", ""),
        height=100,
        placeholder="Descreva brevemente a história e seus objetivos com este livro...",
    )

    if st.button("Salvar contexto no livro"):
        book["genre"] = ctx_genre
        book["synopsis"] = ctx_synopsis
        from utils.storage import save_book
        save_book(book)
        st.success("Contexto salvo!")

run_btn = st.button(
    "📚 Analisar Livro",
    type="primary",
    disabled=not text_to_analyze.strip(),
)


def run_analysis(text: str):
    api_key = st.session_state.get("api_keys", {}).get(provider, "")
    if not api_key:
        st.error(
            f"Chave de API para **{PROVIDER_NAMES[provider]}** não configurada. "
            "Vá em ⚙️ Configurações."
        )
        return

    # Adiciona contexto ao texto se fornecido
    context_header = ""
    if ctx_genre:
        context_header += f"Gênero: {ctx_genre}\n"
    if ctx_synopsis:
        context_header += f"Sinopse: {ctx_synopsis}\n"
    if context_header:
        text = f"{context_header}\n---\n\n{text}"

    current_system = st.session_state.get("al_system", system_prompt)
    current_template = st.session_state.get("al_user_template", user_template)
    user_msg = current_template.replace("{texto}", text)

    with st.spinner("Analisando o manuscrito... isso pode levar alguns minutos."):
        try:
            result = call_ai(
                provider=provider,
                model=model,
                user_prompt=user_msg,
                system_prompt=current_system,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            st.session_state["al_result"] = result
        except Exception as e:
            st.error(f"Erro: {e}")


if run_btn and text_to_analyze.strip():
    run_analysis(text_to_analyze)

# ─── Resultado ────────────────────────────────────────────────────────────────
if "al_result" in st.session_state:
    st.divider()
    st.subheader("Relatório Editorial")
    result_text = st.session_state["al_result"]
    st.markdown(result_text)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "⬇️ Baixar relatório (.txt)",
            data=result_text.encode("utf-8"),
            file_name="analise_livro.txt",
            mime="text/plain; charset=utf-8",
            key="dl_al_txt",
        )
    with col_dl2:
        st.download_button(
            "⬇️ Baixar relatório (.md)",
            data=result_text.encode("utf-8"),
            file_name="analise_livro.md",
            mime="text/markdown",
            key="dl_al_md",
        )
