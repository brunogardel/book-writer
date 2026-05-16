"""
Anti-IA — Detecta padrões de escrita artificial e sugere melhorias.
Suporta análise do capítulo inteiro ou cena por cena.
Rastreia histórico de Pontuação Humana por revisão.
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
    split_into_scenes,
    parse_human_score,
    save_antia_score_entry,
    get_antia_score_history,
    load_antia_score_history,
    clear_antia_score_history,
    score_badge,
    check_convergence,
    check_voice_drift,
    SCORE_THRESHOLDS,
)
from utils.ai_client import call_ai, call_ai_for_task, PROVIDER_NAMES
from utils.components import model_selector, show_model_info

st.set_page_config(page_title="Anti-IA — Escritor", page_icon="🤖", layout="wide")
init_session_state()

st.title("🤖 Anti-IA")
st.markdown(
    "Analisa seu texto em busca de padrões típicos de escrita por IA — "
    "repetições, frases genéricas, estruturas artificiais — e sugere reescritas mais humanas e únicas."
)

# Mostra modelo recomendado e custo
use_recommended_model, _ = show_model_info("anti_ia")

prompts = load_prompts()
prompt_data = prompts.get("anti_ia", {})

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    provider, model, temperature = model_selector("anti_ia", default_temp=0.3)

    st.divider()
    st.subheader("Prompt do Agente")
    st.caption("Edite o prompt para personalizar a análise.")

    system_prompt = st.text_area(
        "System Prompt",
        value=prompt_data.get("system", ""),
        height=120,
        key="anti_ia_system",
    )

    user_template = st.text_area(
        "Template do Usuário (use {texto})",
        value=prompt_data.get("user_template", ""),
        height=250,
        key="anti_ia_user_template",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Salvar Prompt", use_container_width=True):
            prompts["anti_ia"]["system"] = system_prompt
            prompts["anti_ia"]["user_template"] = user_template
            save_prompts(prompts)
            st.success("Prompt salvo!")
    with col2:
        if st.button("Restaurar Padrão", use_container_width=True):
            reset_prompt("anti_ia")
            st.success("Restaurado!")
            st.rerun()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def _call_ai_safe(text: str) -> str | None:
    current_system = st.session_state.get("anti_ia_system", system_prompt)
    current_template = st.session_state.get("anti_ia_user_template", user_template)
    user_msg = current_template.replace("{texto}", text)
    max_tokens = st.session_state.get("max_tokens", 8192)

    try:
        # Usa modelo recomendado ou configuração manual
        if use_recommended_model:
            return call_ai_for_task(
                task="anti_ia",
                user_prompt=user_msg,
                system_prompt=current_system,
                temperature=temperature,
                max_tokens=max_tokens,
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
                return None
            return call_ai(
                provider=provider,
                model=model,
                user_prompt=user_msg,
                system_prompt=current_system,
                temperature=temperature,
                max_tokens=max_tokens,
            )
    except Exception as e:
        st.error(f"Erro: {e}")
        return None


def _render_antia_history(chapter_title: str, key_suffix: str = "") -> None:
    """Exibe o histórico de Pontuação Humana do capítulo."""
    import pandas as pd

    history = get_antia_score_history(chapter_title)
    if not history:
        return

    st.divider()

    col_title, col_btn = st.columns([5, 1])
    with col_title:
        st.subheader("📊 Histórico de Pontuação Humana")
    with col_btn:
        safe_key = chapter_title.replace(" ", "_").replace("/", "_")
        if st.button("Limpar", key=f"clear_antia_{safe_key}{key_suffix}",
                     help="Apagar histórico deste capítulo"):
            clear_antia_score_history(chapter_title)
            st.rerun()

    last = history[-1]
    first = history[0]
    score_last = last["score"]
    score_first = first["score"]
    delta = score_last - score_first

    # Métricas de resumo
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric(
            "Pontuação atual",
            f"{score_last}/10",
            delta=f"{'+'if delta>=0 else ''}{delta}" if len(history) > 1 else None,
        )
    with col_m2:
        st.metric("Revisões", len(history))
    with col_m3:
        status_label = (
            "Pronto para publicar" if score_last >= 8
            else ("Em desenvolvimento" if score_last >= 6 else "Revisão necessária")
        )
        st.metric("Status", f"{score_badge(score_last)} {status_label}")

    # ── Quality Guards ────────────────────────────────────────────────────────
    if score_last >= SCORE_THRESHOLDS["publication_ready"]:
        st.success(
            "**Limiar de autenticidade atingido** — Pontuação Humana ≥ 8/10. "
            "Revisões adicionais têm risco alto de homogeneizar a voz autoral. "
            "Considere encerrar o ciclo de revisão Anti-IA."
        )
    else:
        conv = check_convergence(history)
        if conv:
            st.warning(f"**Aviso de Convergência** — {conv['message']}")

        drift = check_voice_drift(history)
        if drift:
            st.warning(f"**Alerta de Deriva de Voz** — {drift['message']}")

    # Tabela de histórico
    rows = []
    for entry in history:
        s = entry["score"]
        rows.append({
            "Revisão": f"v{entry['revision']}",
            "Data": entry["timestamp"],
            "Modelo": entry["model"].split("-")[0] if "-" in entry["model"] else entry["model"],
            "Modo": "Por cena" if entry.get("mode") == "scene" else "Completo",
            "Pontuação": s,
        })

    df = pd.DataFrame(rows)

    def _color_score_cell(val):
        try:
            v = float(val)
        except (TypeError, ValueError):
            return ""
        if v >= 8:
            return "background-color: #d4edda; color: #155724"
        if v >= 6:
            return "background-color: #fff3cd; color: #856404"
        return "background-color: #f8d7da; color: #721c24"

    styled = df.style.map(_color_score_cell, subset=["Pontuação"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.caption("🟢 ≥ 8 pronto · 🟡 6–7 em desenvolvimento · 🔴 < 6 revisão necessária")

    # Gráfico de evolução
    if len(history) >= 2:
        chart_df = pd.DataFrame(
            {"Pontuação Humana": [e["score"] for e in history]},
            index=[f"v{e['revision']} {e['timestamp']}" for e in history],
        )
        st.line_chart(chart_df, y_label="Nota", use_container_width=True)


# ─── Área principal ───────────────────────────────────────────────────────────
tab_free, tab_chapter, tab_history = st.tabs([
    "✏️ Texto Livre",
    "📚 De um Capítulo",
    "📊 Histórico de Notas",
])

with tab_free:
    text_input = st.text_area(
        "Cole ou escreva o texto que deseja analisar:",
        height=300,
        placeholder="Coloque aqui o trecho que quer verificar...",
        key="anti_ia_free_text",
    )
    analyze_free = st.button(
        "🔍 Analisar Texto",
        type="primary",
        disabled=not text_input.strip(),
        key="anti_ia_run_free",
    )

with tab_chapter:
    chapters = get_chapters()
    if not chapters:
        st.info("Nenhum capítulo disponível. Crie capítulos no Editor primeiro.")
        selected_chapter_text = ""
        selected_chapter_title = ""
    else:
        chapter_options = {ch["title"]: ch["content"] for ch in chapters}
        selected_chapter_title = st.selectbox(
            "Selecione o capítulo:",
            list(chapter_options.keys()),
            key="anti_ia_chapter_select",
        )
        selected_chapter_text = chapter_options[selected_chapter_title]

        word_count = len(selected_chapter_text.split())
        st.caption(f"{word_count:,} palavras")

    scene_mode = st.toggle(
        "Analisar cena por cena",
        value=False,
        key="anti_ia_scene_mode",
        help="Divide o capítulo em cenas e analisa cada uma separadamente — mais preciso para capítulos longos.",
    )

    if scene_mode and selected_chapter_text.strip():
        scenes = split_into_scenes(selected_chapter_text)
        st.caption(f"{len(scenes)} cena(s) detectada(s)")

    label = "🔍 Analisar por Cena" if scene_mode else "🔍 Analisar Capítulo"
    analyze_chapter = st.button(
        label,
        type="primary",
        disabled=not selected_chapter_text.strip() if chapters else True,
        key="anti_ia_run_chapter",
    )

with tab_history:
    import pandas as pd

    all_antia_history = load_antia_score_history()

    if not all_antia_history:
        st.info("Nenhuma análise Anti-IA registrada ainda. Rode a análise de um capítulo para começar.")
    else:
        st.markdown("### Resumo por Capítulo")
        summary_rows = []
        for ch_title, entries in all_antia_history.items():
            last_e = entries[-1]
            first_e = entries[0]
            s_last = last_e["score"]
            s_first = first_e["score"]
            delta = s_last - s_first
            badge = score_badge(s_last)
            summary_rows.append({
                "Capítulo": ch_title,
                "Revisões": len(entries),
                "Pontuação atual": s_last,
                "Variação": f"{'+'if delta>=0 else ''}{delta}" if len(entries) > 1 else "—",
                "Status": f"{badge} {'Pronto' if s_last >= 8 else ('Em dev' if s_last >= 6 else 'Revisar')}",
            })

        summary_df = pd.DataFrame(summary_rows).set_index("Capítulo")

        def _color_summary(val):
            try:
                v = float(val)
            except (TypeError, ValueError):
                return ""
            if v >= 8:
                return "background-color: #d4edda; color: #155724"
            if v >= 6:
                return "background-color: #fff3cd; color: #856404"
            return "background-color: #f8d7da; color: #721c24"

        styled_summary = summary_df.style.map(_color_summary, subset=["Pontuação atual"])
        st.dataframe(styled_summary, use_container_width=True)

        st.divider()
        st.markdown("### Histórico Detalhado")
        for ch_title, entries in all_antia_history.items():
            with st.expander(f"🤖 {ch_title} — {len(entries)} revisão(ões)", expanded=False):
                _render_antia_history(ch_title, key_suffix="_tab")


# ─── Execução ─────────────────────────────────────────────────────────────────
if analyze_free and text_input.strip():
    st.session_state.pop("anti_ia_scene_results", None)
    with st.spinner("Analisando o texto..."):
        result = _call_ai_safe(text_input)
        if result:
            st.session_state["anti_ia_result"] = result
            st.session_state.pop("anti_ia_chapter_title", None)

if analyze_chapter and selected_chapter_text.strip():
    if scene_mode:
        scenes = split_into_scenes(selected_chapter_text)
        results: list[tuple[str, str]] = []
        best_score: int | None = None
        progress = st.progress(0, text="Preparando análise por cena...")

        for idx, (scene_title, scene_text) in enumerate(scenes):
            progress.progress(
                idx / len(scenes),
                text=f"Analisando {scene_title} ({idx + 1}/{len(scenes)})...",
            )
            result = _call_ai_safe(scene_text)
            if result:
                results.append((scene_title, result))
                s = parse_human_score(result)
                if s is not None:
                    best_score = round((best_score + s) / 2) if best_score else s

        progress.progress(1.0, text="Análise concluída!")
        if best_score is not None and selected_chapter_title:
            save_antia_score_entry(
                selected_chapter_title, best_score, model, mode="scene",
                text=selected_chapter_text,
            )
        st.session_state["anti_ia_result"] = None
        st.session_state["anti_ia_scene_results"] = results
        st.session_state["anti_ia_chapter_title"] = selected_chapter_title
    else:
        st.session_state.pop("anti_ia_scene_results", None)
        with st.spinner("Analisando o texto..."):
            result = _call_ai_safe(selected_chapter_text)
            if result:
                st.session_state["anti_ia_result"] = result
                st.session_state["anti_ia_chapter_title"] = selected_chapter_title
                score = parse_human_score(result)
                if score is not None:
                    save_antia_score_entry(
                        selected_chapter_title, score, model, mode="full",
                        text=selected_chapter_text,
                    )
                    st.success(f"✅ Análise salva — Pontuação Humana: {score}/10")
                else:
                    st.warning("⚠️ Nota não detectada no formato esperado. Verifique se a resposta contém 'Pontuação Humana: X/10'")


# ─── Resultado — modo cena por cena ───────────────────────────────────────────
if st.session_state.get("anti_ia_scene_results"):
    scene_results: list[tuple[str, str]] = st.session_state["anti_ia_scene_results"]
    st.divider()
    st.subheader(f"Análise Anti-IA — {len(scene_results)} cena(s)")

    full_combined = ""
    for scene_title, result_text in scene_results:
        full_combined += f"\n\n## {scene_title}\n\n{result_text}"
        with st.expander(f"🤖 {scene_title}", expanded=True):
            st.markdown(result_text)

    st.divider()
    st.download_button(
        "⬇️ Baixar análise completa (.txt)",
        data=full_combined.strip().encode("utf-8"),
        file_name="analise_anti_ia_cenas.txt",
        mime="text/plain; charset=utf-8",
        key="dl_anti_ia_scenes",
    )

    chapter_title = st.session_state.get("anti_ia_chapter_title", "")
    if chapter_title:
        _render_antia_history(chapter_title)

# ─── Resultado — modo texto inteiro ───────────────────────────────────────────
elif st.session_state.get("anti_ia_result"):
    st.divider()
    st.subheader("Análise Anti-IA")

    result_text = st.session_state["anti_ia_result"]
    st.markdown(result_text)

    st.download_button(
        "⬇️ Baixar análise (.txt)",
        data=result_text.encode("utf-8"),
        file_name="analise_anti_ia.txt",
        mime="text/plain; charset=utf-8",
        key="dl_anti_ia",
    )

    chapter_title = st.session_state.get("anti_ia_chapter_title", "")
    if chapter_title:
        _render_antia_history(chapter_title)
