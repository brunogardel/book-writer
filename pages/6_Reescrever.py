"""
Reescrever — reformula trechos com diferentes tons, estilos ou objetivos.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from utils.storage import init_session_state, load_prompts, save_prompts, reset_prompt
from utils.ai_client import call_ai, call_ai_for_task, PROVIDER_NAMES
from utils.components import model_selector, show_model_info

st.set_page_config(page_title="Reescrever — Escritor", page_icon="🔄", layout="wide")
init_session_state()

st.title("🔄 Reescrever")
st.markdown(
    "Reformule um trecho com um objetivo específico: mudar o tom, adicionar tensão, "
    "simplificar, enriquecer as descrições ou qualquer outra direção narrativa."
)

# Mostra modelo recomendado e custo
use_recommended_model, _ = show_model_info("reescrever")

prompts = load_prompts()
prompt_data = prompts.get("reescrever", {})

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    provider, model, temperature = model_selector("rw", default_temp=0.75)

    st.divider()
    st.subheader("Prompt")

    system_prompt = st.text_area(
        "System Prompt",
        value=prompt_data.get("system", ""),
        height=120,
        key="rw_system",
    )

    user_template = st.text_area(
        "Template (use {texto} e {objetivo})",
        value=prompt_data.get("user_template", ""),
        height=200,
        key="rw_user_template",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Salvar Prompt", use_container_width=True):
            prompts["reescrever"]["system"] = system_prompt
            prompts["reescrever"]["user_template"] = user_template
            save_prompts(prompts)
            st.success("Salvo!")
    with col2:
        if st.button("Restaurar Padrão", use_container_width=True):
            reset_prompt("reescrever")
            st.success("Restaurado!")
            st.rerun()

# ─── Área principal ───────────────────────────────────────────────────────────
text_input = st.text_area(
    "Trecho para reescrever:",
    height=220,
    placeholder="Cole aqui o parágrafo ou cena que deseja reformular...",
    key="rw_text",
)

st.subheader("Objetivo da reescrita")

# Objetivos pré-definidos + campo livre
preset_objectives = [
    "Tornar mais tenso e dramático",
    "Tornar mais poético e lírico",
    "Tornar mais seco e direto",
    "Enriquecer com detalhes sensoriais",
    "Adicionar mais emoção interna do personagem",
    "Simplificar para leitura mais fluida",
    "Tornar mais misterioso e ambíguo",
    "Aumentar o ritmo / velocidade da cena",
    "Reescrever em primeira pessoa",
    "Reescrever em terceira pessoa",
    "Personalizado...",
]

selected_preset = st.selectbox("Objetivo pré-definido:", preset_objectives, key="rw_preset")

if selected_preset == "Personalizado...":
    objective = st.text_input(
        "Descreva o objetivo:",
        placeholder="Ex: reescrever com mais humor negro, mais violência implícita...",
        key="rw_custom_obj",
    )
else:
    objective = selected_preset

num_versions = st.radio(
    "Quantas versões gerar:",
    [1, 2, 3],
    horizontal=True,
    index=1,
)

run_btn = st.button(
    "🔄 Reescrever",
    type="primary",
    disabled=not (text_input.strip() and objective.strip()),
)

# ─── Execução ────────────────────────────────────────────────────────────────
if run_btn:
    current_system = st.session_state.get("rw_system", system_prompt)
    current_template = st.session_state.get("rw_user_template", user_template)

    user_msg = current_template.replace("{texto}", text_input).replace("{objetivo}", objective)
    if num_versions > 1:
        user_msg = user_msg.replace(
            "3 versões diferentes",
            f"{num_versions} versões diferentes",
        )

    with st.spinner("Reescrevendo..."):
        try:
            result = None
            # Usa modelo recomendado ou configuração manual
            if use_recommended_model:
                result = call_ai_for_task(
                    task="reescrever",
                    user_prompt=user_msg,
                    system_prompt=current_system,
                    temperature=temperature,
                    max_tokens=len(text_input.split()) * 6 + 500,
                    use_recommended=True,
                )
            else:
                # Fallback: usa configuração manual da sidebar
                api_key = st.session_state.get("api_keys", {}).get(provider, "")
                if not api_key:
                    st.error(
                        f"Chave de API para **{PROVIDER_NAMES[provider]}** não configurada. "
                        "Vá em ⚙️ Configurações."
                    )
                else:
                    result = call_ai(
                        provider=provider,
                        model=model,
                        user_prompt=user_msg,
                        system_prompt=current_system,
                        temperature=temperature,
                        max_tokens=len(text_input.split()) * 6 + 500,
                    )
            if result:
                st.session_state["rw_result"] = result
                st.session_state["rw_original"] = text_input
        except Exception as e:
            st.error(f"Erro: {e}")

# ─── Resultado ────────────────────────────────────────────────────────────────
if "rw_result" in st.session_state:
    st.divider()

    col_orig, col_new = st.columns(2)
    with col_orig:
        st.subheader("Original")
        st.markdown(
            f'<div style="background:#f5f5f5;padding:1rem;border-radius:8px;'
            f'font-size:0.9rem;color:#444">{st.session_state["rw_original"]}</div>',
            unsafe_allow_html=True,
        )
    with col_new:
        st.subheader("Reescrito")
        st.markdown(st.session_state["rw_result"])

    st.download_button(
        "⬇️ Baixar versões reescritas",
        data=st.session_state["rw_result"].encode("utf-8"),
        file_name="reescrita.txt",
        mime="text/plain; charset=utf-8",
        key="dl_rw",
    )
