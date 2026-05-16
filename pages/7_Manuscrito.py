"""
Manuscrito — visão geral de todos os capítulos importados.
Lista todos os capítulos com estatísticas e permite ler o conteúdo completo.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from utils.storage import init_session_state, get_current_project, get_chapters, load_book, delete_chapter

st.set_page_config(page_title="Manuscrito — Escritor", page_icon="📖", layout="wide")
init_session_state()

current_project = get_current_project()
st.title("📖 Manuscrito")
st.caption(f"Projeto ativo: **{current_project}**")

chapters = get_chapters()
book = load_book()

if not chapters:
    st.info("Nenhum capítulo importado ainda. Vá em **📥 Importar** para começar.")
    st.stop()

# ─── Cabeçalho com stats gerais ───────────────────────────────────────────────
total_words = sum(len(c.get("content", "").split()) for c in chapters)
total_chars = sum(len(c.get("content", "")) for c in chapters)
total_pages = max(1, total_words // 250)

book_title = book.get("title", "") or current_project
if book_title:
    st.subheader(book_title)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Capítulos", len(chapters))
col2.metric("Palavras", f"{total_words:,}")
col3.metric("Caracteres", f"{total_chars:,}")
col4.metric("Páginas estimadas", f"~{total_pages:,}")

st.divider()

# ─── Filtro / busca ───────────────────────────────────────────────────────────
col_search, col_sort = st.columns([3, 1])
with col_search:
    search = st.text_input(
        "Buscar no manuscrito:",
        placeholder="Digite uma palavra ou trecho para filtrar capítulos...",
        key="manu_search",
    )
with col_sort:
    sort_by = st.selectbox(
        "Ordenar por:",
        ["Ordem original", "Mais palavras", "Menos palavras", "Nome A→Z"],
        key="manu_sort",
    )

# Aplica ordenação
sorted_chapters = list(chapters)
if sort_by == "Mais palavras":
    sorted_chapters.sort(key=lambda c: len(c.get("content", "").split()), reverse=True)
elif sort_by == "Menos palavras":
    sorted_chapters.sort(key=lambda c: len(c.get("content", "").split()))
elif sort_by == "Nome A→Z":
    sorted_chapters.sort(key=lambda c: c.get("title", "").lower())

# Aplica filtro de busca
search_lower = search.strip().lower()
if search_lower:
    filtered = [
        c for c in sorted_chapters
        if search_lower in c.get("title", "").lower()
        or search_lower in c.get("content", "").lower()
    ]
else:
    filtered = sorted_chapters

if search_lower and not filtered:
    st.warning(f"Nenhum capítulo contém **{search}**.")
    st.stop()

if search_lower:
    st.caption(f"{len(filtered)} de {len(chapters)} capítulo(s) correspondem à busca.")

# ─── Lista de capítulos ───────────────────────────────────────────────────────
for i, ch in enumerate(filtered):
    title = ch.get("title", f"Capítulo {i + 1}")
    content = ch.get("content", "")
    words = len(content.split())
    chars = len(content)
    pages = max(1, words // 250)

    # Destaca termos buscados no título
    display_title = title
    if search_lower and search_lower in title.lower():
        display_title = f"**{title}** 🔍"

    # Prévia do conteúdo (primeira linha não vazia)
    preview_lines = [l.strip() for l in content.splitlines() if l.strip()]
    preview = preview_lines[0][:120] + "…" if preview_lines else "_(sem conteúdo)_"

    with st.expander(
        f"{display_title}   ·   {words:,} palavras   ·   ~{pages} pág.",
        expanded=False,
    ):
        # Stats do capítulo
        c1, c2, c3 = st.columns(3)
        c1.metric("Palavras", f"{words:,}")
        c2.metric("Caracteres", f"{chars:,}")
        c3.metric("Parágrafos", len([l for l in content.splitlines() if l.strip()]))

        st.caption(f"**Prévia:** {preview}")
        st.divider()

        # Conteúdo completo (com destaque de busca se houver)
        if search_lower and search_lower in content.lower():
            # Mostra trechos com o termo encontrado
            lines = content.splitlines()
            match_lines = [
                (idx, line) for idx, line in enumerate(lines)
                if search_lower in line.lower()
            ]
            st.caption(f"🔍 {len(match_lines)} ocorrência(s) de **{search}** neste capítulo:")
            for idx, line in match_lines[:10]:
                # Destaca o termo na linha
                highlighted = line.replace(
                    search, f"**{search}**"
                ).replace(
                    search.capitalize(), f"**{search.capitalize()}**"
                )
                st.markdown(f"> …{highlighted}…")
            if len(match_lines) > 10:
                st.caption(f"_(+{len(match_lines) - 10} ocorrências adicionais)_")

            st.divider()

        # Texto completo
        st.markdown("**Texto completo:**")
        truncate_msg = '<br><br><i style="color:#888">[...texto truncado — abra no Editor para ver o completo]</i>' if len(content) > 8000 else ''
        st.markdown(
            f"<div style='font-family: Georgia, serif; font-size: 15px; "
            f"line-height: 1.7; white-space: pre-wrap; max-height: 500px; "
            f"overflow-y: auto; padding: 12px; "
            f"background: #1e1e1e; border-radius: 6px;'>"
            f"{content[:8000]}"
            f"{truncate_msg}"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Ações
        col_dl, col_del = st.columns([3, 1])
        with col_dl:
            st.download_button(
                f"⬇️ Baixar «{title}»",
                data=content.encode("utf-8"),
                file_name=f"{title.replace('/', '-')}.txt",
                mime="text/plain; charset=utf-8",
                key=f"dl_{ch.get('id', i)}",
            )
        with col_del:
            ch_id = ch.get("id", "")
            confirm_key = f"confirm_del_{ch_id}"
            if st.session_state.get(confirm_key):
                st.error("Tem certeza?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Sim, excluir", key=f"yes_del_{ch_id}", type="primary"):
                        delete_chapter(ch_id)
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
                with col_no:
                    if st.button("Cancelar", key=f"no_del_{ch_id}"):
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
            else:
                if st.button("🗑️ Excluir", key=f"del_{ch_id}", use_container_width=True):
                    st.session_state[confirm_key] = True
                    st.rerun()

st.divider()
st.markdown(
    f"<small style='color:#aaa'>**{len(chapters)}** capítulos · "
    f"**{total_words:,}** palavras · ~**{total_pages:,}** páginas</small>",
    unsafe_allow_html=True,
)
