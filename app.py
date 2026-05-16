"""
Escritor — App de suporte à escrita de livros
Página inicial
"""

import sys
from pathlib import Path

# Garante que o diretório raiz esteja no path
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from utils.storage import init_session_state, load_book, get_chapters

st.set_page_config(
    page_title="Escritor",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()

# ─── Estilo ───────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #555;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        border-left: 4px solid #6c63ff;
        margin-bottom: 0.8rem;
    }
    .feature-title {
        font-weight: 600;
        font-size: 1rem;
        color: #1a1a2e;
    }
    .feature-desc {
        font-size: 0.88rem;
        color: #666;
        margin-top: 0.2rem;
    }
    .stat-box {
        background: linear-gradient(135deg, #6c63ff22, #a29bfe22);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stat-num {
        font-size: 2rem;
        font-weight: 700;
        color: #6c63ff;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #555;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Header ───────────────────────────────────────────────────────────────────
book = load_book()
chapters = get_chapters()
total_words = sum(len(ch.get("content", "").split()) for ch in chapters)
total_chars = sum(len(ch.get("content", "")) for ch in chapters)

st.markdown('<p class="main-title">✍️ Escritor</p>', unsafe_allow_html=True)
st.markdown(
    f'<p class="subtitle">Seu assistente pessoal para escrever e publicar <strong>{book.get("title", "seu livro")}</strong></p>',
    unsafe_allow_html=True,
)

# ─── Estatísticas do livro ────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f'<div class="stat-box"><div class="stat-num">{len(chapters)}</div>'
        f'<div class="stat-label">Capítulos</div></div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f'<div class="stat-box"><div class="stat-num">{total_words:,}</div>'
        f'<div class="stat-label">Palavras</div></div>',
        unsafe_allow_html=True,
    )
with c3:
    pages = max(1, total_words // 250)
    st.markdown(
        f'<div class="stat-box"><div class="stat-num">{pages}</div>'
        f'<div class="stat-label">Páginas ~</div></div>',
        unsafe_allow_html=True,
    )
with c4:
    provider = st.session_state.get("ai_provider", "—")
    model = st.session_state.get("ai_model", "—")
    short_model = model.split("/")[-1] if "/" in model else model
    st.markdown(
        f'<div class="stat-box"><div class="stat-num" style="font-size:1rem;padding-top:0.4rem">{provider}</div>'
        f'<div class="stat-label">{short_model}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# ─── Funcionalidades ──────────────────────────────────────────────────────────
st.subheader("Funcionalidades")

col_a, col_b = st.columns(2)

features_left = [
    ("📝", "Editor", "pages/1_Editor.py", "Escreva e organize seus capítulos. Navegue pelo manuscrito completo."),
    ("🤖", "Anti-IA", "pages/2_Anti_IA.py", "Detecta padrões de escrita por IA e sugere melhorias para tornar o texto mais humano e único."),
    ("🔍", "Análise de Capítulo", "pages/3_Analise_Capitulo.py", "Avaliação editorial rigorosa: ritmo, personagens, diálogo, tensão — com notas e sugestões."),
    ("📚", "Análise do Livro", "pages/4_Analise_Livro.py", "Visão geral do manuscrito completo: estrutura, temas, arcos, mercado editorial."),
]

features_right = [
    ("✨", "Continuar Escrevendo", "pages/5_Continuar.py", "Trava criativa? A IA continua o texto mantendo seu estilo e voz."),
    ("🔄", "Reescrever", "pages/6_Reescrever.py", "Reformula trechos com diferentes tons, estilos ou objetivos narrativos."),
    ("💡", "Brainstorm", "pages/7_Brainstorm.py", "Gera ideias para trama, personagens, cenas, conflitos e reviravoltas."),
    ("📖", "Bíblia do Livro", "pages/8_Biblia.py", "Fichas de personagens, locais, linha do tempo e notas de mundo."),
]

with col_a:
    for icon, name, path, desc in features_left:
        st.markdown(
            f'<div class="feature-card">'
            f'<div class="feature-title">{icon} {name}</div>'
            f'<div class="feature-desc">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

with col_b:
    for icon, name, path, desc in features_right:
        st.markdown(
            f'<div class="feature-card">'
            f'<div class="feature-title">{icon} {name}</div>'
            f'<div class="feature-desc">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("---")
st.markdown(
    '<small style="color:#999">Navegue pelas ferramentas usando o menu lateral esquerdo. '
    'Configure suas chaves de API em ⚙️ Configurações.</small>',
    unsafe_allow_html=True,
)
