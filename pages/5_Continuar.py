"""
Continuar Escrevendo — a IA continua seu texto mantendo seu estilo e voz.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from utils.storage import init_session_state, load_prompts, save_prompts, reset_prompt, get_chapters
from utils.ai_client import call_ai, PROVIDER_NAMES
from utils.components import model_selector

st.set_page_config(page_title="Continuar Escrevendo — Escritor", page_icon="✨", layout="wide")
init_session_state()

st.title("✨ Continuar Escrevendo")
st.markdown(
    "Travou? Cole o trecho onde parou e a IA continua no seu estilo, "
    "mantendo a voz, o tom e os personagens."
)

prompts = load_prompts()
prompt_data = prompts.get("continuar", {})

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    provider, model, temperature = model_selector("cont", default_temp=0.8)

    st.divider()
    st.subheader("Prompt")

    system_prompt = st.text_area(
        "System Prompt",
        value=prompt_data.get("system", ""),
        height=120,
        key="cont_system",
    )

    user_template = st.text_area(
        "Template (use {texto} e {num_palavras})",
        value=prompt_data.get("user_template", ""),
        height=200,
        key="cont_user_template",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Salvar Prompt", use_container_width=True):
            prompts["continuar"]["system"] = system_prompt
            prompts["continuar"]["user_template"] = user_template
            save_prompts(prompts)
            st.success("Salvo!")
    with col2:
        if st.button("Restaurar Padrão", use_container_width=True):
            reset_prompt("continuar")
            st.success("Restaurado!")
            st.rerun()

# ─── Área principal ───────────────────────────────────────────────────────────
source_tab, free_tab = st.tabs(["📚 De um Capítulo", "✏️ Texto Livre"])

context_text = ""

with source_tab:
    chapters = get_chapters()
    if not chapters:
        st.info("Crie capítulos no Editor primeiro.")
    else:
        chapter_options = {ch["title"]: ch["content"] for ch in chapters}
        selected = st.selectbox("Capítulo:", list(chapter_options.keys()), key="cont_chapter")
        chapter_text = chapter_options[selected]
        wc = len(chapter_text.split())
        st.caption(f"{wc:,} palavras")

        use_last = st.checkbox("Usar apenas os últimos N parágrafos (recomendado para capítulos longos)", value=True)
        if use_last:
            n_paras = st.number_input("Quantos parágrafos finais usar:", min_value=1, max_value=20, value=5)
            paras = [p for p in chapter_text.split("\n\n") if p.strip()]
            context_text = "\n\n".join(paras[-n_paras:])
            st.caption(f"Usando {len(context_text.split())} palavras dos últimos {n_paras} parágrafos.")
        else:
            context_text = chapter_text

with free_tab:
    context_text_free = st.text_area(
        "Cole o texto onde parou:",
        height=300,
        placeholder="Cole aqui o texto. A IA vai continuar a partir do último ponto...",
        key="cont_free_text",
    )
    if context_text_free.strip():
        context_text = context_text_free

# Configurações de geração
st.divider()
col_words, col_style = st.columns(2)
with col_words:
    num_words = st.select_slider(
        "Quantas palavras gerar:",
        options=[100, 200, 300, 500, 700, 1000],
        value=300,
    )
with col_style:
    style_hint = st.text_input(
        "Dica de direção (opcional):",
        placeholder="Ex: cena de confronto, clima tenso, revelar segredo...",
    )

num_variations = st.radio(
    "Número de continuações:",
    [1, 2, 3],
    horizontal=True,
    help="Gere múltiplas opções e escolha a melhor.",
)

run_btn = st.button(
    "✨ Continuar",
    type="primary",
    disabled=not context_text.strip(),
)

# ─── Execução ────────────────────────────────────────────────────────────────
if run_btn and context_text.strip():
    api_key = st.session_state.get("api_keys", {}).get(provider, "")
    if not api_key:
        st.error(f"Chave de API para **{PROVIDER_NAMES[provider]}** não configurada. Vá em ⚙️ Configurações.")
    else:
        current_system = st.session_state.get("cont_system", system_prompt)
        current_template = st.session_state.get("cont_user_template", user_template)

        direction = f"\n\nDireção desejada: {style_hint}" if style_hint else ""
        user_msg = current_template.replace("{texto}", context_text).replace(
            "{num_palavras}", str(num_words)
        ) + direction

        if num_variations > 1:
            user_msg += f"\n\nApresente {num_variations} variações distintas, numeradas."

        with st.spinner("Gerando continuação..."):
            try:
                result = call_ai(
                    provider=provider,
                    model=model,
                    user_prompt=user_msg,
                    system_prompt=current_system,
                    temperature=temperature,
                    max_tokens=num_words * 2 + 500,
                )
                st.session_state["cont_result"] = result
            except Exception as e:
                st.error(f"Erro: {e}")

# ─── Resultado ────────────────────────────────────────────────────────────────
if "cont_result" in st.session_state:
    st.divider()
    st.subheader("Continuação gerada")
    result = st.session_state["cont_result"]
    st.markdown(result)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Baixar texto",
            data=result.encode("utf-8"),
            file_name="continuacao.txt",
            mime="text/plain; charset=utf-8",
            key="dl_cont",
        )
    with col2:
        if st.button("🔄 Gerar novamente", key="cont_regen"):
            if "cont_result" in st.session_state:
                del st.session_state["cont_result"]
            st.rerun()
