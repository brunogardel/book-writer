"""
Busca no Livro — pesquisa inteligente no conteúdo dos capítulos escritos.
Respostas baseadas EXCLUSIVAMENTE no texto do manuscrito.
"""

import sys
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from utils.storage import (
    init_session_state,
    get_chapters,
    get_full_text,
    load_prompts,
)
from utils.ai_client import call_ai, PROVIDER_NAMES
from utils.components import model_selector

# ─── Pré-filtro por palavras-chave ────────────────────────────────────────────
_STOPWORDS_PT = {
    "o", "a", "os", "as", "um", "uma", "de", "da", "do", "das", "dos",
    "em", "no", "na", "nos", "nas", "por", "para", "com", "que", "e",
    "é", "se", "não", "eu", "ele", "ela", "eles", "elas", "você", "como",
    "onde", "quando", "qual", "quais", "foi", "são", "ser", "ter", "há",
    "me", "te", "lhe", "nos", "vos", "ao", "à", "às", "aos", "or",
    "sobre", "entre", "depois", "antes", "mais", "mas", "já", "até",
    "também", "bem", "muito", "pouco", "mais", "menos", "sim", "não",
}

def _keyword_filter(query: str, chapters: list, scope_titles: list) -> list:
    """
    Retorna apenas os capítulos (dentre os do escopo selecionado) que contêm
    pelo menos uma das palavras-chave da pergunta.
    Fallback: retorna todos do escopo se nenhum capítulo bater.
    """
    scoped = [ch for ch in chapters if ch["title"] in scope_titles]

    # Extrai palavras relevantes da pergunta (≥ 3 chars, fora de stopwords)
    words = re.findall(r'\b\w{3,}\b', query.lower())
    keywords = [w for w in words if w not in _STOPWORDS_PT]

    if not keywords:
        return scoped

    matched = []
    for ch in scoped:
        content_lower = ch.get("content", "").lower()
        title_lower = ch.get("title", "").lower()
        if any(kw in content_lower or kw in title_lower for kw in keywords):
            matched.append(ch)

    return matched if matched else scoped


st.set_page_config(page_title="Busca no Livro — Escritor", page_icon="🔎", layout="wide")
init_session_state()

st.title("🔎 Busca no Livro")
st.markdown(
    "Faça perguntas sobre o conteúdo do manuscrito. "
    "As respostas são extraídas **exclusivamente dos capítulos escritos** — "
    "sem invenções, com citação do capítulo e trecho de origem."
)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    provider, model, temperature = model_selector("busca", default_temp=0.1)
    st.caption("Temperatura baixa recomendada para respostas mais precisas e literais.")

    st.divider()
    chapters = get_chapters()
    if chapters:
        st.subheader("Capítulos disponíveis")
        for ch in chapters:
            wc = len(ch.get("content", "").split())
            st.caption(f"• {ch['title']} ({wc:,} palavras)")
    else:
        st.info("Nenhum capítulo importado ainda.")

# ─── Exemplos de perguntas ────────────────────────────────────────────────────
EXAMPLE_QUERIES = [
    "Onde no livro foi descrita a primeira vez que [personagem] aparece?",
    "Qual a idade de [personagem] mencionada no texto?",
    "Quando aconteceu [evento]? Em que capítulo?",
    "Como é descrito fisicamente [personagem]?",
    "Qual a relação entre [personagem A] e [personagem B] segundo o texto?",
    "Em que capítulo [personagem] descobre [informação]?",
    "Quais locais foram mencionados até agora no livro?",
]

# ─── Área principal ───────────────────────────────────────────────────────────
if not chapters:
    st.warning("Importe capítulos primeiro em **Importar** ou crie-os no **Editor** para usar a busca.")
    st.stop()

# Escopo da busca
col_scope, col_info = st.columns([2, 3])
with col_scope:
    all_titles = [ch["title"] for ch in chapters]
    search_scope = st.multiselect(
        "Capítulos para pesquisar:",
        options=all_titles,
        default=all_titles,
        help="Selecione quais capítulos incluir na busca. Menos capítulos = resposta mais rápida.",
    )

with col_info:
    total_words = sum(
        len(ch.get("content", "").split())
        for ch in chapters
        if ch["title"] in search_scope
    )
    st.metric("Palavras no escopo", f"{total_words:,}")
    if total_words > 50_000:
        st.caption("Livro longo — a busca pode demorar mais e usar mais tokens.")

st.divider()

# Sugestões de perguntas
with st.expander("Exemplos de perguntas"):
    for ex in EXAMPLE_QUERIES:
        st.caption(f"• {ex}")

# Campo de busca
query = st.text_area(
    "Sua pergunta sobre o livro:",
    height=100,
    placeholder="Ex: Qual a idade de Mariana quando conhece o protagonista?",
    key="busca_query",
)

run_search = st.button(
    "🔎 Buscar",
    type="primary",
    disabled=not query.strip() or not search_scope,
    key="busca_run",
)

# ─── Histórico de buscas ──────────────────────────────────────────────────────
if "busca_history" not in st.session_state:
    st.session_state["busca_history"] = []

# ─── Execução ─────────────────────────────────────────────────────────────────
if run_search and query.strip() and search_scope:
    api_key = st.session_state.get("api_keys", {}).get(provider, "")
    if not api_key:
        st.error(
            f"Chave de API para **{PROVIDER_NAMES[provider]}** não configurada. "
            "Vá em ⚙️ Configurações."
        )
        st.stop()

    # ── Pré-filtro: só capítulos que contêm palavras-chave da pergunta ─────────
    filtered_chs = _keyword_filter(query.strip(), chapters, search_scope)
    filtered_titles = [ch["title"] for ch in filtered_chs]
    filtered_words = sum(len(ch.get("content", "").split()) for ch in filtered_chs)
    total_scoped = len([ch for ch in chapters if ch["title"] in search_scope])

    if len(filtered_chs) < total_scoped:
        st.info(
            f"Pré-filtro: encontrados **{len(filtered_chs)}** capítulo(s) relevantes "
            f"({filtered_words:,} palavras) de {total_scoped} no escopo. "
            f"Capítulos: {', '.join(f'*{t}*' for t in filtered_titles)}"
        )
    else:
        st.caption(
            f"Pré-filtro não reduziu escopo — enviando todos os {total_scoped} capítulos "
            f"({filtered_words:,} palavras)."
        )

    # Monta o texto apenas dos capítulos filtrados
    scope_text = ""
    for ch in filtered_chs:
        scope_text += f"\n\n{'=' * 60}\n# {ch['title']}\n{'=' * 60}\n\n{ch.get('content', '')}"

    prompts = load_prompts()
    prompt_data = prompts.get("busca_livro", {})
    system_prompt = prompt_data.get(
        "system",
        "Você é um assistente de pesquisa literária. Responda usando exclusivamente o texto fornecido.",
    )
    user_template = prompt_data.get("user_template", "{pergunta}\n\nTexto:\n\n{texto}")

    user_msg = (
        user_template
        .replace("{pergunta}", query.strip())
        .replace("{texto}", scope_text.strip())
    )

    with st.spinner(f"Pesquisando em {len(filtered_chs)} capítulo(s)..."):
        try:
            result = call_ai(
                provider=provider,
                model=model,
                user_prompt=user_msg,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=st.session_state.get("max_tokens", 8192),
            )
            # Salva no histórico
            st.session_state["busca_history"].insert(0, {
                "query": query.strip(),
                "result": result,
                "scope": filtered_titles,  # capítulos efetivamente pesquisados
                "scope_original": search_scope,
            })
        except Exception as e:
            st.error(f"Erro: {e}")

# ─── Resultados ───────────────────────────────────────────────────────────────
history = st.session_state.get("busca_history", [])

if history:
    st.divider()

    # Botão para limpar histórico
    col_h, col_clr = st.columns([4, 1])
    with col_h:
        st.subheader("Respostas")
    with col_clr:
        if st.button("Limpar", key="clear_busca"):
            st.session_state["busca_history"] = []
            st.rerun()

    for i, entry in enumerate(history):
        scoped = entry.get("scope", [])
        original = entry.get("scope_original", scoped)

        # Pergunta
        st.markdown(f"**P:** {entry['query']}")

        # Resposta em destaque
        with st.container(border=True):
            st.markdown("**R:**")
            st.markdown(entry["result"])

        # Metadados da busca — menos destaque
        if len(scoped) < len(original):
            st.caption(f"🔍 Pesquisado em {len(scoped)} capítulo(s): {', '.join(scoped)}")
        else:
            st.caption(f"🔍 Pesquisado em {len(scoped)} capítulo(s) (escopo completo)")

        dl_text = f"Pergunta: {entry['query']}\n\nCapítulos pesquisados: {', '.join(scoped)}\n\n{entry['result']}"
        st.download_button(
            "⬇️ Baixar resposta (.txt)",
            data=dl_text.encode("utf-8"),
            file_name=f"busca_{i+1}.txt",
            mime="text/plain; charset=utf-8",
            key=f"dl_busca_{i}",
        )

        if i < len(history) - 1:
            st.divider()
