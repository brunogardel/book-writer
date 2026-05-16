"""
Projetos — cria, seleciona e gerencia projetos independentes.
Cada projeto tem seu próprio livro, histórico de notas e bíblia.
Configurações e prompts são compartilhados entre projetos.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from utils.storage import (
    init_session_state,
    get_current_project,
    set_current_project,
    list_projects,
    create_project,
    delete_project,
    get_project_dir,
    get_chapters,
    load_score_history,
    load_antia_score_history,
    DEFAULT_PROJECT,
)

st.set_page_config(page_title="Projetos — Escritor", page_icon="📁", layout="wide")
init_session_state()

st.title("📁 Projetos")
st.markdown(
    "Cada projeto é um livro independente com seu próprio manuscrito, "
    "histórico de notas Anti-IA e Análise de Capítulo, e Bíblia. "
    "Configurações e prompts são compartilhados."
)

current = get_current_project()
projects = list_projects()

# ─── Projeto ativo ────────────────────────────────────────────────────────────
st.info(f"**Projeto ativo:** {current}")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_switch, tab_new, tab_manage = st.tabs(
    ["🔀 Trocar Projeto", "➕ Novo Projeto", "🗂 Gerenciar"]
)

# ── Trocar Projeto ────────────────────────────────────────────────────────────
with tab_switch:
    st.subheader("Selecionar projeto ativo")

    if len(projects) == 1:
        st.info("Só existe o projeto padrão. Crie um novo na aba **➕ Novo Projeto**.")
    else:
        # Cards por projeto
        for name in projects:
            is_active = name == current
            chapters = get_chapters()  # só carrega do projeto ativo

            # Conta capítulos e scores do projeto
            pdir = get_project_dir(name)
            import json
            book_path = pdir / "book.json"
            scores_path = pdir / "scores.json"
            antia_path = pdir / "antia_scores.json"

            try:
                book_data = json.loads(book_path.read_text(encoding="utf-8")) if book_path.exists() else {}
                n_chapters = len(book_data.get("chapters", []))
                total_words = sum(
                    len(c.get("content", "").split())
                    for c in book_data.get("chapters", [])
                )
            except Exception:
                n_chapters, total_words = 0, 0

            try:
                scores_data = json.loads(scores_path.read_text(encoding="utf-8")) if scores_path.exists() else {}
                n_analyzed = len(scores_data)
            except Exception:
                n_analyzed = 0

            border = "2px solid #4CAF50" if is_active else "1px solid #444"
            label = " (ativo)" if is_active else ""

            with st.container(border=True):
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**{name}{label}**")
                    st.caption(
                        f"{n_chapters} capítulo(s) · {total_words:,} palavras · "
                        f"{n_analyzed} capítulo(s) analisado(s)"
                    )
                with col_btn:
                    if not is_active:
                        if st.button(
                            "Selecionar",
                            key=f"select_{name}",
                            use_container_width=True,
                            type="primary",
                        ):
                            set_current_project(name)
                            st.success(f"Projeto **{name}** ativado. Recarregue a página.")
                            st.rerun()
                    else:
                        st.success("Ativo")

# ── Novo Projeto ──────────────────────────────────────────────────────────────
with tab_new:
    st.subheader("Criar novo projeto")
    st.markdown(
        "Um novo projeto começa completamente vazio — sem capítulos, sem histórico de notas, "
        "sem bíblia. Ideal para um livro novo que não deve misturar dados com projetos anteriores."
    )

    new_name = st.text_input(
        "Nome do projeto:",
        placeholder="Ex: meu-romance-2025",
        key="new_project_name",
        help="Use letras, números e hífens. Sem espaços.",
    )

    # Validação do nome
    import re as _re
    name_valid = bool(new_name.strip()) and bool(_re.match(r"^[a-zA-Z0-9_\-]+$", new_name.strip()))
    name_exists = new_name.strip() in projects

    if new_name.strip():
        if not name_valid:
            st.warning("Nome inválido — use apenas letras, números, hífens e underscores (sem espaços).")
        elif name_exists:
            st.warning(f"Já existe um projeto com o nome **{new_name.strip()}**.")

    activate_now = st.checkbox("Ativar imediatamente após criar", value=True, key="activate_new")

    if st.button(
        "➕ Criar Projeto",
        type="primary",
        disabled=not (name_valid and not name_exists),
        key="btn_create_project",
    ):
        create_project(new_name.strip())
        if activate_now:
            set_current_project(new_name.strip())
            st.success(
                f"Projeto **{new_name.strip()}** criado e ativado. "
                "Importe seu livro em **📥 Importar**."
            )
        else:
            st.success(f"Projeto **{new_name.strip()}** criado.")
        st.rerun()

# ── Gerenciar ─────────────────────────────────────────────────────────────────
with tab_manage:
    st.subheader("Gerenciar projetos existentes")

    named_projects = [p for p in projects if p != DEFAULT_PROJECT]
    if not named_projects:
        st.info("Nenhum projeto nomeado ainda. O projeto **default** não pode ser excluído.")
    else:
        st.warning(
            "**Atenção:** excluir um projeto remove permanentemente todos os seus dados "
            "(capítulos, notas, bíblia). Esta ação não pode ser desfeita."
        )
        for name in named_projects:
            is_active = name == current
            with st.container(border=True):
                col_name, col_btn = st.columns([4, 1])
                with col_name:
                    st.markdown(f"**{name}**{'  ← ativo' if is_active else ''}")
                    pdir = get_project_dir(name)
                    book_path = pdir / "book.json"
                    try:
                        import json as _json
                        bd = _json.loads(book_path.read_text(encoding="utf-8")) if book_path.exists() else {}
                        n_ch = len(bd.get("chapters", []))
                        st.caption(f"{n_ch} capítulo(s) · {pdir}")
                    except Exception:
                        st.caption(str(pdir))
                with col_btn:
                    if is_active:
                        st.caption("(ativo — troque antes de excluir)")
                    else:
                        if st.button(
                            "Excluir",
                            key=f"del_{name}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            delete_project(name)
                            st.success(f"Projeto **{name}** excluído.")
                            st.rerun()
