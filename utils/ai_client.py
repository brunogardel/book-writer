"""
Cliente unificado de IA - suporta OpenAI, Anthropic Claude e Google Gemini.
"""

import streamlit as st


def get_api_key(provider: str) -> str:
    """Retorna a chave de API para o provider especificado."""
    keys = st.session_state.get("api_keys", {})
    return keys.get(provider, "")


def call_ai(
    provider: str,
    model: str,
    user_prompt: str,
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """
    Chama a IA selecionada e retorna a resposta como string.

    Args:
        provider: "openai", "anthropic" ou "gemini"
        model: nome do modelo (ex: "gpt-4o", "claude-3-5-sonnet-20241022", "gemini-1.5-pro")
        user_prompt: o prompt do usuário
        system_prompt: instrução de sistema (opcional)
        temperature: criatividade da resposta (0.0 a 1.0)
        max_tokens: tamanho máximo da resposta

    Returns:
        Texto da resposta da IA
    """
    api_key = get_api_key(provider)
    if not api_key:
        raise ValueError(
            f"Chave de API para '{provider}' não configurada. Vá em Configurações."
        )

    if provider == "openai":
        return _call_openai(api_key, model, user_prompt, system_prompt, temperature, max_tokens)
    elif provider == "anthropic":
        return _call_anthropic(api_key, model, user_prompt, system_prompt, temperature, max_tokens)
    elif provider == "gemini":
        return _call_gemini(api_key, model, user_prompt, system_prompt, temperature, max_tokens)
    else:
        raise ValueError(f"Provider desconhecido: {provider}")


# Modelos que usam a Responses API (/v1/responses) em vez de Chat Completions
_RESPONSES_API_MODELS = {"gpt-5.2-pro", "gpt-5.2-codex", "gpt-5.3-codex"}


def _is_openai_reasoning_model(model: str) -> bool:
    """
    Modelos de raciocínio da OpenAI (o1, o3, o4, gpt-5, etc.) usam
    max_completion_tokens e não aceitam o parâmetro temperature.
    """
    reasoning_prefixes = ("o1", "o3", "o4", "gpt-5")
    return any(model.startswith(p) for p in reasoning_prefixes)


def _call_openai_responses_api(client, model, user_prompt, system_prompt, max_tokens):
    """Chama modelos que usam a Responses API (ex: gpt-5.2-pro)."""
    kwargs = {
        "model": model,
        "input": user_prompt,
        "max_output_tokens": max_tokens,
    }
    if system_prompt:
        kwargs["instructions"] = system_prompt

    response = client.responses.create(**kwargs)
    # A resposta pode vir em response.output_text ou response.output[0].content[0].text
    if hasattr(response, "output_text"):
        return response.output_text
    # Fallback para estrutura de output aninhada
    return response.output[0].content[0].text


def _call_openai(api_key, model, user_prompt, system_prompt, temperature, max_tokens):
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        # Modelos que usam a Responses API
        if model in _RESPONSES_API_MODELS:
            return _call_openai_responses_api(client, model, user_prompt, system_prompt, max_tokens)

        # Modelos Chat Completions
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        kwargs = {"model": model, "messages": messages}

        if _is_openai_reasoning_model(model):
            # Modelos de raciocínio: usam max_completion_tokens, sem temperature
            kwargs["max_completion_tokens"] = max_tokens
        else:
            # Modelos GPT clássicos
            kwargs["max_tokens"] = max_tokens
            kwargs["temperature"] = temperature

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except ImportError:
        raise ImportError("Instale a biblioteca openai: pip install openai")
    except Exception as e:
        raise RuntimeError(f"Erro ao chamar OpenAI: {str(e)}")


def _call_anthropic(api_key, model, user_prompt, system_prompt, temperature, max_tokens):
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)
        return response.content[0].text
    except ImportError:
        raise ImportError("Instale a biblioteca anthropic: pip install anthropic")
    except Exception as e:
        raise RuntimeError(f"Erro ao chamar Anthropic: {str(e)}")


def _call_gemini(api_key, model, user_prompt, system_prompt, temperature, max_tokens):
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        full_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
        )
        response = gemini_model.generate_content(full_prompt)
        return response.text
    except ImportError:
        raise ImportError(
            "Instale a biblioteca google-generativeai: pip install google-generativeai"
        )
    except Exception as e:
        raise RuntimeError(f"Erro ao chamar Gemini: {str(e)}")


# Modelos disponíveis por provider
# A opção especial "_custom_" permite digitar qualquer model ID
AVAILABLE_MODELS = {
    "openai": [
        # ── GPT-5.4 (mais recente — março/2026) ───────────────────────────────
        "gpt-5.4",              # Flagship com extended thinking
        "gpt-5.4-mini",         # Versão rápida e eficiente
        "gpt-5.4-turbo",        # Balanceado entre velocidade e qualidade
        # ── GPT-5.2 ───────────────────────────────────────────────────────────
        "gpt-5.2",              # Thinking — Chat Completions + Responses API
        "gpt-5.2-pro",          # Pro — Responses API apenas
        "gpt-5.2-chat-latest",  # Instant — Chat Completions
        "gpt-5.2-codex",        # Agentic coding — Responses API
        "gpt-5.3-codex",        # Codex mais recente — Responses API
        # ── GPT-5.1 / GPT-5 ───────────────────────────────────────────────────
        "gpt-5.1",              # Predecessor do 5.2, ainda disponível
        "gpt-5",                # Modelo base GPT-5
        "gpt-5-mini",           # Versão rápida e acessível do GPT-5
        # ── o-series (raciocínio) ─────────────────────────────────────────────
        "o4-mini",              # Raciocínio rápido e econômico
        "o3",                   # Raciocínio avançado
        "o3-mini",              # Raciocínio compacto
        "o1-pro",               # o1 com mais compute
        "o1",
        "o1-mini",
        # ── GPT-4.1 (1M tokens de contexto, lançado abr/2025) ─────────────────
        "gpt-4.1",              # Coding e instruction-following, 1M ctx
        "gpt-4.1-mini",         # Rápido e eficiente
        "gpt-4.1-nano",         # Menor e mais barato
        # ── GPT-4o (legado, API ainda ativa) ──────────────────────────────────
        "gpt-4o",
        "gpt-4o-mini",
    ],
    "anthropic": [
        # ── Claude 4.6 (mais recente — fev/2026) ──────────────────────────────
        "claude-opus-4-6",
        # ── Claude 4.5 ────────────────────────────────────────────────────────
        "claude-opus-4-5-20251101",
        "claude-sonnet-4-5-20250929",
        "claude-haiku-4-5-20251001",
        # ── Claude 4.1 ────────────────────────────────────────────────────────
        "claude-opus-4-1-20250805",
    ],
    "gemini": [
        # Gemini 3 (mais recentes — preview)
        "gemini-3-pro-preview",
        "gemini-3-flash-preview",
        "gemini-3-pro-image-preview",
        # Gemini 2.5 (estáveis)
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        # Gemini 2.0 (será descontinuado em março/2026)
        "gemini-2.0-flash",
    ],
}

PROVIDER_NAMES = {
    "openai": "OpenAI",
    "anthropic": "Anthropic (Claude)",
    "gemini": "Google (Gemini)",
}
