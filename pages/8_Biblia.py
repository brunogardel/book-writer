"""
Bíblia do Livro — fichas de personagens, locais, linha do tempo e notas de mundo.
Inclui geração automática via IA a partir do manuscrito.
"""

import sys
import json
import re
from pathlib import Path
import uuid

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from utils.storage import (
    init_session_state,
    load_bible,
    save_bible,
    restore_bible_backup,
    has_bible_backup,
    load_prompts,
    save_prompts,
    reset_prompt,
    get_chapters,
    get_full_text,
)
from utils.ai_client import call_ai, PROVIDER_NAMES
from utils.components import model_selector

st.set_page_config(page_title="Bíblia do Livro — Escritor", page_icon="📖", layout="wide")
init_session_state()

st.title("📖 Bíblia do Livro")
st.markdown(
    "Mantenha fichas de personagens, locais, eventos da linha do tempo e notas de world-building. "
    "Consulte enquanto escreve para manter consistência."
)

bible = load_bible()

# ─── Restaurar Backup ─────────────────────────────────────────────────────────
if has_bible_backup():
    with st.expander("Backup disponível — clique para restaurar"):
        st.warning(
            "Existe um backup automático da bíblia anterior ao último salvamento. "
            "Se você perdeu dados acidentalmente, clique abaixo para restaurar."
        )
        if st.button("Restaurar Backup", type="primary"):
            if restore_bible_backup():
                st.success("Backup restaurado com sucesso! Recarregando...")
                st.rerun()
            else:
                st.error("Falha ao restaurar o backup.")

tab_ia, tab_chars, tab_locs, tab_timeline, tab_myth, tab_notes = st.tabs(
    ["🤖 Gerar com IA", "👥 Personagens", "🗺️ Locais", "📅 Linha do Tempo", "⚡ Mitologia", "📝 Notas Gerais"]
)

# ─── Geração com IA ───────────────────────────────────────────────────────────
with tab_ia:
    st.subheader("Gerar Bíblia Automaticamente")
    st.markdown(
        "A IA analisa o manuscrito **capítulo por capítulo** e extrai informações. "
        "Escolha **um tipo por vez** para runs menores, mais rápidos e confiáveis."
    )

    # ── Seletor de tipo ────────────────────────────────────────────────────────
    _TIPO_OPTS = ["👥 Personagens", "🗺️ Locais", "📅 Linha do Tempo", "⚡ Mitologia", "📝 Notas", "🌐 Tudo"]
    _TIPO_FIELD = {
        "👥 Personagens":    "characters",
        "🗺️ Locais":         "locations",
        "📅 Linha do Tempo": "timeline",
        "⚡ Mitologia":      "mythology",
        "📝 Notas":          "notes",
        "🌐 Tudo":           None,
    }
    _TIPO_HINT = {
        "characters": (
            "\n\nIMPORTANTE: Foque APENAS em personagens (campo 'characters'). "
            "Retorne listas vazias para 'locations', 'timeline' e 'mythology', e string vazia para 'notes'."
        ),
        "locations": (
            "\n\nIMPORTANTE: Foque APENAS em locais (campo 'locations'). "
            "Retorne listas vazias para 'characters', 'timeline' e 'mythology', e string vazia para 'notes'."
        ),
        "timeline": (
            "\n\nIMPORTANTE: Foque APENAS na linha do tempo/eventos (campo 'timeline'). "
            "Retorne listas vazias para 'characters', 'locations' e 'mythology', e string vazia para 'notes'."
        ),
        "mythology": (
            "\n\nIMPORTANTE: Foque APENAS em elementos mitológicos/world-building (campo 'mythology'). "
            "Retorne listas vazias para 'characters', 'locations' e 'timeline', e string vazia para 'notes'."
        ),
        "notes": (
            "\n\nIMPORTANTE: Foque APENAS em notas gerais de world-building (campo 'notes', string). "
            "Retorne listas vazias para 'characters', 'locations', 'timeline' e 'mythology'."
        ),
    }

    tipo_geracao = st.radio(
        "O que extrair neste run:",
        _TIPO_OPTS,
        horizontal=True,
        key="bib_tipo",
        index=0,
    )
    tipo_focus = _TIPO_FIELD[tipo_geracao]  # None = Tudo

    if tipo_focus is not None:
        st.info(
            f"Modo **{tipo_geracao}**: a IA focará apenas nesse campo em cada capítulo, "
            "tornando a extração e a consolidação muito mais rápidas e precisas."
        )

    # Seletor de IA na sidebar
    with st.sidebar:
        provider, model, temperature = model_selector("biblia", default_temp=0.3)
        st.divider()
        st.subheader("Prompts da Bíblia")
        prompts = load_prompts()

        prompt_edit_key = st.selectbox(
            "Editar prompt:",
            ["biblia_geracao", "biblia_merge"],
            format_func=lambda k: {"biblia_geracao": "📄 Extração por capítulo",
                                    "biblia_merge": "🔀 Consolidação (merge)"}[k],
            key="bib_prompt_select",
        )
        bp = prompts.get(prompt_edit_key, {})
        sys_p = st.text_area("System Prompt", value=bp.get("system", ""), height=100, key=f"bib_sys_{prompt_edit_key}")
        usr_p = st.text_area("Template", value=bp.get("user_template", ""), height=180, key=f"bib_usr_{prompt_edit_key}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Salvar", use_container_width=True, key="bib_save_prompt"):
                prompts[prompt_edit_key]["system"] = sys_p
                prompts[prompt_edit_key]["user_template"] = usr_p
                save_prompts(prompts)
                st.success("Salvo!")
        with col2:
            if st.button("Restaurar", use_container_width=True, key="bib_reset_prompt"):
                reset_prompt(prompt_edit_key)
                st.success("Restaurado!")
                st.rerun()

    # ── Seleção de capítulos ───────────────────────────────────────────────────
    chapters = get_chapters()
    if not chapters:
        st.warning("Nenhum capítulo encontrado. Importe ou escreva o livro primeiro.")
    else:
        total_words = sum(len(c.get("content", "").split()) for c in chapters)

        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.metric("Capítulos disponíveis", len(chapters))
        with col_info2:
            st.metric("Total de palavras", f"{total_words:,}")

        use_all = st.checkbox("Usar todos os capítulos", value=True, key="bib_use_all")

        if use_all:
            selected_chs = chapters
        else:
            selected_titles = st.multiselect(
                "Selecione os capítulos:",
                options=[c["title"] for c in chapters],
                default=[c["title"] for c in chapters],
            )
            selected_chs = [c for c in chapters if c["title"] in selected_titles]

        if not selected_chs:
            st.warning("Selecione ao menos um capítulo.")
        else:
            st.caption(
                f"**{len(selected_chs)} capítulo(s)** serão processados individualmente. "
                f"Total: {sum(len(c.get('content','').split()) for c in selected_chs):,} palavras."
            )

        merge_mode = st.radio(
            "Como combinar com a bíblia existente:",
            ["Adicionar ao que já existe", "Substituir tudo"],
            horizontal=True,
            key="bib_merge_mode",
        )
        if merge_mode == "Substituir tudo":
            st.error("**ATENÇÃO:** 'Substituir tudo' apagará permanentemente os personagens, mitologia e linha do tempo já salvos. Um backup automático será feito antes de salvar.")

        run_gen = st.button(
            f"🤖 Gerar {tipo_geracao} com IA",
            type="primary",
            disabled=not selected_chs,
        )

        # ── Função auxiliar para parsear JSON da resposta da IA ───────────────
        def _parse_json_response(raw: str) -> dict:
            clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
            match = re.search(r"\{.*\}", clean, re.DOTALL)
            if match:
                clean = match.group(0)
            return json.loads(clean)

        # ── Deduplicação Python antes do merge ────────────────────────────────
        def _dedup_by_name(items: list, key: str = "name") -> list:
            """
            Agrupa entradas pelo campo `key` (case-insensitive).
            Para campos de texto (str): concatena valores distintos com " | " para
            que a IA de merge receba todas as informações e decida o que fica.
            Para listas: une sem duplicatas.
            Reduz N entradas repetidas para 1 entrada rica por personagem/local/etc.
            """
            seen: dict = {}
            for item in items:
                k = item.get(key, "").strip().lower()
                if not k:
                    k = f"__unnamed_{len(seen)}"
                if k not in seen:
                    seen[k] = dict(item)
                else:
                    existing = seen[k]
                    for field, val in item.items():
                        if field == key:
                            continue  # preserva o nome original
                        ex_val = existing.get(field, "")
                        if isinstance(val, str) and val.strip():
                            if not ex_val:
                                existing[field] = val
                            elif val.strip() not in ex_val:
                                # Concatena apenas se a info for nova/diferente
                                existing[field] = f"{ex_val} | {val.strip()}"
                        elif isinstance(val, list):
                            # Une listas sem duplicatas
                            ex_list = existing.get(field, [])
                            for v in val:
                                if v not in ex_list:
                                    ex_list.append(v)
                            existing[field] = ex_list
            return list(seen.values())

        # ── Processamento capítulo por capítulo ───────────────────────────────
        if run_gen and selected_chs:
            api_key = st.session_state.get("api_keys", {}).get(provider, "")
            if not api_key:
                st.error(f"Chave de API para **{PROVIDER_NAMES[provider]}** não configurada.")
            else:
                all_prompts = load_prompts()
                gen_p = all_prompts.get("biblia_geracao", {})
                merge_p = all_prompts.get("biblia_merge", {})

                accumulated = {"characters": [], "locations": [], "timeline": [], "mythology": [], "notes": ""}
                errors = []

                progress_bar = st.progress(0, text="Iniciando...")
                status_box = st.empty()
                log_area = st.expander("Log detalhado", expanded=False)

                total = len(selected_chs)
                success_count = 0

                for idx, chapter in enumerate(selected_chs):
                    chapter_title = chapter.get("title", f"Capítulo {idx+1}")
                    chapter_content = chapter.get("content", "").strip()

                    progress_bar.progress(
                        idx / (total + 1),
                        text=f"Extraindo: {chapter_title} ({idx+1}/{total})..."
                    )
                    status_box.info(f"Processando **{chapter_title}**...")

                    if not chapter_content:
                        log_area.warning(f"⚠️ {chapter_title}: capítulo vazio, pulando.")
                        continue

                    try:
                        base_msg = gen_p.get("user_template", "{texto}").replace("{texto}", chapter_content)
                        # Adiciona instrução de foco quando não é "Tudo"
                        if tipo_focus and tipo_focus in _TIPO_HINT:
                            user_msg = base_msg + _TIPO_HINT[tipo_focus]
                        else:
                            user_msg = base_msg

                        raw = call_ai(
                            provider=provider,
                            model=model,
                            user_prompt=user_msg,
                            system_prompt=gen_p.get("system", ""),
                            temperature=temperature,
                            max_tokens=4096,
                        )
                        chapter_data = _parse_json_response(raw)

                        # Acumula apenas o tipo selecionado (ou tudo)
                        if tipo_focus in (None, "characters"):
                            accumulated["characters"].extend(chapter_data.get("characters", []))
                        if tipo_focus in (None, "locations"):
                            accumulated["locations"].extend(chapter_data.get("locations", []))
                        if tipo_focus in (None, "timeline"):
                            accumulated["timeline"].extend(chapter_data.get("timeline", []))
                        if tipo_focus in (None, "mythology"):
                            accumulated["mythology"].extend(chapter_data.get("mythology", []))
                        if tipo_focus in (None, "notes"):
                            ch_notes = chapter_data.get("notes", "")
                            if ch_notes:
                                accumulated["notes"] = (
                                    f"{accumulated['notes']}\n\n{ch_notes}".strip()
                                    if accumulated["notes"] else ch_notes
                                )

                        # Log apenas do campo relevante
                        if tipo_focus == "characters":
                            log_area.success(f"✅ {chapter_title}: {len(chapter_data.get('characters',[]))} personagens.")
                        elif tipo_focus == "locations":
                            log_area.success(f"✅ {chapter_title}: {len(chapter_data.get('locations',[]))} locais.")
                        elif tipo_focus == "timeline":
                            log_area.success(f"✅ {chapter_title}: {len(chapter_data.get('timeline',[]))} eventos.")
                        elif tipo_focus == "mythology":
                            log_area.success(f"✅ {chapter_title}: {len(chapter_data.get('mythology',[]))} elementos mitológicos.")
                        elif tipo_focus == "notes":
                            log_area.success(f"✅ {chapter_title}: notas extraídas.")
                        else:
                            log_area.success(
                                f"✅ {chapter_title}: "
                                f"{len(chapter_data.get('characters',[]))} personagens, "
                                f"{len(chapter_data.get('locations',[]))} locais, "
                                f"{len(chapter_data.get('timeline',[]))} eventos, "
                                f"{len(chapter_data.get('mythology',[]))} elem. mitológicos."
                            )
                        success_count += 1

                    except json.JSONDecodeError:
                        errors.append(chapter_title)
                        log_area.error(f"❌ {chapter_title}: resposta inválida da IA.")
                    except Exception as e:
                        errors.append(chapter_title)
                        log_area.error(f"❌ {chapter_title}: {e}")

                # ── Passo de consolidação (merge) ─────────────────────────────
                if success_count > 0:
                    progress_bar.progress(
                        total / (total + 1),
                        text="Consolidando e deduplicando informações..."
                    )

                    # ── Deduplicação Python antes de montar o payload ─────────
                    _KEY_MAP = {
                        "characters": "name",
                        "locations":  "name",
                        "timeline":   "title",
                        "mythology":  "name",
                    }
                    deduped = {}
                    for field, key in _KEY_MAP.items():
                        raw_list = accumulated.get(field, [])
                        deduped[field] = _dedup_by_name(raw_list, key=key) if raw_list else []

                    # Monta o payload do merge — apenas o tipo selecionado para reduzir tokens
                    if tipo_focus and tipo_focus != "notes":
                        before = len(accumulated[tipo_focus])
                        after  = len(deduped[tipo_focus])
                        merge_payload = {tipo_focus: deduped[tipo_focus]}
                        status_box.info(
                            f"Pré-dedup: {before} → **{after}** entradas de **{tipo_geracao}**. "
                            "Consolidando com IA..."
                        )
                    elif tipo_focus == "notes":
                        merge_payload = {"notes": accumulated["notes"]}
                        status_box.info("Consolidando notas...")
                    else:
                        merge_payload = {
                            "characters": deduped["characters"],
                            "locations":  deduped["locations"],
                            "timeline":   deduped["timeline"],
                            "mythology":  deduped["mythology"],
                            "notes":      accumulated["notes"],
                        }
                        status_box.info(
                            f"Pré-dedup: {len(deduped['characters'])} personagens, "
                            f"{len(deduped['locations'])} locais, "
                            f"{len(deduped['timeline'])} eventos. Consolidando..."
                        )

                    # ── Função de merge em lote (chunks) ─────────────────────
                    MERGE_CHUNK = 18  # máx entradas por chamada de merge

                    def _merge_list_chunked(items: list, field_name: str) -> list:
                        """
                        Divide `items` em lotes de MERGE_CHUNK e faz uma chamada de merge
                        por lote. Retorna a lista consolidada. Se a lista for pequena o
                        suficiente, faz uma única chamada.
                        """
                        if not items:
                            return []

                        merged_all = []
                        chunks = [items[i:i+MERGE_CHUNK] for i in range(0, len(items), MERGE_CHUNK)]
                        hint = _TIPO_HINT.get(field_name, "")

                        for c_idx, chunk in enumerate(chunks):
                            chunk_payload = {field_name: chunk}
                            chunk_user = (
                                merge_p.get("user_template", "{biblia_acumulada}")
                                .replace("{biblia_acumulada}",
                                         json.dumps(chunk_payload, ensure_ascii=False, indent=2))
                            ) + hint

                            status_box.info(
                                f"Consolidando lote {c_idx+1}/{len(chunks)} "
                                f"({len(chunk)} entradas)..."
                            )
                            raw_c = call_ai(
                                provider=provider,
                                model=model,
                                user_prompt=chunk_user,
                                system_prompt=merge_p.get("system", ""),
                                temperature=0.1,
                                max_tokens=8192,
                            )
                            parsed_c = _parse_json_response(raw_c)
                            merged_all.extend(parsed_c.get(field_name, chunk))

                        return merged_all

                    try:
                        # Para tipos focados: merge chunked da lista
                        if tipo_focus and tipo_focus != "notes":
                            merged_list = _merge_list_chunked(
                                merge_payload[tipo_focus], tipo_focus
                            )
                            final_data = dict(accumulated)
                            final_data[tipo_focus] = merged_list

                        elif tipo_focus == "notes":
                            # Notas: merge simples (texto, não lista)
                            merge_user = (
                                merge_p.get("user_template", "{biblia_acumulada}")
                                .replace("{biblia_acumulada}",
                                         json.dumps(merge_payload, ensure_ascii=False, indent=2))
                            ) + _TIPO_HINT.get("notes", "")
                            raw_merged = call_ai(
                                provider=provider, model=model,
                                user_prompt=merge_user,
                                system_prompt=merge_p.get("system", ""),
                                temperature=0.1, max_tokens=4096,
                            )
                            merged_data = _parse_json_response(raw_merged)
                            final_data = dict(accumulated)
                            final_data["notes"] = merged_data.get("notes", accumulated["notes"])

                        else:
                            # Tudo: merge chunked por campo
                            final_data = dict(accumulated)
                            for field in ("characters", "locations", "timeline", "mythology"):
                                if merge_payload.get(field):
                                    final_data[field] = _merge_list_chunked(
                                        merge_payload[field], field
                                    )
                            final_data["notes"] = accumulated["notes"]

                        st.session_state["biblia_gerada"] = final_data
                        st.session_state["biblia_gerada_tipo"] = tipo_focus
                        progress_bar.progress(1.0, text="Concluído!")
                        status_box.success(
                            f"**{tipo_geracao}** gerado a partir de {success_count}/{total} capítulos! "
                            "Revise abaixo antes de salvar."
                        )
                        if errors:
                            st.warning(f"Capítulos com erro (não incluídos): {', '.join(errors)}")

                    except json.JSONDecodeError:
                        st.error("Erro na etapa de consolidação: resposta inválida. Verifique o log.")
                        with st.expander("Resposta bruta da consolidação"):
                            st.code(raw_merged if 'raw_merged' in dir() else "(sem resposta)")
                    except Exception as e:
                        st.error(f"Erro na consolidação: {e}")
                else:
                    progress_bar.empty()
                    status_box.error("Nenhum capítulo foi processado com sucesso.")

        # ── Revisão e salvamento ───────────────────────────────────────────────
        if "biblia_gerada" in st.session_state:
            data = st.session_state["biblia_gerada"]
            _saved_tipo = st.session_state.get("biblia_gerada_tipo")  # None = Tudo
            st.divider()
            st.subheader("Revisão antes de salvar")

            # Personagens
            if _saved_tipo in (None, "characters"):
                chars_gen = data.get("characters", [])
                st.markdown(f"**👥 {len(chars_gen)} personagem(ns) encontrado(s)**")
                for i, ch in enumerate(chars_gen):
                    with st.expander(f"  {ch.get('name', f'Personagem {i+1}')} — {ch.get('role', '')}"):
                        ch["name"] = st.text_input("Nome", value=ch.get("name", ""), key=f"gen_cn_{i}")
                        ch["role"] = st.selectbox("Papel", ["Protagonista","Antagonista","Secundário","Figurante"],
                            index=["Protagonista","Antagonista","Secundário","Figurante"].index(ch.get("role","Secundário"))
                            if ch.get("role","Secundário") in ["Protagonista","Antagonista","Secundário","Figurante"] else 2,
                            key=f"gen_cr_{i}")
                        ch["age"] = st.text_input("Idade", value=ch.get("age", ""), key=f"gen_ca_{i}")
                        ch["appearance"] = st.text_area("Aparência", value=ch.get("appearance", ""), height=60, key=f"gen_cap_{i}")
                        ch["personality"] = st.text_area("Personalidade", value=ch.get("personality", ""), height=60, key=f"gen_cper_{i}")
                        ch["motivation"] = st.text_area("Motivação", value=ch.get("motivation", ""), height=60, key=f"gen_cmot_{i}")
                        ch["backstory"] = st.text_area("Backstory", value=ch.get("backstory", ""), height=60, key=f"gen_cbs_{i}")
                        ch["arc"] = st.text_area("Arco", value=ch.get("arc", ""), height=60, key=f"gen_carc_{i}")
            else:
                chars_gen = []

            # Locais
            if _saved_tipo in (None, "locations"):
                locs_gen = data.get("locations", [])
                st.markdown(f"**🗺️ {len(locs_gen)} local(is) encontrado(s)**")
                for i, loc in enumerate(locs_gen):
                    with st.expander(f"  {loc.get('name', f'Local {i+1}')}"):
                        loc["name"] = st.text_input("Nome", value=loc.get("name", ""), key=f"gen_ln_{i}")
                        loc["type"] = st.text_input("Tipo", value=loc.get("type", ""), key=f"gen_lt_{i}")
                        loc["description"] = st.text_area("Descrição", value=loc.get("description", ""), height=60, key=f"gen_ld_{i}")
                        loc["atmosphere"] = st.text_area("Atmosfera", value=loc.get("atmosphere", ""), height=60, key=f"gen_la_{i}")
                        loc["significance"] = st.text_area("Importância", value=loc.get("significance", ""), height=60, key=f"gen_ls_{i}")
            else:
                locs_gen = []

            # Timeline
            if _saved_tipo in (None, "timeline"):
                tl_gen = data.get("timeline", [])
                st.markdown(f"**📅 {len(tl_gen)} evento(s) encontrado(s)**")
                for i, ev in enumerate(tl_gen):
                    with st.expander(f"  {ev.get('date','—')} — {ev.get('title', f'Evento {i+1}')}"):
                        ev["date"] = st.text_input("Data/Período", value=ev.get("date",""), key=f"gen_ed_{i}")
                        ev["title"] = st.text_input("Título", value=ev.get("title",""), key=f"gen_et_{i}")
                        ev["description"] = st.text_area("Descrição", value=ev.get("description",""), height=60, key=f"gen_edesc_{i}")
                        # characters pode vir como lista da IA — normaliza para string
                        _ev_chars = ev.get("characters", "")
                        if isinstance(_ev_chars, list):
                            _ev_chars = ", ".join(str(c) for c in _ev_chars)
                        ev["characters"] = st.text_input("Personagens", value=_ev_chars, key=f"gen_ec_{i}")
                        ev["importance"] = st.selectbox("Importância", ["Alta","Médio","Baixo"],
                            index=["Alta","Médio","Baixo"].index(ev.get("importance","Médio"))
                            if ev.get("importance","Médio") in ["Alta","Médio","Baixo"] else 1,
                            key=f"gen_ei_{i}")
            else:
                tl_gen = []

            # Mitologia
            if _saved_tipo in (None, "mythology"):
                myth_gen = data.get("mythology", [])
                st.markdown(f"**⚡ {len(myth_gen)} elemento(s) mitológico(s) encontrado(s)**")
                _myth_types = ["Divindade", "Mito de Criação", "Lenda", "Profecia", "Religião", "Ritual", "Símbolo", "Outro"]
                for i, myth in enumerate(myth_gen):
                    with st.expander(f"  {myth.get('name', f'Elemento {i+1}')} — {myth.get('type', '')}"):
                        myth["name"] = st.text_input("Nome", value=myth.get("name", ""), key=f"gen_mn_{i}")
                        myth["type"] = st.selectbox(
                            "Tipo", _myth_types,
                            index=_myth_types.index(myth.get("type", "Outro")) if myth.get("type", "Outro") in _myth_types else 7,
                            key=f"gen_mt_{i}",
                        )
                        myth["description"] = st.text_area("Descrição", value=myth.get("description", ""), height=80, key=f"gen_md_{i}")
                        myth["origin"] = st.text_area("Origem no mundo", value=myth.get("origin", ""), height=60, key=f"gen_mo_{i}")
                        myth["believers"] = st.text_input("Quem acredita / pratica", value=myth.get("believers", ""), key=f"gen_mb_{i}")
                        myth["significance"] = st.text_area("Importância para a narrativa", value=myth.get("significance", ""), height=60, key=f"gen_ms_{i}")
                        myth["notes"] = st.text_area("Notas", value=myth.get("notes", ""), height=40, key=f"gen_mno_{i}")
            else:
                myth_gen = []

            # Notas
            if _saved_tipo in (None, "notes"):
                notes_gen = data.get("notes", "")
                st.markdown("**📝 Notas de World-Building**")
                notes_gen = st.text_area("Notas", value=notes_gen, height=100, key="gen_notes")
            else:
                notes_gen = ""

            st.divider()
            if st.button("💾 Salvar Resultado", type="primary", use_container_width=True):
                empty_bible = {"characters": [], "locations": [], "timeline": [], "mythology": [], "notes": ""}
                current_bible = load_bible() if merge_mode == "Adicionar ao que já existe" else dict(empty_bible)

                # Adiciona IDs únicos e salva apenas o que foi gerado
                if _saved_tipo in (None, "characters") and chars_gen:
                    for ch in chars_gen:
                        ch.setdefault("id", str(uuid.uuid4()))
                        ch.setdefault("notes", "")
                    combined = current_bible.get("characters", []) + chars_gen
                    current_bible["characters"] = _dedup_by_name(combined, key="name")

                if _saved_tipo in (None, "locations") and locs_gen:
                    for loc in locs_gen:
                        loc.setdefault("id", str(uuid.uuid4()))
                        loc.setdefault("notes", "")
                    combined = current_bible.get("locations", []) + locs_gen
                    current_bible["locations"] = _dedup_by_name(combined, key="name")

                if _saved_tipo in (None, "timeline") and tl_gen:
                    for ev in tl_gen:
                        ev.setdefault("id", str(uuid.uuid4()))
                    combined = current_bible.get("timeline", []) + tl_gen
                    current_bible["timeline"] = _dedup_by_name(combined, key="title")

                if _saved_tipo in (None, "mythology") and myth_gen:
                    for myth in myth_gen:
                        myth.setdefault("id", str(uuid.uuid4()))
                        myth.setdefault("notes", "")
                    combined = current_bible.get("mythology", []) + myth_gen
                    current_bible["mythology"] = _dedup_by_name(combined, key="name")

                if _saved_tipo in (None, "notes") and notes_gen:
                    existing_notes = current_bible.get("notes", "")
                    current_bible["notes"] = f"{existing_notes}\n\n{notes_gen}".strip() if existing_notes else notes_gen

                save_bible(current_bible)
                del st.session_state["biblia_gerada"]
                st.session_state.pop("biblia_gerada_tipo", None)

                saved_parts = []
                if chars_gen: saved_parts.append(f"{len(chars_gen)} personagens")
                if locs_gen: saved_parts.append(f"{len(locs_gen)} locais")
                if tl_gen: saved_parts.append(f"{len(tl_gen)} eventos")
                if myth_gen: saved_parts.append(f"{len(myth_gen)} elem. mitológicos")
                if notes_gen: saved_parts.append("notas")

                st.success(f"Bíblia salva: {', '.join(saved_parts) if saved_parts else 'nenhum dado novo'}!")
                st.balloons()
                st.rerun()

# ─── Helpers de detecção de duplicatas ───────────────────────────────────────
import unicodedata

def _normalize_char_name(name: str) -> str:
    """Remove acentos, lowercase, strip prefixos como 'o ', 'a ', 'dr. '."""
    n = unicodedata.normalize("NFD", name.lower().strip())
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")  # remove combining chars
    for prefix in ("o ", "a ", "os ", "as ", "dr. ", "dr ", "sr. ", "sr ", "prof. "):
        if n.startswith(prefix):
            n = n[len(prefix):]
    return n.strip()

def _find_char_duplicates(chars: list) -> list[tuple]:
    """
    Retorna lista de tuplas (idx_a, idx_b, razão) com pares suspeitos de duplicatas.
    Critérios:
      1. Nome normalizado idêntico
      2. Um nome normalizado está contido no outro (e ambos têm ≥ 3 chars)
    """
    pairs = []
    seen_pairs = set()
    norms = [(_normalize_char_name(c.get("name", "")), i) for i, c in enumerate(chars)]

    for i, (ni, idx_i) in enumerate(norms):
        if not ni:
            continue
        for j, (nj, idx_j) in enumerate(norms):
            if j <= i or not nj:
                continue
            key = (min(idx_i, idx_j), max(idx_i, idx_j))
            if key in seen_pairs:
                continue

            if ni == nj:
                pairs.append((idx_i, idx_j, "nome idêntico após normalização"))
                seen_pairs.add(key)
            elif len(ni) >= 4 and len(nj) >= 4 and (ni in nj or nj in ni):
                pairs.append((idx_i, idx_j, "um nome contém o outro"))
                seen_pairs.add(key)

    return pairs

def _merge_two_chars(primary: dict, secondary: dict) -> dict:
    """Mescla secondary em primary: concatena campos distintos."""
    merged = dict(primary)
    for field, val in secondary.items():
        if field in ("id", "name"):
            continue
        ex = merged.get(field, "")
        if isinstance(val, str) and val.strip() and val.strip() not in (ex or ""):
            merged[field] = f"{ex} | {val.strip()}" if ex else val.strip()
    return merged


# ─── Personagens ──────────────────────────────────────────────────────────────
with tab_chars:
    characters = bible.get("characters", [])

    # ── Detecção interativa de duplicatas ─────────────────────────────────────
    if characters:
        dup_col1, dup_col2 = st.columns([2, 3])
        with dup_col1:
            if st.button("🔍 Detectar Duplicatas", use_container_width=True, key="detect_dups"):
                pairs = _find_char_duplicates(characters)
                st.session_state["char_dup_pairs"] = pairs
                st.session_state["char_dup_ignored"] = set()
                if not pairs:
                    st.session_state["char_dup_pairs"] = []
        with dup_col2:
            if st.session_state.get("char_dup_pairs") is not None:
                n = len(st.session_state["char_dup_pairs"])
                if n == 0:
                    st.success("Nenhuma duplicata encontrada.")
                else:
                    st.caption(f"**{n} par(es)** suspeito(s) encontrado(s). Revise abaixo.")

        # ── Painel de duplicatas ──────────────────────────────────────────────
        dup_pairs = st.session_state.get("char_dup_pairs")
        ignored = st.session_state.get("char_dup_ignored", set())

        if dup_pairs:
            active_pairs = [(a, b, r) for (a, b, r) in dup_pairs if (a, b) not in ignored]
            if active_pairs:
                st.divider()
                st.markdown("#### Possíveis Duplicatas")

                chars_updated = False
                for a_idx, b_idx, reason in active_pairs:
                    if a_idx >= len(characters) or b_idx >= len(characters):
                        continue
                    char_a = characters[a_idx]
                    char_b = characters[b_idx]
                    name_a = char_a.get("name", f"Personagem {a_idx+1}")
                    name_b = char_b.get("name", f"Personagem {b_idx+1}")

                    with st.expander(
                        f"**{name_a}** × **{name_b}** — _{reason}_",
                        expanded=True,
                    ):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**{name_a}**")
                            st.caption(f"Papel: {char_a.get('role','—')}")
                            st.caption(f"Aparência: {char_a.get('appearance','—')[:120]}")
                            st.caption(f"Personalidade: {char_a.get('personality','—')[:120]}")
                        with c2:
                            st.markdown(f"**{name_b}**")
                            st.caption(f"Papel: {char_b.get('role','—')}")
                            st.caption(f"Aparência: {char_b.get('appearance','—')[:120]}")
                            st.caption(f"Personalidade: {char_b.get('personality','—')[:120]}")

                        m1, m2, m3 = st.columns(3)
                        with m1:
                            if st.button(
                                f"Mesclar → manter **{name_a}**",
                                key=f"merge_ab_{a_idx}_{b_idx}",
                                use_container_width=True,
                                type="primary",
                            ):
                                merged = _merge_two_chars(char_a, char_b)
                                characters[a_idx] = merged
                                characters.pop(b_idx)
                                bible["characters"] = characters
                                save_bible(bible)
                                st.session_state.pop("char_dup_pairs", None)
                                st.session_state.pop("active_char_id", None)
                                st.rerun()
                        with m2:
                            if st.button(
                                f"Mesclar → manter **{name_b}**",
                                key=f"merge_ba_{a_idx}_{b_idx}",
                                use_container_width=True,
                            ):
                                merged = _merge_two_chars(char_b, char_a)
                                characters[b_idx] = merged
                                characters.pop(a_idx)
                                bible["characters"] = characters
                                save_bible(bible)
                                st.session_state.pop("char_dup_pairs", None)
                                st.session_state.pop("active_char_id", None)
                                st.rerun()
                        with m3:
                            if st.button(
                                "Ignorar este par",
                                key=f"ignore_{a_idx}_{b_idx}",
                                use_container_width=True,
                            ):
                                ignored.add((a_idx, b_idx))
                                st.session_state["char_dup_ignored"] = ignored
                                st.rerun()
                st.divider()

    col_list, col_detail = st.columns([1, 2])

    with col_list:
        st.subheader("Personagens")
        if st.button("+ Novo Personagem", use_container_width=True, type="primary"):
            new_char = {
                "id": str(uuid.uuid4()),
                "name": "Novo Personagem",
                "role": "Secundário",
                "age": "",
                "appearance": "",
                "personality": "",
                "motivation": "",
                "backstory": "",
                "arc": "",
                "notes": "",
            }
            characters.append(new_char)
            bible["characters"] = characters
            save_bible(bible)
            st.session_state["active_char_id"] = new_char["id"]
            st.rerun()

        for char in characters:
            role_badge = {"Protagonista": "🔵", "Antagonista": "🔴", "Secundário": "⚪"}.get(
                char.get("role", ""), "⚪"
            )
            if st.button(
                f"{role_badge} {char['name']}",
                key=f"char_btn_{char['id']}",
                use_container_width=True,
            ):
                st.session_state["active_char_id"] = char["id"]
                st.rerun()

    with col_detail:
        active_char_id = st.session_state.get("active_char_id")
        if not characters:
            st.info("Crie um personagem no painel ao lado.")
        elif not active_char_id or not any(c["id"] == active_char_id for c in characters):
            st.info("Selecione um personagem à esquerda para editar.")
        else:
            char = next(c for c in characters if c["id"] == active_char_id)
            char_idx = next(i for i, c in enumerate(characters) if c["id"] == active_char_id)

            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                char["name"] = st.text_input("Nome", value=char["name"], key=f"cn_{char['id']}")
            with c2:
                char["role"] = st.selectbox(
                    "Papel",
                    ["Protagonista", "Antagonista", "Secundário", "Figurante"],
                    index=["Protagonista", "Antagonista", "Secundário", "Figurante"].index(
                        char.get("role", "Secundário")
                    ),
                    key=f"cr_{char['id']}",
                )
            with c3:
                char["age"] = st.text_input("Idade", value=char.get("age", ""), key=f"ca_{char['id']}")

            char["appearance"] = st.text_area(
                "Aparência física",
                value=char.get("appearance", ""),
                height=80,
                key=f"cap_{char['id']}",
            )
            char["personality"] = st.text_area(
                "Personalidade e traços",
                value=char.get("personality", ""),
                height=80,
                key=f"cper_{char['id']}",
            )
            char["motivation"] = st.text_area(
                "Motivação / Objetivo",
                value=char.get("motivation", ""),
                height=80,
                key=f"cmot_{char['id']}",
            )
            char["backstory"] = st.text_area(
                "Backstory / História anterior",
                value=char.get("backstory", ""),
                height=100,
                key=f"cbs_{char['id']}",
            )
            char["arc"] = st.text_area(
                "Arco do personagem (transformação ao longo do livro)",
                value=char.get("arc", ""),
                height=80,
                key=f"carc_{char['id']}",
            )
            char["notes"] = st.text_area(
                "Notas extras",
                value=char.get("notes", ""),
                height=60,
                key=f"cnotes_{char['id']}",
            )

            col_save, col_del = st.columns([3, 1])
            with col_save:
                if st.button("💾 Salvar Personagem", type="primary", use_container_width=True, key=f"save_char_{char['id']}"):
                    characters[char_idx] = char
                    bible["characters"] = characters
                    save_bible(bible)
                    st.success("Salvo!")
            with col_del:
                if st.button("🗑️ Excluir", use_container_width=True, key=f"del_char_{char['id']}"):
                    bible["characters"] = [c for c in characters if c["id"] != active_char_id]
                    save_bible(bible)
                    st.session_state.pop("active_char_id", None)
                    st.rerun()

# ─── Locais ───────────────────────────────────────────────────────────────────
with tab_locs:
    locations = bible.get("locations", [])

    col_llist, col_ldetail = st.columns([1, 2])

    with col_llist:
        st.subheader("Locais")
        if st.button("+ Novo Local", use_container_width=True, type="primary"):
            new_loc = {
                "id": str(uuid.uuid4()),
                "name": "Novo Local",
                "type": "",
                "description": "",
                "atmosphere": "",
                "significance": "",
                "notes": "",
            }
            locations.append(new_loc)
            bible["locations"] = locations
            save_bible(bible)
            st.session_state["active_loc_id"] = new_loc["id"]
            st.rerun()

        for loc in locations:
            if st.button(f"📍 {loc['name']}", key=f"loc_btn_{loc['id']}", use_container_width=True):
                st.session_state["active_loc_id"] = loc["id"]
                st.rerun()

    with col_ldetail:
        active_loc_id = st.session_state.get("active_loc_id")
        if not locations:
            st.info("Crie um local no painel ao lado.")
        elif not active_loc_id or not any(l["id"] == active_loc_id for l in locations):
            st.info("Selecione um local à esquerda.")
        else:
            loc = next(l for l in locations if l["id"] == active_loc_id)
            loc_idx = next(i for i, l in enumerate(locations) if l["id"] == active_loc_id)

            c1, c2 = st.columns([3, 2])
            with c1:
                loc["name"] = st.text_input("Nome do local", value=loc["name"], key=f"ln_{loc['id']}")
            with c2:
                loc["type"] = st.text_input("Tipo (cidade, floresta, etc.)", value=loc.get("type", ""), key=f"lt_{loc['id']}")

            loc["description"] = st.text_area("Descrição física", value=loc.get("description", ""), height=100, key=f"ld_{loc['id']}")
            loc["atmosphere"] = st.text_area("Atmosfera / clima emocional", value=loc.get("atmosphere", ""), height=80, key=f"la_{loc['id']}")
            loc["significance"] = st.text_area("Importância para a história", value=loc.get("significance", ""), height=80, key=f"ls_{loc['id']}")
            loc["notes"] = st.text_area("Notas", value=loc.get("notes", ""), height=60, key=f"lnotes_{loc['id']}")

            col_save, col_del = st.columns([3, 1])
            with col_save:
                if st.button("💾 Salvar Local", type="primary", use_container_width=True, key=f"save_loc_{loc['id']}"):
                    locations[loc_idx] = loc
                    bible["locations"] = locations
                    save_bible(bible)
                    st.success("Salvo!")
            with col_del:
                if st.button("🗑️ Excluir", use_container_width=True, key=f"del_loc_{loc['id']}"):
                    bible["locations"] = [l for l in locations if l["id"] != active_loc_id]
                    save_bible(bible)
                    st.session_state.pop("active_loc_id", None)
                    st.rerun()

# ─── Linha do Tempo ───────────────────────────────────────────────────────────
with tab_timeline:
    timeline = bible.get("timeline", [])

    st.subheader("Linha do Tempo")

    if st.button("+ Novo Evento", type="primary"):
        new_event = {
            "id": str(uuid.uuid4()),
            "date": "",
            "title": "Novo Evento",
            "description": "",
            "characters": "",
            "importance": "Médio",
        }
        timeline.append(new_event)
        bible["timeline"] = timeline
        save_bible(bible)
        st.rerun()

    if not timeline:
        st.info("Adicione eventos da linha do tempo da história.")
    else:
        for i, event in enumerate(timeline):
            with st.expander(f"📅 {event.get('date', '—')} | {event['title']}", expanded=False):
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    event["date"] = st.text_input("Data / Período", value=event.get("date", ""), key=f"ev_date_{event['id']}")
                with col2:
                    event["title"] = st.text_input("Título do evento", value=event["title"], key=f"ev_title_{event['id']}")
                with col3:
                    event["importance"] = st.selectbox(
                        "Importância",
                        ["Alta", "Médio", "Baixo"],
                        index=["Alta", "Médio", "Baixo"].index(event.get("importance", "Médio")),
                        key=f"ev_imp_{event['id']}",
                    )

                event["description"] = st.text_area("O que acontece:", value=event.get("description", ""), height=80, key=f"ev_desc_{event['id']}")
                # characters pode vir como lista da IA — normaliza para string
                _chars_val = event.get("characters", "")
                if isinstance(_chars_val, list):
                    _chars_val = ", ".join(str(c) for c in _chars_val)
                event["characters"] = st.text_input("Personagens envolvidos:", value=_chars_val, key=f"ev_chars_{event['id']}")

                col_save, col_del = st.columns([3, 1])
                with col_save:
                    if st.button("Salvar evento", key=f"save_ev_{event['id']}"):
                        timeline[i] = event
                        bible["timeline"] = timeline
                        save_bible(bible)
                        st.success("Salvo!")
                with col_del:
                    if st.button("🗑️ Excluir", key=f"del_ev_{event['id']}"):
                        bible["timeline"] = [e for e in timeline if e["id"] != event["id"]]
                        save_bible(bible)
                        st.rerun()

# ─── Mitologia ────────────────────────────────────────────────────────────────
with tab_myth:
    mythology = bible.get("mythology", [])

    _myth_type_opts = ["Divindade", "Mito de Criação", "Lenda", "Profecia", "Religião", "Ritual", "Símbolo", "Outro"]
    _myth_icons = {
        "Divindade": "🌟", "Mito de Criação": "🌍", "Lenda": "📜",
        "Profecia": "🔮", "Religião": "🛕", "Ritual": "🕯️",
        "Símbolo": "☯️", "Outro": "⚡",
    }

    col_mlist, col_mdetail = st.columns([1, 2])

    with col_mlist:
        st.subheader("Mitologia")
        if st.button("+ Novo Elemento", use_container_width=True, type="primary"):
            new_myth = {
                "id": str(uuid.uuid4()),
                "name": "Novo Elemento",
                "type": "Outro",
                "description": "",
                "origin": "",
                "believers": "",
                "significance": "",
                "notes": "",
            }
            mythology.append(new_myth)
            bible["mythology"] = mythology
            save_bible(bible)
            st.session_state["active_myth_id"] = new_myth["id"]
            st.rerun()

        for myth in mythology:
            icon = _myth_icons.get(myth.get("type", "Outro"), "⚡")
            if st.button(
                f"{icon} {myth['name']}",
                key=f"myth_btn_{myth['id']}",
                use_container_width=True,
            ):
                st.session_state["active_myth_id"] = myth["id"]
                st.rerun()

    with col_mdetail:
        active_myth_id = st.session_state.get("active_myth_id")
        if not mythology:
            st.info("Crie um elemento mitológico no painel ao lado.")
        elif not active_myth_id or not any(m["id"] == active_myth_id for m in mythology):
            st.info("Selecione um elemento à esquerda para editar.")
        else:
            myth = next(m for m in mythology if m["id"] == active_myth_id)
            myth_idx = next(i for i, m in enumerate(mythology) if m["id"] == active_myth_id)

            c1, c2 = st.columns([3, 2])
            with c1:
                myth["name"] = st.text_input("Nome", value=myth["name"], key=f"mn_{myth['id']}")
            with c2:
                myth["type"] = st.selectbox(
                    "Tipo",
                    _myth_type_opts,
                    index=_myth_type_opts.index(myth.get("type", "Outro"))
                    if myth.get("type", "Outro") in _myth_type_opts else 7,
                    key=f"mt_{myth['id']}",
                )

            myth["description"] = st.text_area(
                "Descrição detalhada",
                value=myth.get("description", ""),
                height=120,
                key=f"md_{myth['id']}",
            )
            myth["origin"] = st.text_area(
                "Origem no mundo da história",
                value=myth.get("origin", ""),
                height=80,
                key=f"mo_{myth['id']}",
            )
            myth["believers"] = st.text_input(
                "Quem acredita / pratica (povos, personagens, facções)",
                value=myth.get("believers", ""),
                key=f"mb_{myth['id']}",
            )
            myth["significance"] = st.text_area(
                "Importância para a narrativa",
                value=myth.get("significance", ""),
                height=80,
                key=f"ms_{myth['id']}",
            )
            myth["notes"] = st.text_area(
                "Notas extras",
                value=myth.get("notes", ""),
                height=60,
                key=f"mnotes_{myth['id']}",
            )

            col_save, col_del = st.columns([3, 1])
            with col_save:
                if st.button("💾 Salvar", type="primary", use_container_width=True, key=f"save_myth_{myth['id']}"):
                    mythology[myth_idx] = myth
                    bible["mythology"] = mythology
                    save_bible(bible)
                    st.success("Salvo!")
            with col_del:
                if st.button("🗑️ Excluir", use_container_width=True, key=f"del_myth_{myth['id']}"):
                    bible["mythology"] = [m for m in mythology if m["id"] != active_myth_id]
                    save_bible(bible)
                    st.session_state.pop("active_myth_id", None)
                    st.rerun()

# ─── Notas Gerais ─────────────────────────────────────────────────────────────
with tab_notes:
    st.subheader("Notas de World-Building e Apontamentos Gerais")

    notes = st.text_area(
        "Notas livres:",
        value=bible.get("notes", ""),
        height=400,
        placeholder=(
            "Use este espaço para anotar regras do mundo, sistemas de magia, tecnologia, "
            "cultura, referências, inspirações, ideias soltas..."
        ),
        key="bible_notes",
    )

    if st.button("💾 Salvar Notas", type="primary"):
        bible["notes"] = notes
        save_bible(bible)
        st.success("Notas salvas!")
