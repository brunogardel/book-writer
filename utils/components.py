"""
Componentes Streamlit reutilizáveis.
"""

import streamlit as st
from utils.ai_client import AVAILABLE_MODELS, PROVIDER_NAMES

_CUSTOM_OPTION = "✏️ Digitar modelo..."

# Nomes amigáveis para exibição no seletor
MODEL_DISPLAY_NAMES = {
    # OpenAI — GPT-5.2
    "gpt-5.2":              "GPT-5.2 Thinking",
    "gpt-5.2-pro":          "GPT-5.2 Pro",
    "gpt-5.2-chat-latest":  "GPT-5.2 Instant",
    "gpt-5.2-codex":        "GPT-5.2 Codex",
    "gpt-5.3-codex":        "GPT-5.3 Codex",
    # OpenAI — GPT-5.1 / 5
    "gpt-5.1":              "GPT-5.1",
    "gpt-5":                "GPT-5",
    "gpt-5-mini":           "GPT-5 Mini",
    # OpenAI — o-series
    "o4-mini":              "o4 Mini (raciocínio)",
    "o3":                   "o3 (raciocínio)",
    "o3-mini":              "o3 Mini (raciocínio)",
    "o1-pro":               "o1 Pro (raciocínio)",
    "o1":                   "o1 (raciocínio)",
    "o1-mini":              "o1 Mini (raciocínio)",
    # OpenAI — GPT-4.1
    "gpt-4.1":              "GPT-4.1 (1M ctx)",
    "gpt-4.1-mini":         "GPT-4.1 Mini",
    "gpt-4.1-nano":         "GPT-4.1 Nano",
    # OpenAI — GPT-4o legado
    "gpt-4o":               "GPT-4o (legado)",
    "gpt-4o-mini":          "GPT-4o Mini (legado)",
    # Anthropic — Claude 4.7
    "claude-opus-4-7":                "Claude Opus 4.7 ✨ mais recente",
    # Anthropic — Claude 4.6
    "claude-opus-4-6":                "Claude Opus 4.6",
    "claude-sonnet-4-6":              "Claude Sonnet 4.6 ⭐ recomendado",
    "claude-haiku-4-6":               "Claude Haiku 4.6",
    # Anthropic — Claude 4.5
    "claude-opus-4-5-20251101":       "Claude Opus 4.5",
    "claude-sonnet-4-5-20250929":     "Claude Sonnet 4.5",
    "claude-haiku-4-5-20251001":      "Claude Haiku 4.5 (rápido)",
    "claude-haiku-4-5":               "Claude Haiku 4.5",
    # Anthropic — Claude 4.1
    "claude-opus-4-1-20250805":       "Claude Opus 4.1",
    # Gemini
    "gemini-3-pro-preview":           "Gemini 3 Pro (preview)",
    "gemini-3-flash-preview":         "Gemini 3 Flash (preview)",
    "gemini-3-pro-image-preview":     "Gemini 3 Pro Image (preview)",
    "gemini-2.5-pro":                 "Gemini 2.5 Pro",
    "gemini-2.5-flash":               "Gemini 2.5 Flash ⭐ recomendado",
    "gemini-2.5-flash-lite":          "Gemini 2.5 Flash Lite",
    "gemini-2.0-flash":               "Gemini 2.0 Flash (legado)",
}


def _display_name(model_id: str) -> str:
    """Retorna o nome amigável do modelo, ou o ID se não houver mapeamento."""
    return MODEL_DISPLAY_NAMES.get(model_id, model_id)


def model_selector(key_prefix: str, default_temp: float = 0.7) -> tuple:
    """
    Renderiza na sidebar os seletores de Provider, Modelo e Temperatura.
    Inclui opção de digitar qualquer model ID manualmente.

    Retorna: (provider: str, model: str, temperature: float)
    """
    st.subheader("Configurações de IA")

    default_provider = st.session_state.get("ai_provider", "anthropic")
    default_model = st.session_state.get("ai_model", "claude-sonnet-4-5-20250929")

    # Provider
    provider_list = list(AVAILABLE_MODELS.keys())
    provider_idx = provider_list.index(default_provider) if default_provider in provider_list else 1

    provider = st.selectbox(
        "Provider",
        options=provider_list,
        format_func=lambda x: PROVIDER_NAMES[x],
        index=provider_idx,
        key=f"{key_prefix}_provider",
    )

    # Modelo — lista conhecida + opção de digitar
    model_options = AVAILABLE_MODELS[provider] + [_CUSTOM_OPTION]

    if default_model in AVAILABLE_MODELS[provider]:
        model_idx = AVAILABLE_MODELS[provider].index(default_model)
    else:
        model_idx = len(model_options) - 1  # Seleciona "Digitar..."

    selected = st.selectbox(
        "Modelo",
        options=model_options,
        format_func=lambda x: _display_name(x) if x != _CUSTOM_OPTION else x,
        index=model_idx,
        key=f"{key_prefix}_model_select",
    )

    if selected == _CUSTOM_OPTION:
        typed = st.text_input(
            "ID do modelo (exato):",
            value=default_model if default_model not in AVAILABLE_MODELS[provider] else "",
            placeholder="Ex: gpt-4.1, claude-sonnet-4-5-20250929...",
            key=f"{key_prefix}_custom_model",
        )
        model = typed.strip() if typed.strip() else ""
        if not model:
            st.warning("Digite o ID do modelo para continuar.")
    else:
        model = selected

    # Temperatura
    temperature = st.slider(
        "Temperatura",
        0.0,
        1.0,
        default_temp,
        0.05,
        key=f"{key_prefix}_temp",
    )

    with st.expander("Guia de temperatura"):
        st.markdown(
            "| Tarefa | Ideal |\n"
            "|---|---|\n"
            "| Análise / Anti-IA | 0.2 – 0.4 |\n"
            "| Reescrever | 0.5 – 0.6 |\n"
            "| Continuar Escrevendo | 0.7 – 0.8 |\n"
            "| Brainstorm | 0.8 – 1.0 |"
        )

    return provider, model, temperature


def show_model_info(task: str, container=None):
    """
    Exibe informações sobre o modelo recomendado para a tarefa.

    Args:
        task: Nome da tarefa (anti_ia, analise_capitulo, etc.)
        container: Container Streamlit opcional para renderizar

    Returns:
        Tuple (use_recommended: bool, override_model: str | None)
    """
    from utils.storage import get_task_info, format_cost, get_model_display_name

    target = container if container else st

    task_info = get_task_info(task)
    if not task_info:
        return True, None

    # Mostra info do modelo recomendado
    with target.expander("🤖 Modelo de IA Recomendado", expanded=False):
        col1, col2 = st.columns([2, 1])

        with col1:
            model_name = get_model_display_name(task_info["model"])
            st.markdown(f"**Modelo:** {model_name}")
            st.caption(f"💡 {task_info['reason']}")

        with col2:
            cost_str = format_cost(task_info["avg_cost"])
            st.metric("Custo médio", cost_str)

        st.divider()

        # Opção de override
        use_recommended = st.checkbox(
            "✅ Usar modelo recomendado (otimizado para esta tarefa)",
            value=True,
            key=f"use_recommended_{task}",
            help="Desmarque para escolher manualmente nas Configurações"
        )

        if not use_recommended:
            st.info("💡 O modelo será definido pelas suas configurações globais em ⚙️ Configurações")

        return use_recommended, None
