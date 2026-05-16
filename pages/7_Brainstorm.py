"""
Brainstorm — gerador de ideias para trama, personagens, cenas e conflitos.
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
    load_book,
    get_chapters,
)
from utils.ai_client import call_ai, call_ai_for_task, PROVIDER_NAMES
from utils.components import model_selector, show_model_info

st.set_page_config(page_title="Brainstorm — Escritor", page_icon="💡", layout="wide")
init_session_state()

st.title("💡 Brainstorm")
st.markdown(
    "Gere ideias criativas para trama, personagens, cenas, conflitos, "
    "diálogos, reviravoltas e muito mais."
)

# Mostra modelo recomendado e custo
use_recommended_model, _ = show_model_info("brainstorm")

prompts = load_prompts()
prompt_data = prompts.get("brainstorm", {})

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    provider, model, temperature = model_selector("bs", default_temp=0.9)

    st.divider()
    st.subheader("Prompt")

    system_prompt = st.text_area(
        "System Prompt",
        value=prompt_data.get("system", ""),
        height=120,
        key="bs_system",
    )

    user_template = st.text_area(
        "Template (use {contexto} e {tema})",
        value=prompt_data.get("user_template", ""),
        height=220,
        key="bs_user_template",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Salvar Prompt", use_container_width=True):
            prompts["brainstorm"]["system"] = system_prompt
            prompts["brainstorm"]["user_template"] = user_template
            save_prompts(prompts)
            st.success("Salvo!")
    with col2:
        if st.button("Restaurar Padrão", use_container_width=True):
            reset_prompt("brainstorm")
            st.success("Restaurado!")
            st.rerun()

# ─── Contexto do livro ────────────────────────────────────────────────────────
book = load_book()
chapters = get_chapters()

with st.expander("Contexto do livro (alimenta o brainstorm)", expanded=True):
    context_mode = st.radio(
        "Usar como contexto:",
        ["Sinopse do livro", "Capítulo específico", "Texto livre"],
        horizontal=True,
    )

    if context_mode == "Sinopse do livro":
        synopsis = book.get("synopsis", "")
        if not synopsis:
            st.warning("Sem sinopse cadastrada. Adicione em ⚙️ Configurações ou no Editor.")
        context = f"Título: {book.get('title', '')}\nGênero: {book.get('genre', '')}\nSinopse: {synopsis}"

    elif context_mode == "Capítulo específico":
        if not chapters:
            st.info("Nenhum capítulo disponível.")
            context = ""
        else:
            ch_names = {c["title"]: c["content"] for c in chapters}
            sel = st.selectbox("Capítulo:", list(ch_names.keys()), key="bs_chapter")
            ch_text = ch_names[sel]
            # Usa apenas o resumo ou os primeiros 1000 chars para não sobrecarregar
            context = f"Contexto do capítulo '{sel}':\n{ch_text[:1500]}"

    else:
        context = st.text_area(
            "Descreva o contexto da história:",
            height=100,
            placeholder="Ex: história de ficção científica em 2150, protagonista é uma IA que ganha consciência...",
            key="bs_free_context",
        )

# ─── Tema do brainstorm ───────────────────────────────────────────────────────
st.subheader("O que quer brainstormar?")

BRAINSTORM_CATEGORIES = {
    "Trama e Plot": [
        "Próximos acontecimentos da trama",
        "Reviravolta inesperada",
        "Como resolver o conflito central",
        "Cenas de virada de capítulo",
        "Como escalar a tensão",
    ],
    "Personagens": [
        "Desenvolvimento do protagonista",
        "Antagonista mais complexo",
        "Motivações internas do personagem",
        "Arco de transformação",
        "Novo personagem secundário",
    ],
    "Cenas e Ambientes": [
        "Cena de confronto dramático",
        "Cena de revelação",
        "Abertura de capítulo impactante",
        "Fechamento de capítulo com ganchos",
        "Descrição de ambiente evocativo",
    ],
    "Diálogo e Voz": [
        "Diálogo de conflito entre personagens",
        "Linha de abertura marcante",
        "Monólogo interno revelador",
        "Subtexto em conversa",
    ],
    "Temas e Simbolismo": [
        "Metáforas visuais para o tema central",
        "Símbolos recorrentes",
        "Motivos literários",
        "Como aprofundar o tema",
    ],
}

category = st.selectbox("Categoria:", list(BRAINSTORM_CATEGORIES.keys()), key="bs_category")
preset_topics = BRAINSTORM_CATEGORIES[category]

topic_choice = st.selectbox(
    "Tópico:",
    preset_topics + ["Personalizado..."],
    key="bs_topic",
)

if topic_choice == "Personalizado...":
    brainstorm_theme = st.text_input(
        "Descreva o que quer explorar:",
        placeholder="Ex: como dois personagens rivais podem desenvolver aliança improvável...",
        key="bs_custom_theme",
    )
else:
    brainstorm_theme = topic_choice

num_ideas = st.slider("Número de ideias:", 3, 10, 5, key="bs_num_ideas")

run_btn = st.button(
    "💡 Gerar Ideias",
    type="primary",
    disabled=not (context and brainstorm_theme),
)

# ─── Execução ────────────────────────────────────────────────────────────────
if run_btn:
    current_system = st.session_state.get("bs_system", system_prompt)
    current_template = st.session_state.get("bs_user_template", user_template)

    user_msg = (
        current_template
        .replace("{contexto}", context)
        .replace("{tema}", brainstorm_theme)
    )
    user_msg += f"\n\nApresente exatamente {num_ideas} ideias distintas e desenvolvidas."

    with st.spinner("Gerando ideias..."):
        try:
            result = None
            # Usa modelo recomendado ou configuração manual
            if use_recommended_model:
                result = call_ai_for_task(
                    task="brainstorm",
                    user_prompt=user_msg,
                    system_prompt=current_system,
                    temperature=temperature,
                    max_tokens=3000,
                    use_recommended=True,
                )
            else:
                # Fallback: usa configuração manual da sidebar
                api_key = st.session_state.get("api_keys", {}).get(provider, "")
                if not api_key:
                    st.error(
                        f"Chave de API para **{PROVIDER_NAMES[provider]}** não configurada. "
                        "Vá em ⚙️ Configurações."
                    )
                else:
                    result = call_ai(
                        provider=provider,
                        model=model,
                        user_prompt=user_msg,
                        system_prompt=current_system,
                        temperature=temperature,
                        max_tokens=3000,
                    )
            if result:
                if "bs_history" not in st.session_state:
                    st.session_state["bs_history"] = []
                st.session_state["bs_history"].append({
                    "theme": brainstorm_theme,
                    "result": result,
                })
        except Exception as e:
            st.error(f"Erro: {e}")

# ─── Resultado ────────────────────────────────────────────────────────────────
if "bs_history" in st.session_state and st.session_state["bs_history"]:
    st.divider()
    history = st.session_state["bs_history"]

    if len(history) > 1:
        st.caption(f"{len(history)} sessões de brainstorm nesta sessão.")

    for i, session in enumerate(reversed(history)):
        with st.expander(f"{'Mais recente' if i == 0 else f'Sessão {len(history) - i}'}: {session['theme']}", expanded=(i == 0)):
            st.markdown(session["result"])
            st.download_button(
                "⬇️ Baixar ideias",
                data=session["result"].encode("utf-8"),
                file_name=f"brainstorm_{i+1}.txt",
                mime="text/plain; charset=utf-8",
                key=f"bs_dl_{i}",
            )

    if st.button("🗑️ Limpar histórico"):
        del st.session_state["bs_history"]
        st.rerun()
