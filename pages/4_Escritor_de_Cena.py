"""
Escritor de Cena — gera prosa em dois passos:
  1. Beat Sheet  (estrutura dramática editável)
  2. Prosa Final (expansão com voz do autor)
Usa o final do capítulo selecionado como contexto de continuidade.
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
    save_chapter,
)
from utils.ai_client import call_ai, PROVIDER_NAMES
from utils.components import model_selector

st.set_page_config(page_title="Escritor de Cena — Escritor", page_icon="🎬", layout="wide")
init_session_state()

st.title("🎬 Escritor de Cena")
st.markdown(
    "Escreva uma cena em dois passos: primeiro gere o **beat sheet** (estrutura dramática), "
    "edite-o se quiser, depois expanda para **prosa** com a voz do narrador."
)

prompts = load_prompts()
beats_data = prompts.get("escrita_cena_beats", {})
prosa_data = prompts.get("escrita_cena_prosa", {})

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    provider, model, temperature = model_selector("cena", default_temp=0.7)

    st.divider()
    st.subheader("Prompts dos Agentes")

    with st.expander("Beat Sheet"):
        beats_system = st.text_area(
            "System",
            value=beats_data.get("system", ""),
            height=200,
            key="cena_beats_system",
        )
        beats_template = st.text_area(
            "Template (use {descricao}, {contexto}, {num_palavras})",
            value=beats_data.get("user_template", ""),
            height=200,
            key="cena_beats_template",
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Salvar", key="save_beats_prompt", use_container_width=True):
                prompts["escrita_cena_beats"]["system"] = beats_system
                prompts["escrita_cena_beats"]["user_template"] = beats_template
                save_prompts(prompts)
                st.success("Salvo!")
        with col2:
            if st.button("Restaurar", key="reset_beats_prompt", use_container_width=True):
                reset_prompt("escrita_cena_beats")
                st.success("Restaurado!")
                st.rerun()

    with st.expander("Prosa"):
        prosa_system = st.text_area(
            "System",
            value=prosa_data.get("system", ""),
            height=200,
            key="cena_prosa_system",
        )
        prosa_template = st.text_area(
            "Template (use {beats}, {contexto}, {num_palavras})",
            value=prosa_data.get("user_template", ""),
            height=200,
            key="cena_prosa_template",
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Salvar", key="save_prosa_prompt", use_container_width=True):
                prompts["escrita_cena_prosa"]["system"] = prosa_system
                prompts["escrita_cena_prosa"]["user_template"] = prosa_template
                save_prompts(prompts)
                st.success("Salvo!")
        with col2:
            if st.button("Restaurar", key="reset_prosa_prompt", use_container_width=True):
                reset_prompt("escrita_cena_prosa")
                st.success("Restaurado!")
                st.rerun()


# ─── Helpers ──────────────────────────────────────────────────────────────────
_CONTEXT_CHARS = 1500  # últimos N caracteres do capítulo como contexto


def _get_context(chapter_content: str) -> str:
    """Retorna as últimas linhas do capítulo para uso como contexto."""
    if len(chapter_content) <= _CONTEXT_CHARS:
        return chapter_content.strip()
    excerpt = chapter_content[-_CONTEXT_CHARS:]
    # começa no primeiro parágrafo completo
    newline = excerpt.find("\n")
    if newline != -1:
        excerpt = excerpt[newline + 1:]
    return "[...]\n\n" + excerpt.strip()


def _call_beats(description: str, context: str, num_palavras: int) -> str | None:
    api_key = st.session_state.get("api_keys", {}).get(provider, "")
    if not api_key:
        st.error(
            f"Chave de API para **{PROVIDER_NAMES[provider]}** não configurada. "
            "Vá em ⚙️ Configurações."
        )
        return None

    system = st.session_state.get("cena_beats_system", beats_system)
    template = st.session_state.get("cena_beats_template", beats_template)
    user_msg = (
        template
        .replace("{descricao}", description)
        .replace("{contexto}", context)
        .replace("{num_palavras}", str(num_palavras))
    )
    max_tokens = st.session_state.get("max_tokens", 8192)
    try:
        return call_ai(
            provider=provider,
            model=model,
            user_prompt=user_msg,
            system_prompt=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        st.error(f"Erro: {e}")
        return None


def _call_prosa(beats_text: str, context: str, num_palavras: int) -> str | None:
    api_key = st.session_state.get("api_keys", {}).get(provider, "")
    if not api_key:
        st.error(
            f"Chave de API para **{PROVIDER_NAMES[provider]}** não configurada. "
            "Vá em ⚙️ Configurações."
        )
        return None

    system = st.session_state.get("cena_prosa_system", prosa_system)
    template = st.session_state.get("cena_prosa_template", prosa_template)
    user_msg = (
        template
        .replace("{beats}", beats_text)
        .replace("{contexto}", context)
        .replace("{num_palavras}", str(num_palavras))
    )
    max_tokens = st.session_state.get("max_tokens", 8192)
    try:
        return call_ai(
            provider=provider,
            model=model,
            user_prompt=user_msg,
            system_prompt=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        st.error(f"Erro: {e}")
        return None


# ─── Área principal ───────────────────────────────────────────────────────────
chapters = get_chapters()

if not chapters:
    st.info("Nenhum capítulo disponível. Crie ao menos um capítulo no Editor primeiro.")
    st.stop()

chapter_options = {ch["title"]: ch for ch in chapters}

# ── Passo 1: Entradas ─────────────────────────────────────────────────────────
st.subheader("Passo 1 — Descreva a Cena")

col_left, col_right = st.columns([3, 1])

with col_left:
    description = st.text_area(
        "Descrição da cena",
        height=160,
        placeholder=(
            "Ex: Pibe encontra Eva no corredor do escritório às 23h. "
            "Ela está prestes a sair e ele precisa decidir se conta o que descobriu. "
            "Tensão contida, diálogo curto, sem resolução."
        ),
        key="cena_description",
    )

with col_right:
    context_title = st.selectbox(
        "Capítulo de contexto",
        list(chapter_options.keys()),
        key="cena_context_chapter",
        help="As últimas linhas deste capítulo serão usadas para manter continuidade de voz.",
    )
    num_palavras = st.slider(
        "Meta de palavras",
        min_value=200,
        max_value=2000,
        value=600,
        step=100,
        key="cena_num_palavras",
    )

context_content = chapter_options[context_title].get("content", "")
context_excerpt = _get_context(context_content)

with st.expander(f"Pré-visualizar contexto — últimas linhas de «{context_title}»"):
    st.text(context_excerpt)

run_beats = st.button(
    "🎬 Gerar Beat Sheet",
    type="primary",
    disabled=not description.strip(),
    key="cena_run_beats",
)

# ── Execução Passo 1 ──────────────────────────────────────────────────────────
if run_beats and description.strip():
    st.session_state.pop("cena_beats_result", None)
    st.session_state.pop("cena_prosa_result", None)
    with st.spinner("Gerando beat sheet..."):
        result = _call_beats(description, context_excerpt, num_palavras)
        if result:
            st.session_state["cena_beats_result"] = result
            st.session_state["cena_context_excerpt"] = context_excerpt
            st.session_state["cena_num_palavras_used"] = num_palavras

# ── Passo 2: Beat Sheet → Prosa ───────────────────────────────────────────────
if st.session_state.get("cena_beats_result"):
    st.divider()
    st.subheader("Passo 2 — Beat Sheet")
    st.caption("Revise e edite o beat sheet abaixo antes de gerar a prosa.")

    beats_edited = st.text_area(
        "Beat Sheet (editável)",
        value=st.session_state["cena_beats_result"],
        height=380,
        key="cena_beats_edited",
    )

    col_dl, col_run = st.columns([1, 2])
    with col_dl:
        st.download_button(
            "⬇️ Baixar beat sheet",
            data=beats_edited.encode("utf-8"),
            file_name="beat_sheet.txt",
            mime="text/plain; charset=utf-8",
            key="dl_beats",
        )
    with col_run:
        run_prosa = st.button(
            "✍️ Escrever Cena",
            type="primary",
            disabled=not beats_edited.strip(),
            key="cena_run_prosa",
            use_container_width=True,
        )

    # ── Execução Passo 2 ──────────────────────────────────────────────────────
    if run_prosa and beats_edited.strip():
        ctx = st.session_state.get("cena_context_excerpt", context_excerpt)
        nw = st.session_state.get("cena_num_palavras_used", num_palavras)
        with st.spinner("Escrevendo a cena..."):
            prosa = _call_prosa(beats_edited, ctx, nw)
            if prosa:
                st.session_state["cena_prosa_result"] = prosa

# ── Passo 3: Resultado — Prosa ────────────────────────────────────────────────
if st.session_state.get("cena_prosa_result"):
    st.divider()
    st.subheader("Passo 3 — Prosa Gerada")

    prosa_text = st.session_state["cena_prosa_result"]
    word_count = len(prosa_text.split())
    st.caption(f"{word_count:,} palavras geradas")

    st.markdown(prosa_text)

    # Downloads
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "⬇️ Baixar cena (.txt)",
            data=prosa_text.encode("utf-8"),
            file_name="cena.txt",
            mime="text/plain; charset=utf-8",
            key="dl_prosa_txt",
        )
    with col_dl2:
        st.download_button(
            "⬇️ Baixar cena (.md)",
            data=prosa_text.encode("utf-8"),
            file_name="cena.md",
            mime="text/markdown",
            key="dl_prosa_md",
        )

    # ── Adicionar a um capítulo ───────────────────────────────────────────────
    st.divider()
    st.subheader("Adicionar ao Capítulo")

    col_sel, col_sep, col_btn = st.columns([3, 2, 2])

    with col_sel:
        target_title = st.selectbox(
            "Capítulo de destino",
            list(chapter_options.keys()),
            key="cena_target_chapter",
        )
    with col_sep:
        separator = st.selectbox(
            "Separador",
            options=["— (sem separador)", "Linha em branco dupla", "***", "---"],
            key="cena_separator",
        )
    with col_btn:
        st.write("")  # alinha verticalmente
        st.write("")
        add_to_chapter = st.button(
            "➕ Adicionar ao Capítulo",
            type="secondary",
            use_container_width=True,
            key="cena_add_to_chapter",
        )

    if add_to_chapter:
        target_ch = dict(chapter_options[target_title])
        current_content = target_ch.get("content", "").rstrip()

        sep_map = {
            "— (sem separador)": "\n\n",
            "Linha em branco dupla": "\n\n",
            "***": "\n\n***\n\n",
            "---": "\n\n---\n\n",
        }
        sep = sep_map.get(separator, "\n\n")
        target_ch["content"] = current_content + sep + prosa_text.strip()
        save_chapter(target_ch)
        st.success(f"Cena adicionada a **{target_title}**.")
