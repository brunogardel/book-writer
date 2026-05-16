"""
Análise de Capítulo — avaliação editorial rigorosa com pontuação.
Suporta análise do capítulo inteiro ou cena por cena.
Rastreia histórico de notas por revisão.
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
    parse_scores,
    save_score_entry,
    get_score_history,
    load_score_history,
    clear_score_history,
    CRITERIA_NAMES,
    SCORE_THRESHOLDS,
    score_badge,
    check_convergence,
    check_voice_drift,
)
from utils.ai_client import call_ai, call_ai_for_task, PROVIDER_NAMES
from utils.components import model_selector, show_model_info

st.set_page_config(page_title="Análise de Capítulo — Escritor", page_icon="🔍", layout="wide")
init_session_state()

st.title("🔍 Análise de Capítulo")
st.markdown(
    "Avaliação editorial rigorosa: receba notas e feedback detalhado sobre ritmo, personagens, "
    "diálogos, tensão, estilo e muito mais — como um editor profissional avaliaria seu capítulo."
)

# Mostra modelo recomendado e custo
use_recommended_model, _ = show_model_info("analise_capitulo")

prompts = load_prompts()
prompt_data = prompts.get("analise_capitulo", {})

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    provider, model, temperature = model_selector("ac", default_temp=0.3)

    st.divider()
    st.subheader("Prompt do Editor")

    system_prompt = st.text_area(
        "System Prompt",
        value=prompt_data.get("system", ""),
        height=120,
        key="ac_system",
    )

    user_template = st.text_area(
        "Template (use {texto})",
        value=prompt_data.get("user_template", ""),
        height=280,
        key="ac_user_template",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Salvar Prompt", use_container_width=True):
            prompts["analise_capitulo"]["system"] = system_prompt
            prompts["analise_capitulo"]["user_template"] = user_template
            save_prompts(prompts)
            st.success("Salvo!")
    with col2:
        if st.button("Restaurar Padrão", use_container_width=True):
            reset_prompt("analise_capitulo")
            st.success("Restaurado!")
            st.rerun()

# ─── Helper ───────────────────────────────────────────────────────────────────
def _call_ai_safe(text: str) -> str | None:
    current_system = st.session_state.get("ac_system", system_prompt)
    current_template = st.session_state.get("ac_user_template", user_template)
    user_msg = current_template.replace("{texto}", text)
    max_tokens = st.session_state.get("max_tokens", 8192)

    try:
        # Usa modelo recomendado ou configuração manual
        if use_recommended_model:
            return call_ai_for_task(
                task="analise_capitulo",
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


def _color_score(val):
    """Cor de fundo para célula de nota (usado no pandas Styler)."""
    try:
        score = float(val)
    except (TypeError, ValueError):
        return ""
    if score >= 8:
        return "background-color: #d4edda; color: #155724"   # verde
    if score >= 6:
        return "background-color: #fff3cd; color: #856404"   # amarelo
    return "background-color: #f8d7da; color: #721c24"       # vermelho


def _render_score_history(chapter_title: str, key_suffix: str = "") -> None:
    """Exibe o histórico de notas do capítulo com tabela e gráfico."""
    import pandas as pd

    history = get_score_history(chapter_title)
    if not history:
        return

    st.divider()

    col_title, col_btn = st.columns([5, 1])
    with col_title:
        st.subheader("📊 Histórico de Notas")
    with col_btn:
        safe_key = chapter_title.replace(" ", "_").replace("/", "_")
        btn_key = f"clear_history_{safe_key}{key_suffix}"
        if st.button("Limpar", key=btn_key, help="Apagar histórico deste capítulo"):
            clear_score_history(chapter_title)
            st.rerun()

    # ── Métricas de resumo ────────────────────────────────────────────────────
    last = history[-1]
    first = history[0]
    avg_last = last.get("average", 0)
    avg_first = first.get("average", 0)
    delta = round(avg_last - avg_first, 1)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Média atual", f"{avg_last}/10",
                  delta=f"{'+' if delta >= 0 else ''}{delta}" if len(history) > 1 else None)
    with col_m2:
        st.metric("Revisões", len(history))
    with col_m3:
        best_criterion = max(last["scores"], key=last["scores"].get) if last["scores"] else "—"
        st.metric("Melhor critério", f"{last['scores'].get(best_criterion, '—')}", best_criterion)
    with col_m4:
        worst_criterion = min(last["scores"], key=last["scores"].get) if last["scores"] else "—"
        st.metric("Pior critério", f"{last['scores'].get(worst_criterion, '—')}", worst_criterion,
                  delta_color="inverse")

    # ── Quality Guards ────────────────────────────────────────────────────────
    if avg_last >= SCORE_THRESHOLDS["publication_ready"]:
        st.success(
            "**Limiar de publicação atingido** — Média atual ≥ 8/10. "
            "Revisões adicionais têm risco alto de perda de voz autoral e rendimento decrescente. "
            "Considere encerrar o ciclo de revisão."
        )
    else:
        conv = check_convergence(history)
        if conv:
            st.warning(f"**Aviso de Convergência** — {conv['message']}")

        drift = check_voice_drift(history)
        if drift:
            st.warning(f"**Alerta de Deriva de Voz** — {drift['message']}")

    # ── Tabela ────────────────────────────────────────────────────────────────
    col_labels = [f"v{e['revision']} · {e['timestamp']}" for e in history]

    # Dados numéricos para estilo
    data = {}
    for col_label, entry in zip(col_labels, history):
        col_data = {}
        for criterion in CRITERIA_NAMES:
            col_data[criterion] = entry["scores"].get(criterion, None)
        data[col_label] = col_data

    df = pd.DataFrame(data, index=CRITERIA_NAMES)

    # Linha de média
    avg_row = {
        col_label: entry.get("average")
        for col_label, entry in zip(col_labels, history)
    }
    df.loc["── Média"] = avg_row

    styled = (
        df.style
        .map(_color_score)
        .format(precision=1, na_rep="—")
    )
    st.dataframe(styled, use_container_width=True)

    st.caption("🟢 ≥ 8 pronto · 🟡 6–7 em desenvolvimento · 🔴 < 6 revisão necessária")

    # ── Gráfico de evolução da média ─────────────────────────────────────────
    if len(history) >= 2:
        avg_series = pd.DataFrame(
            {"Média": [e.get("average", 0) for e in history]},
            index=col_labels,
        )
        st.line_chart(avg_series, y_label="Nota", use_container_width=True)


# ─── Área principal ───────────────────────────────────────────────────────────
tab_chapter, tab_free, tab_history = st.tabs([
    "📚 De um Capítulo",
    "✏️ Texto Livre",
    "📊 Histórico de Notas",
])

with tab_chapter:
    chapters = get_chapters()
    if not chapters:
        st.info("Nenhum capítulo disponível. Crie capítulos no Editor primeiro.")
        selected_text = ""
        selected_title = ""
    else:
        chapter_options = {ch["title"]: ch for ch in chapters}
        selected_title = st.selectbox(
            "Selecione o capítulo para analisar:",
            list(chapter_options.keys()),
            key="ac_chapter_select",
        )
        selected_ch = chapter_options[selected_title]
        selected_text = selected_ch.get("content", "")

        word_count = len(selected_text.split())
        st.caption(f"{word_count:,} palavras")

        with st.expander("Pré-visualizar conteúdo"):
            st.text(selected_text[:1000] + ("..." if len(selected_text) > 1000 else ""))

    scene_mode = st.toggle(
        "Analisar cena por cena",
        value=False,
        key="ac_scene_mode",
        help="Divide o capítulo em cenas e analisa cada uma separadamente — mais preciso para capítulos longos.",
    )

    if scene_mode and selected_text.strip():
        scenes = split_into_scenes(selected_text)
        st.caption(f"{len(scenes)} cena(s) detectada(s)")

    label = "🔍 Analisar por Cena" if scene_mode else "🔍 Analisar Capítulo"
    run_chapter = st.button(
        label,
        type="primary",
        disabled=not (chapters and selected_text.strip()),
        key="ac_run_chapter",
    )

with tab_free:
    free_text = st.text_area(
        "Cole o texto do capítulo:",
        height=300,
        placeholder="Cole aqui o texto do capítulo que deseja analisar...",
        key="ac_free_text",
    )
    run_free = st.button(
        "🔍 Analisar Texto",
        type="primary",
        disabled=not free_text.strip(),
        key="ac_run_free",
    )

with tab_history:
    import pandas as pd

    all_history = load_score_history()

    if not all_history:
        st.info("Nenhuma análise registrada ainda. Rode a análise de um capítulo para começar a rastrear as notas.")
    else:
        # Visão geral — resumo de todos os capítulos
        st.markdown("### Resumo por Capítulo")
        summary_rows = []
        for ch_title, entries in all_history.items():
            last = entries[-1]
            first = entries[0]
            avg_last = last.get("average", 0)
            avg_first = first.get("average", 0)
            delta = round(avg_last - avg_first, 1)
            badge = score_badge(round(avg_last))
            summary_rows.append({
                "Capítulo": ch_title,
                "Revisões": len(entries),
                "Média atual": avg_last,
                "Variação": f"{'+'if delta>=0 else ''}{delta}" if len(entries) > 1 else "—",
                "Status": f"{badge} {'Pronto' if avg_last >= 8 else ('Em dev' if avg_last >= 6 else 'Revisar')}",
            })

        summary_df = pd.DataFrame(summary_rows).set_index("Capítulo")

        def _color_avg(val):
            try:
                v = float(val)
            except (TypeError, ValueError):
                return ""
            if v >= 8:
                return "background-color: #d4edda; color: #155724"
            if v >= 6:
                return "background-color: #fff3cd; color: #856404"
            return "background-color: #f8d7da; color: #721c24"

        styled_summary = summary_df.style.map(_color_avg, subset=["Média atual"])
        st.dataframe(styled_summary, use_container_width=True)

        st.divider()

        # Detalhe por capítulo
        st.markdown("### Histórico Detalhado")
        for ch_title, entries in all_history.items():
            with st.expander(f"📖 {ch_title} — {len(entries)} revisão(ões)", expanded=False):
                _render_score_history(ch_title, key_suffix="_tab")


# ─── Execução ─────────────────────────────────────────────────────────────────
if run_chapter and selected_text.strip():
    if scene_mode:
        scenes = split_into_scenes(selected_text)
        results: list[tuple[str, str]] = []
        progress = st.progress(0, text="Preparando análise por cena...")
        all_scores: dict[str, int] = {}

        for idx, (scene_title, scene_text) in enumerate(scenes):
            progress.progress(
                idx / len(scenes),
                text=f"Analisando {scene_title} ({idx + 1}/{len(scenes)})...",
            )
            result = _call_ai_safe(scene_text)
            if result:
                results.append((scene_title, result))
                # Agrega scores de todas as cenas (usa última cena que tiver a nota)
                scene_scores = parse_scores(result)
                all_scores.update(scene_scores)

        progress.progress(1.0, text="Análise concluída!")
        if all_scores and selected_title:
            save_score_entry(selected_title, all_scores, model, mode="scene", text=selected_text)
        st.session_state["ac_result"] = None
        st.session_state["ac_scene_results"] = results
        st.session_state["ac_chapter_title"] = selected_title
    else:
        st.session_state.pop("ac_scene_results", None)
        with st.spinner("Analisando o capítulo..."):
            result = _call_ai_safe(selected_text)
            if result:
                st.session_state["ac_result"] = result
                st.session_state["ac_chapter_title"] = selected_title
                scores = parse_scores(result)
                if scores:
                    save_score_entry(selected_title, scores, model, mode="full", text=selected_text)

if run_free and free_text.strip():
    st.session_state.pop("ac_scene_results", None)
    with st.spinner("Analisando o capítulo..."):
        result = _call_ai_safe(free_text)
        if result:
            st.session_state["ac_result"] = result
            st.session_state.pop("ac_chapter_title", None)


# ─── Resultado — modo cena por cena ───────────────────────────────────────────
if st.session_state.get("ac_scene_results"):
    scene_results: list[tuple[str, str]] = st.session_state["ac_scene_results"]
    st.divider()
    st.subheader(f"Parecer Editorial — {len(scene_results)} cena(s)")

    full_combined = ""
    for scene_title, result_text in scene_results:
        full_combined += f"\n\n## {scene_title}\n\n{result_text}"
        with st.expander(f"📖 {scene_title}", expanded=True):
            st.markdown(result_text)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "⬇️ Baixar análise completa (.txt)",
            data=full_combined.strip().encode("utf-8"),
            file_name="analise_capitulo_cenas.txt",
            mime="text/plain; charset=utf-8",
            key="dl_ac_scenes_txt",
        )
    with col_dl2:
        st.download_button(
            "⬇️ Baixar análise completa (.md)",
            data=full_combined.strip().encode("utf-8"),
            file_name="analise_capitulo_cenas.md",
            mime="text/markdown",
            key="dl_ac_scenes_md",
        )

    chapter_title = st.session_state.get("ac_chapter_title", "")
    if chapter_title:
        _render_score_history(chapter_title)

# ─── Resultado — modo capítulo inteiro ────────────────────────────────────────
elif st.session_state.get("ac_result"):
    st.divider()
    st.subheader("Parecer Editorial")
    result_text = st.session_state["ac_result"]
    st.markdown(result_text)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "⬇️ Baixar análise (.txt)",
            data=result_text.encode("utf-8"),
            file_name="analise_capitulo.txt",
            mime="text/plain; charset=utf-8",
            key="dl_ac_txt",
        )
    with col_dl2:
        st.download_button(
            "⬇️ Baixar análise (.md)",
            data=result_text.encode("utf-8"),
            file_name="analise_capitulo.md",
            mime="text/markdown",
            key="dl_ac_md",
        )

    chapter_title = st.session_state.get("ac_chapter_title", "")
    if chapter_title:
        _render_score_history(chapter_title)
