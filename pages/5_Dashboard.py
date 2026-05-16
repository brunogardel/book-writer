"""
Dashboard de Revisão — analisa todos os capítulos em lote e mostra
uma tabela de priorização por nota (Análise de Capítulo + Anti-IA).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import time
import streamlit as st
import pandas as pd
from utils.storage import (
    init_session_state,
    get_current_project,
    get_chapters,
    load_prompts,
    parse_scores,
    save_score_entry,
    parse_human_score,
    save_antia_score_entry,
    get_score_history,
    get_antia_score_history,
    load_score_history,
    load_antia_score_history,
    CRITERIA_NAMES,
    SCORE_THRESHOLDS,
    score_badge,
)
from utils.ai_client import call_ai, PROVIDER_NAMES
from utils.components import model_selector

st.set_page_config(
    page_title="Dashboard de Revisão — Escritor", page_icon="📊", layout="wide"
)
init_session_state()

current_project = get_current_project()
st.title("📊 Dashboard de Revisão")
st.caption(f"Projeto ativo: **{current_project}**")
st.markdown(
    "Analise todos os capítulos em lote e veja quais precisam de revisão prioritária. "
    "Os resultados ficam salvos no histórico de cada capítulo."
)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    provider, model, temperature = model_selector("dash", default_temp=0.3)
    st.divider()

    st.subheader("Análises")
    st.caption("Usa os prompts configurados nas páginas Análise e Anti-IA.")
    run_both = st.checkbox("Ambas as análises", value=True, key="dash_run_both")
    run_ac = st.checkbox("Análise de Capítulo", value=True, key="dash_run_ac", disabled=run_both)
    run_antia = st.checkbox("Anti-IA", value=True, key="dash_run_antia", disabled=run_both)

    if run_both:
        do_ac = True
        do_antia = True
    else:
        do_ac = run_ac
        do_antia = run_antia

    st.divider()
    st.subheader("Controle de Lote")

    skip_analyzed = st.checkbox(
        "Pular capítulos já analisados",
        value=True,
        key="dash_skip_analyzed",
        help=(
            "Se marcado, pula capítulos que já têm score salvo para cada tipo de análise. "
            "Permite retomar de onde parou sem repetir trabalho."
        ),
    )

    batch_options = [5, 10, 15, 20, 30, 53]
    batch_size = st.select_slider(
        "Máximo de capítulos por sessão",
        options=batch_options,
        value=10,
        key="dash_batch_size",
        help="Processa no máximo N capítulos por execução. Use valores menores para controlar custo e evitar timeouts.",
    )

    call_delay = st.select_slider(
        "Pausa entre chamadas (s)",
        options=[0.0, 0.5, 1.0, 1.5, 2.0],
        value=1.0,
        key="dash_call_delay",
        help="Intervalo entre chamadas de API. Recomendado ≥ 1s para evitar rate limit em lotes grandes.",
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _call(system: str, user_msg: str) -> str | None:
    api_key = st.session_state.get("api_keys", {}).get(provider, "")
    if not api_key:
        return None
    max_tokens = st.session_state.get("max_tokens", 8192)
    try:
        return call_ai(
            provider=provider,
            model=model,
            user_prompt=user_msg,
            system_prompt=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        st.warning(f"Erro na API: {e}")
        return None


def _priority_label(score: float) -> str:
    if score < SCORE_THRESHOLDS["developing"]:
        return "🔴 Urgente"
    if score < SCORE_THRESHOLDS["publication_ready"]:
        return "🟡 Revisar"
    return "🟢 Pronto"


def _color_score_cell(val):
    try:
        v = float(val)
    except (TypeError, ValueError):
        return ""
    if v >= SCORE_THRESHOLDS["publication_ready"]:
        return "background-color: #d4edda; color: #155724"
    if v >= SCORE_THRESHOLDS["developing"]:
        return "background-color: #fff3cd; color: #856404"
    return "background-color: #f8d7da; color: #721c24"


# ─── Capítulos disponíveis ────────────────────────────────────────────────────
chapters = get_chapters()

if not chapters:
    st.info("Nenhum capítulo disponível. Importe um livro primeiro em **📥 Importar**.")
    st.stop()

st.markdown(f"**{len(chapters)} capítulo(s)** no projeto **{current_project}**")

# ─── Pré-computar fila de trabalho ───────────────────────────────────────────
ac_history_cur = load_score_history()
antia_history_cur = load_antia_score_history()

def _needs_ac(title: str) -> bool:
    return not bool(ac_history_cur.get(title))

def _needs_antia(title: str) -> bool:
    return not bool(antia_history_cur.get(title))

queue = []
for ch in chapters:
    title = ch.get("title", "")
    content = ch.get("content", "")
    if not content.strip():
        continue
    need_ac = do_ac and (not skip_analyzed or _needs_ac(title))
    need_antia = do_antia and (not skip_analyzed or _needs_antia(title))
    if need_ac or need_antia:
        queue.append((ch, need_ac, need_antia))

# Aplica limite de batch
queue_limited = queue[:batch_size]
skipped_count = len(chapters) - len([c for c in chapters if c.get("content", "").strip()])
already_done = len(chapters) - len(queue) - skipped_count

# ─── Painel de estimativa ─────────────────────────────────────────────────────
api_ok = bool(st.session_state.get("api_keys", {}).get(provider, ""))
if not api_ok:
    st.error(
        f"Chave de API para **{PROVIDER_NAMES[provider]}** não configurada. "
        "Vá em ⚙️ Configurações."
    )

analyses_count = sum((1 if nac else 0) + (1 if nai else 0) for _, nac, nai in queue_limited)
est_seconds = analyses_count * (15 + call_delay)
est_min = int(est_seconds // 60)
est_sec = int(est_seconds % 60)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Total capítulos", len(chapters))
col_m2.metric("Já analisados", already_done)
col_m3.metric("Nesta sessão", len(queue_limited))
col_m4.metric("Tempo estimado", f"~{est_min}m {est_sec:02d}s")

if len(queue) > batch_size:
    st.info(
        f"**{len(queue) - batch_size} capítulo(s) restantes** após esta sessão. "
        f"Aumente o limite ou rode novamente para continuar."
    )
elif len(queue) == 0:
    st.success("Todos os capítulos já foram analisados. Resultados abaixo.")

col_btn, col_info = st.columns([2, 3])
with col_btn:
    run_batch = st.button(
        f"🚀 Analisar {len(queue_limited)} capítulo(s)",
        type="primary",
        disabled=not api_ok or len(queue_limited) == 0,
        key="dash_run_batch",
        use_container_width=True,
    )
with col_info:
    types_label = (
        "Análise de Capítulo + Anti-IA" if do_ac and do_antia
        else "Análise de Capítulo" if do_ac else "Anti-IA"
    )
    st.caption(
        f"{analyses_count} chamada(s) de API · {types_label} · "
        f"Pausa: {call_delay}s entre chamadas"
    )

# ─── Execução em lote ─────────────────────────────────────────────────────────
if run_batch and queue_limited:
    prompts = load_prompts()
    ac_system = prompts.get("analise_capitulo", {}).get("system", "")
    ac_template = prompts.get("analise_capitulo", {}).get("user_template", "")
    antia_system = prompts.get("anti_ia", {}).get("system", "")
    antia_template = prompts.get("anti_ia", {}).get("user_template", "")

    progress = st.progress(0, text="Iniciando análise em lote...")
    errors = []
    done = 0

    for idx, (ch, need_ac, need_antia) in enumerate(queue_limited):
        title = ch.get("title", f"Capítulo {idx + 1}")
        content = ch.get("content", "")
        step_base = idx / len(queue_limited)

        # ── Análise de Capítulo ───────────────────────────────────────────────
        if need_ac:
            progress.progress(
                step_base,
                text=f"[{idx+1}/{len(queue_limited)}] Análise — {title}...",
            )
            user_msg = ac_template.replace("{texto}", content)
            result = _call(ac_system, user_msg)
            if result:
                scores = parse_scores(result)
                if scores:
                    save_score_entry(title, scores, model, mode="full", text=content)
                    done += 1
            else:
                errors.append(f"AC:{title}")
            if call_delay > 0:
                time.sleep(call_delay)

        # ── Anti-IA ───────────────────────────────────────────────────────────
        if need_antia:
            progress.progress(
                step_base + (0.4 / len(queue_limited) if need_ac else 0),
                text=f"[{idx+1}/{len(queue_limited)}] Anti-IA — {title}...",
            )
            user_msg = antia_template.replace("{texto}", content)
            result = _call(antia_system, user_msg)
            if result:
                score = parse_human_score(result)
                if score is not None:
                    save_antia_score_entry(title, score, model, mode="full", text=content)
                    done += 1
            else:
                errors.append(f"Anti-IA:{title}")
            if call_delay > 0:
                time.sleep(call_delay)

    progress.progress(1.0, text="Análise concluída!")

    remaining = len(queue) - len(queue_limited)
    if errors:
        st.warning(f"Erros em {len(errors)} chamada(s): {', '.join(errors[:5])}")
    if remaining > 0:
        st.info(
            f"**{done} análise(s) salvas.** "
            f"Ainda faltam **{remaining} capítulo(s)**. "
            "Clique em **Analisar** novamente para continuar."
        )
    else:
        st.success(f"Lote concluído — {done} análise(s) salvas!")

st.divider()

# ─── Dashboard de Priorização ─────────────────────────────────────────────────
ac_history = load_score_history()
antia_history = load_antia_score_history()

has_ac = bool(ac_history)
has_antia = bool(antia_history)

if not has_ac and not has_antia:
    st.info("Nenhuma análise registrada ainda. Clique em **Analisar** para começar.")
    st.stop()

# Monta tabela unificada
rows = []
for ch in chapters:
    title = ch.get("title", "")
    words = len(ch.get("content", "").split())

    # Score da análise de capítulo
    ac_entries = ac_history.get(title, [])
    ac_avg = ac_entries[-1].get("average") if ac_entries else None

    # Score Anti-IA
    antia_entries = antia_history.get(title, [])
    antia_score = antia_entries[-1].get("score") if antia_entries else None

    # Prioridade composta (mínimo dos scores disponíveis)
    scores_available = [s for s in [ac_avg, antia_score] if s is not None]
    composite = round(min(scores_available), 1) if scores_available else None

    rows.append({
        "Capítulo": title,
        "Palavras": words,
        "Análise (média)": ac_avg,
        "Anti-IA": antia_score,
        "Prioridade": composite,
        "Status": _priority_label(composite) if composite is not None else "—",
        "Revisões AC": len(ac_entries),
        "Revisões Anti-IA": len(antia_entries),
    })

# Ordena: Prólogo primeiro, depois não analisados por último, depois por menor Prioridade
def sort_key(r):
    # Prólogo sempre primeiro
    if r["Capítulo"].lower() in ("prólogo", "prologo", "prefácio", "prefacio"):
        return (0, False, 0)
    # Sem análise por último
    if r["Prioridade"] is None:
        return (1, True, 99)
    # Resto por prioridade (menor primeiro)
    return (1, False, r["Prioridade"])

rows.sort(key=sort_key)

df = pd.DataFrame(rows)

# ── Métricas de resumo ────────────────────────────────────────────────────────
urgentes = sum(1 for r in rows if r["Prioridade"] is not None and r["Prioridade"] < SCORE_THRESHOLDS["developing"])
revisar = sum(1 for r in rows if r["Prioridade"] is not None and SCORE_THRESHOLDS["developing"] <= r["Prioridade"] < SCORE_THRESHOLDS["publication_ready"])
prontos = sum(1 for r in rows if r["Prioridade"] is not None and r["Prioridade"] >= SCORE_THRESHOLDS["publication_ready"])
sem_analise = sum(1 for r in rows if r["Prioridade"] is None)

col1, col2, col3, col4 = st.columns(4)
col1.metric("🔴 Urgente (< 6)", urgentes)
col2.metric("🟡 Revisar (6–7)", revisar)
col3.metric("🟢 Pronto (≥ 8)", prontos)
col4.metric("⬜ Não analisado", sem_analise)

st.markdown("### Tabela de Priorização")
st.caption("Ordenado do mais urgente para o pronto. Clique em um cabeçalho para reordenar.")

# Aplica cores às colunas de score
score_cols = [c for c in ["Análise (média)", "Anti-IA", "Prioridade"] if c in df.columns]

def _color_row(row):
    p = row.get("Prioridade")
    styles = [""] * len(row)
    return styles

styled = (
    df.style
    .map(_color_score_cell, subset=score_cols)
    .format(
        {
            "Análise (média)": lambda v: f"{v:.1f}" if v is not None else "—",
            "Anti-IA": lambda v: f"{v}" if v is not None else "—",
            "Prioridade": lambda v: f"{v:.1f}" if v is not None else "—",
            "Palavras": lambda v: f"{v:,}",
        }
    )
    .hide(axis="index")
)

st.dataframe(styled, use_container_width=True, hide_index=True)

# ── Detalhe expandível por capítulo ──────────────────────────────────────────
st.divider()
st.markdown("### Detalhe por Capítulo")

for row in rows:
    title = row["Capítulo"]
    status = row["Status"]
    ac_avg_val = row["Análise (média)"]
    antia_val = row["Anti-IA"]

    summary = f"{status}  |  AC: {f'{ac_avg_val:.1f}' if ac_avg_val else '—'}  |  Anti-IA: {antia_val if antia_val else '—'}"
    with st.expander(f"{title} — {summary}", expanded=False):
        ac_entries = ac_history.get(title, [])
        antia_entries = antia_history.get(title, [])

        if ac_entries:
            last_ac = ac_entries[-1]
            st.markdown("**Análise de Capítulo — última revisão**")
            score_cols_detail = list(last_ac.get("scores", {}).items())
            if score_cols_detail:
                cols = st.columns(min(4, len(score_cols_detail)))
                for i, (crit, val) in enumerate(score_cols_detail):
                    cols[i % 4].metric(crit[:18], f"{val}/10")

        if antia_entries:
            last_antia = antia_entries[-1]
            st.markdown("**Anti-IA — última revisão**")
            st.metric("Pontuação Humana", f"{last_antia['score']}/10")

        if not ac_entries and not antia_entries:
            st.info("Este capítulo ainda não foi analisado.")
