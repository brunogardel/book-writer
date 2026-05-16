"""
Configurações — API keys, modelo padrão, prompts editáveis e exportação.
"""

import sys
from pathlib import Path
import json

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from utils.storage import (
    init_session_state,
    load_settings,
    save_settings,
    load_prompts,
    save_prompts,
    reset_prompt,
    load_book,
    get_full_text,
    DEFAULT_PROMPTS,
)
from utils.ai_client import AVAILABLE_MODELS, PROVIDER_NAMES

st.set_page_config(page_title="Configurações — Escritor", page_icon="⚙️", layout="wide")
init_session_state()

st.title("⚙️ Configurações")

tab_api, tab_model, tab_prompts, tab_export = st.tabs(
    ["🔑 Chaves de API", "🤖 Modelo Padrão", "📝 Prompts", "📤 Exportar"]
)

# ─── Chaves de API ────────────────────────────────────────────────────────────
with tab_api:
    st.subheader("Chaves de API")
    st.markdown(
        "Configure suas chaves de API. Elas são armazenadas **localmente** em `data/settings.json` "
        "e nunca são enviadas a terceiros além dos provedores de IA que você usa."
    )

    api_keys = st.session_state.get("api_keys", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**OpenAI**")
        openai_key = st.text_input(
            "Chave OpenAI",
            value=api_keys.get("openai", ""),
            type="password",
            placeholder="sk-...",
            key="cfg_openai_key",
        )
        if openai_key:
            st.caption("Modelos disponíveis: " + ", ".join(AVAILABLE_MODELS["openai"]))

        st.divider()

        st.markdown("**Google Gemini**")
        gemini_key = st.text_input(
            "Chave Google AI",
            value=api_keys.get("gemini", ""),
            type="password",
            placeholder="AIza...",
            key="cfg_gemini_key",
        )
        if gemini_key:
            st.caption("Modelos disponíveis: " + ", ".join(AVAILABLE_MODELS["gemini"]))

    with col2:
        st.markdown("**Anthropic (Claude)**")
        anthropic_key = st.text_input(
            "Chave Anthropic",
            value=api_keys.get("anthropic", ""),
            type="password",
            placeholder="sk-ant-...",
            key="cfg_anthropic_key",
        )
        if anthropic_key:
            st.caption("Modelos disponíveis: " + ", ".join(AVAILABLE_MODELS["anthropic"]))

    st.divider()
    if st.button("💾 Salvar Chaves de API", type="primary"):
        new_keys = {}
        if openai_key:
            new_keys["openai"] = openai_key
        if anthropic_key:
            new_keys["anthropic"] = anthropic_key
        if gemini_key:
            new_keys["gemini"] = gemini_key

        st.session_state["api_keys"] = new_keys
        settings = load_settings()
        settings["api_keys"] = new_keys
        save_settings(settings)
        st.success("Chaves salvas com sucesso!")

    st.info(
        "Precisa de uma chave? "
        "OpenAI: platform.openai.com | "
        "Anthropic: console.anthropic.com | "
        "Google: aistudio.google.com"
    )

# ─── Modelo Padrão ────────────────────────────────────────────────────────────
with tab_model:
    st.subheader("Modelo de IA Padrão")
    st.markdown(
        "Define o provider e modelo usados por padrão em todas as ferramentas. "
        "Cada ferramenta também permite ajuste individual."
    )

    settings = load_settings()

    current_provider = settings.get("ai_provider", "anthropic")
    current_model = settings.get("ai_model", "claude-3-5-sonnet-20241022")
    current_temp = settings.get("temperature", 0.7)
    current_tokens = settings.get("max_tokens", 4096)

    col1, col2 = st.columns(2)
    with col1:
        provider = st.selectbox(
            "Provider padrão:",
            options=list(AVAILABLE_MODELS.keys()),
            format_func=lambda x: PROVIDER_NAMES[x],
            index=list(AVAILABLE_MODELS.keys()).index(current_provider)
            if current_provider in AVAILABLE_MODELS
            else 1,
            key="cfg_provider",
        )

    with col2:
        model_list = AVAILABLE_MODELS[provider]
        default_model_idx = model_list.index(current_model) if current_model in model_list else 0
        model = st.selectbox(
            "Modelo padrão:",
            options=model_list,
            index=default_model_idx,
            key="cfg_model",
        )

    col3, col4 = st.columns(2)
    with col3:
        temperature = st.slider("Temperatura padrão:", 0.0, 1.0, current_temp, 0.05, key="cfg_temp")
    with col4:
        max_tokens = st.select_slider(
            "Máx. tokens padrão:",
            options=[1024, 2048, 4096, 8192],
            value=current_tokens,
            key="cfg_max_tokens",
        )

    if st.button("💾 Salvar Modelo Padrão", type="primary"):
        settings["ai_provider"] = provider
        settings["ai_model"] = model
        settings["temperature"] = temperature
        settings["max_tokens"] = max_tokens
        save_settings(settings)
        st.session_state["ai_provider"] = provider
        st.session_state["ai_model"] = model
        st.session_state["temperature"] = temperature
        st.session_state["max_tokens"] = max_tokens
        st.success("Configurações salvas!")

# ─── Prompts ──────────────────────────────────────────────────────────────────
with tab_prompts:
    st.subheader("Editar Prompts dos Agentes")
    st.markdown(
        "Customize os prompts de cada ferramenta. "
        "As alterações são salvas e persistem entre sessões."
    )

    prompts = load_prompts()

    PROMPT_LABELS = {
        "anti_ia": "🤖 Anti-IA",
        "analise_capitulo": "🔍 Análise de Capítulo",
        "analise_livro": "📚 Análise do Livro",
        "continuar": "✨ Continuar Escrevendo",
        "reescrever": "🔄 Reescrever",
        "brainstorm": "💡 Brainstorm",
        "biblia_geracao": "📖 Extração por Capítulo (Bíblia)",
        "biblia_merge": "🔀 Consolidação da Bíblia (Merge)",
    }

    selected_prompt_key = st.selectbox(
        "Selecione o prompt para editar:",
        options=list(PROMPT_LABELS.keys()),
        format_func=lambda k: PROMPT_LABELS[k],
        key="cfg_prompt_select",
    )

    prompt_data = prompts.get(selected_prompt_key, {})
    default_data = DEFAULT_PROMPTS.get(selected_prompt_key, {})

    st.markdown(f"**{PROMPT_LABELS[selected_prompt_key]}**")

    new_system = st.text_area(
        "System Prompt (instrução de sistema):",
        value=prompt_data.get("system", ""),
        height=150,
        key=f"cfg_sys_{selected_prompt_key}",
        help="Define o papel e personalidade da IA para esta ferramenta.",
    )

    new_template = st.text_area(
        "Template do usuário (use as variáveis entre chaves {}):",
        value=prompt_data.get("user_template", ""),
        height=300,
        key=f"cfg_tmpl_{selected_prompt_key}",
        help="Use {texto}, {objetivo}, {contexto}, {tema}, {num_palavras} conforme o agente.",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Salvar Prompt", type="primary", use_container_width=True):
            prompts[selected_prompt_key]["system"] = new_system
            prompts[selected_prompt_key]["user_template"] = new_template
            save_prompts(prompts)
            st.success("Prompt salvo!")

    with col2:
        if st.button("🔄 Restaurar Padrão", use_container_width=True):
            reset_prompt(selected_prompt_key)
            st.success("Restaurado para o padrão!")
            st.rerun()

    with col3:
        if st.button("👁️ Ver Padrão", use_container_width=True):
            with st.expander("Prompt padrão:", expanded=True):
                st.text("=== SYSTEM ===")
                st.text(default_data.get("system", ""))
                st.text("\n=== USER TEMPLATE ===")
                st.text(default_data.get("user_template", ""))

# ─── Exportar ─────────────────────────────────────────────────────────────────
with tab_export:
    st.subheader("Exportar Manuscrito")

    book = load_book()
    from utils.storage import get_chapters
    chapters = get_chapters()

    if not chapters:
        st.info("Nenhum capítulo para exportar. Escreva seu livro no Editor primeiro.")
    else:
        total_words = sum(len(c.get("content", "").split()) for c in chapters)
        st.metric("Total de palavras", f"{total_words:,}")

        # Exportar como TXT
        full_text = f"# {book.get('title', 'Meu Livro')}\n"
        if book.get("author"):
            full_text += f"Autor: {book['author']}\n"
        full_text += "\n\n"

        for ch in chapters:
            full_text += f"## {ch['title']}\n\n{ch.get('content', '')}\n\n---\n\n"

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇️ Exportar como TXT",
                data=full_text,
                file_name=f"{book.get('title', 'livro')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with col2:
            st.download_button(
                "⬇️ Exportar como Markdown",
                data=full_text,
                file_name=f"{book.get('title', 'livro')}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        # Exportar estrutura JSON
        st.divider()
        st.markdown("**Backup completo (JSON)**")
        st.caption("Inclui capítulos, bíblia do livro e configurações de prompts.")

        from utils.storage import load_bible
        backup = {
            "book": book,
            "bible": load_bible(),
            "prompts": load_prompts(),
        }
        st.download_button(
            "⬇️ Baixar Backup Completo (JSON)",
            data=json.dumps(backup, ensure_ascii=False, indent=2),
            file_name="backup_escritor.json",
            mime="application/json",
        )
