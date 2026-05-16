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

# ─── Estilo Moderno ───────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Imports */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global */
    .main {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    }

    /* Header */
    .hero-section {
        text-align: center;
        padding: 3rem 0 2.5rem 0;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border-radius: 24px;
        margin-bottom: 2.5rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }

    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }

    .subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.25rem;
        color: #94A3B8;
        font-weight: 400;
        margin-bottom: 0;
        line-height: 1.6;
    }

    .subtitle strong {
        color: #E2E8F0;
        font-weight: 600;
    }

    /* Stats */
    .stat-box {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(99, 102, 241, 0.3);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .stat-box:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.5);
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.2);
    }

    .stat-num {
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
    }

    .stat-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
        color: #94A3B8;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Section Headers */
    .section-header {
        font-family: 'Inter', sans-serif;
        font-size: 1.75rem;
        font-weight: 700;
        color: #F1F5F9;
        margin: 2.5rem 0 1.5rem 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .section-header::before {
        content: "";
        width: 4px;
        height: 28px;
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        border-radius: 2px;
    }

    /* Feature Cards */
    .feature-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
    }

    .feature-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .feature-card:hover::before {
        opacity: 1;
    }

    .feature-card:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 102, 241, 0.5);
        box-shadow: 0 12px 32px rgba(99, 102, 241, 0.2);
    }

    .feature-icon {
        font-size: 1.75rem;
        margin-bottom: 0.5rem;
        display: inline-block;
        filter: drop-shadow(0 2px 4px rgba(99, 102, 241, 0.4));
    }

    .feature-title {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.125rem;
        color: #F1F5F9;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }

    .feature-desc {
        font-family: 'Inter', sans-serif;
        font-size: 0.9375rem;
        color: #94A3B8;
        line-height: 1.6;
        margin: 0;
    }

    /* Footer */
    .footer-note {
        font-family: 'Inter', sans-serif;
        text-align: center;
        color: #64748B;
        font-size: 0.875rem;
        margin-top: 3rem;
        padding: 2rem 0;
        border-top: 1px solid rgba(99, 102, 241, 0.1);
    }

    .footer-note strong {
        color: #6366F1;
        font-weight: 600;
    }

    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, rgba(99, 102, 241, 0.3) 50%, transparent 100%);
        margin: 2.5rem 0;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #1E293B;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%);
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

# Hero Section
st.markdown(
    f'''
    <div class="hero-section">
        <div class="main-title">✍️ Escritor</div>
        <p class="subtitle">
            Seu assistente pessoal com IA para escrever e publicar<br>
            <strong>{book.get("title", "seu livro")}</strong>
        </p>
    </div>
    ''',
    unsafe_allow_html=True,
)

# ─── Estatísticas do livro ────────────────────────────────────────────────────
st.markdown('<div style="margin-bottom: 2.5rem;">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4, gap="medium")

with c1:
    st.markdown(
        f'''
        <div class="stat-box">
            <div class="stat-num">{len(chapters)}</div>
            <div class="stat-label">Capítulos</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f'''
        <div class="stat-box">
            <div class="stat-num">{total_words:,}</div>
            <div class="stat-label">Palavras</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

with c3:
    pages = max(1, total_words // 250)
    st.markdown(
        f'''
        <div class="stat-box">
            <div class="stat-num">{pages}</div>
            <div class="stat-label">Páginas ~</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

with c4:
    provider = st.session_state.get("ai_provider", "—")
    model = st.session_state.get("ai_model", "—")
    short_model = model.split("-")[-1] if "-" in model else model[:12]
    st.markdown(
        f'''
        <div class="stat-box">
            <div class="stat-num" style="font-size:1.125rem; padding-top:0.25rem; text-transform: uppercase;">
                {provider}
            </div>
            <div class="stat-label">{short_model}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

st.markdown('</div>', unsafe_allow_html=True)

# ─── Funcionalidades ──────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🛠️ Ferramentas</div>', unsafe_allow_html=True)

col_a, col_b = st.columns(2, gap="large")

features_left = [
    ("📝", "Editor", "Escreva e organize seus capítulos. Navegue pelo manuscrito completo."),
    ("🤖", "Anti-IA", "Detecta padrões de escrita por IA e sugere melhorias para tornar o texto mais humano e único."),
    ("🔍", "Análise de Capítulo", "Avaliação editorial rigorosa: ritmo, personagens, diálogo, tensão — com notas e sugestões."),
    ("📚", "Análise do Livro", "Visão geral do manuscrito completo: estrutura, temas, arcos, mercado editorial."),
]

features_right = [
    ("✨", "Continuar Escrevendo", "Trava criativa? A IA continua o texto mantendo seu estilo e voz."),
    ("🔄", "Reescrever", "Reformula trechos com diferentes tons, estilos ou objetivos narrativos."),
    ("💡", "Brainstorm", "Gera ideias para trama, personagens, cenas, conflitos e reviravoltas."),
    ("📖", "Bíblia do Livro", "Fichas de personagens, locais, linha do tempo e notas de mundo."),
]

with col_a:
    for icon, name, desc in features_left:
        st.markdown(
            f'''
            <div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{name}</div>
                <div class="feature-desc">{desc}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

with col_b:
    for icon, name, desc in features_right:
        st.markdown(
            f'''
            <div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{name}</div>
                <div class="feature-desc">{desc}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    '''
    <div class="footer-note">
        💡 Navegue pelas ferramentas usando o <strong>menu lateral esquerdo</strong><br>
        Configure suas chaves de API em <strong>⚙️ Configurações</strong>
    </div>
    ''',
    unsafe_allow_html=True,
)
