"""
Editor de capítulos — escreva e organize seu manuscrito.
"""

import sys
from pathlib import Path
import uuid

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from utils.storage import (
    init_session_state,
    load_book,
    save_book,
    get_chapters,
    save_chapter,
    delete_chapter,
)

st.set_page_config(page_title="Editor — Escritor", page_icon="📝", layout="wide")
init_session_state()

st.title("📝 Editor de Capítulos")

book = load_book()
chapters = get_chapters()

# ─── Sidebar: metadados do livro ──────────────────────────────────────────────
with st.sidebar:
    st.subheader("Livro")
    new_title = st.text_input("Título", value=book.get("title", ""))
    new_author = st.text_input("Autor", value=book.get("author", ""))
    new_genre = st.text_input("Gênero", value=book.get("genre", ""))
    if st.button("Salvar metadados", use_container_width=True):
        book["title"] = new_title
        book["author"] = new_author
        book["genre"] = new_genre
        save_book(book)
        st.success("Salvo!")

    st.divider()

    if st.button("+ Novo Capítulo", use_container_width=True, type="primary"):
        new_ch = {
            "id": str(uuid.uuid4()),
            "title": f"Capítulo {len(chapters) + 1}",
            "content": "",
            "notes": "",
        }
        save_chapter(new_ch)
        st.session_state["active_chapter_id"] = new_ch["id"]
        st.rerun()

    st.divider()
    total_words = sum(len(c.get("content", "").split()) for c in chapters)
    st.caption(f"**{len(chapters)}** capítulos · **{total_words:,}** palavras")

# ─── Área principal ───────────────────────────────────────────────────────────
if not chapters:
    st.info("Nenhum capítulo ainda. Crie um no painel lateral ou importe em **📥 Importar**.")
    st.stop()

# ── Seletor de capítulo por dropdown (funciona com muitos capítulos) ──────────
chapter_map = {ch["title"]: ch for ch in chapters}
chapter_titles = [ch["title"] for ch in chapters]

active_id = st.session_state.get("active_chapter_id")
# Determina o índice atual no dropdown
active_idx = 0
if active_id:
    ids = [ch["id"] for ch in chapters]
    if active_id in ids:
        active_idx = ids.index(active_id)

selected_title = st.selectbox(
    "Selecionar capítulo para editar:",
    chapter_titles,
    index=active_idx,
    key="editor_chapter_select",
)

active_ch = chapter_map[selected_title]
active_id = active_ch["id"]
st.session_state["active_chapter_id"] = active_id

st.divider()

# ── Cabeçalho do capítulo ─────────────────────────────────────────────────────
col_title, col_del = st.columns([5, 1])
with col_title:
    chapter_title = st.text_input(
        "Título do Capítulo",
        value=active_ch["title"],
        key=f"title_{active_id}",
    )
with col_del:
    st.write("")
    confirm_del = st.session_state.get(f"confirm_del_{active_id}", False)
    if confirm_del:
        st.warning("Excluir este capítulo?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Sim", key=f"yes_del_{active_id}", type="primary"):
                delete_chapter(active_id)
                st.session_state.pop("active_chapter_id", None)
                st.session_state.pop(f"confirm_del_{active_id}", None)
                st.rerun()
        with col_no:
            if st.button("Não", key=f"no_del_{active_id}"):
                st.session_state[f"confirm_del_{active_id}"] = False
                st.rerun()
    else:
        if st.button("🗑️ Excluir", key=f"del_btn_{active_id}"):
            st.session_state[f"confirm_del_{active_id}"] = True
            st.rerun()

# ── Área de texto ─────────────────────────────────────────────────────────────
content = st.text_area(
    "Conteúdo",
    value=active_ch.get("content", ""),
    height=520,
    key=f"content_{active_id}",
    placeholder="Escreva seu capítulo aqui...",
    label_visibility="collapsed",
)

notes = st.text_area(
    "Notas internas (não exportadas)",
    value=active_ch.get("notes", ""),
    height=80,
    key=f"notes_{active_id}",
    placeholder="Lembretes, ideias, TODOs sobre este capítulo...",
)

# ── Barra inferior: salvar + stats ───────────────────────────────────────────
col_save, col_stats = st.columns([2, 4])
with col_save:
    if st.button("💾 Salvar Capítulo", type="primary", use_container_width=True, key=f"save_{active_id}"):
        active_ch["title"] = chapter_title
        active_ch["content"] = content
        active_ch["notes"] = notes
        save_chapter(active_ch)
        st.success("Capítulo salvo!")
        st.rerun()

with col_stats:
    words = len(content.split()) if content.strip() else 0
    chars = len(content)
    pages = max(1, words // 250)
    st.markdown(
        f"<small style='color:#888'>**{words:,}** palavras &nbsp;·&nbsp; "
        f"**{chars:,}** caracteres &nbsp;·&nbsp; ~**{pages}** páginas</small>",
        unsafe_allow_html=True,
    )

# ── Sinopse ───────────────────────────────────────────────────────────────────
with st.expander("Sinopse / Resumo do Capítulo"):
    synopsis = st.text_area(
        "Sinopse",
        value=active_ch.get("synopsis", ""),
        height=100,
        key=f"synopsis_{active_id}",
        placeholder="Resumo de uma linha do que acontece neste capítulo...",
    )
    if st.button("Salvar sinopse", key=f"save_syn_{active_id}"):
        active_ch["synopsis"] = synopsis
        save_chapter(active_ch)
        st.success("Sinopse salva!")

# ─── Rodapé ───────────────────────────────────────────────────────────────────
st.divider()
chapters_refreshed = get_chapters()
total_words = sum(len(c.get("content", "").split()) for c in chapters_refreshed)
st.markdown(
    f"<small style='color:#aaa'>Manuscrito: **{len(chapters_refreshed)}** capítulos &nbsp;·&nbsp; "
    f"**{total_words:,}** palavras no total</small>",
    unsafe_allow_html=True,
)
