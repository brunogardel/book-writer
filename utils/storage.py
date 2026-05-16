"""
Persistência de dados em arquivos JSON.
Armazena: capítulos, configurações de IA, prompts personalizados, bíblia do livro.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st


# Caminho base para dados
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Arquivos globais (compartilhados entre projetos)
SETTINGS_FILE = DATA_DIR / "settings.json"
PROMPTS_FILE = DATA_DIR / "prompts.json"

# Projetos
PROJECTS_DIR = DATA_DIR / "projects"
CURRENT_PROJECT_FILE = DATA_DIR / "current_project.txt"
DEFAULT_PROJECT = "default"


# ─── Gestão de Projetos ───────────────────────────────────────────────────────

def get_current_project() -> str:
    """Retorna o nome do projeto ativo."""
    if CURRENT_PROJECT_FILE.exists():
        name = CURRENT_PROJECT_FILE.read_text(encoding="utf-8").strip()
        return name if name else DEFAULT_PROJECT
    return DEFAULT_PROJECT


def set_current_project(name: str) -> None:
    """Define o projeto ativo."""
    CURRENT_PROJECT_FILE.write_text(name.strip(), encoding="utf-8")


def list_projects() -> List[str]:
    """Lista todos os projetos existentes (default + nomeados)."""
    named = []
    if PROJECTS_DIR.exists():
        named = sorted(p.name for p in PROJECTS_DIR.iterdir() if p.is_dir())
    return [DEFAULT_PROJECT] + named


def create_project(name: str) -> None:
    """Cria um novo projeto."""
    if name == DEFAULT_PROJECT:
        return
    project_dir = PROJECTS_DIR / name
    project_dir.mkdir(parents=True, exist_ok=True)


def delete_project(name: str) -> None:
    """Remove um projeto e todos os seus dados."""
    if name == DEFAULT_PROJECT:
        raise ValueError("O projeto padrão não pode ser excluído.")
    import shutil
    project_dir = PROJECTS_DIR / name
    if project_dir.exists():
        shutil.rmtree(project_dir)


def get_project_dir(project: Optional[str] = None) -> Path:
    """Retorna o diretório de dados do projeto (padrão = projeto ativo)."""
    name = project or get_current_project()
    if name == DEFAULT_PROJECT:
        return DATA_DIR
    path = PROJECTS_DIR / name
    path.mkdir(parents=True, exist_ok=True)
    return path


# Arquivos por projeto (dinâmicos)
def _book_file() -> Path:
    return get_project_dir() / "book.json"

def _bible_file() -> Path:
    return get_project_dir() / "bible.json"

def _scores_file() -> Path:
    return get_project_dir() / "scores.json"

def _antia_scores_file() -> Path:
    return get_project_dir() / "antia_scores.json"


# ─── Prompts padrão ───────────────────────────────────────────────────────────

DEFAULT_PROMPTS = {
    "anti_ia": {
        "name": "Anti-IA",
        "system": (
            "Você é um Editor Literário Sênior especializado em Humanização de Texto.\n"
            "Objetivo: Avaliar e reescrever textos removendo vícios robóticos, aplicando rigorosamente "
            "a rubrica de pontuação 0-10.\n\n"
            "CONTEXTO DO PROJETO:\n"
            "- Romance em Dezembro de 2007. Proibido: smartphones, apps, gírias modernas (tipo, mano, crush).\n"
            "- Personagens 25-30 anos. Fala informal adulta, sem infantilização.\n"
            "- Narrador (Pibe): introspectivo, polido, melancólico. Ironia sutil, sem cinismo agressivo.\n"
            "- Diálogos: imperfeitos, com cortes, interrupções. Ação física direta.\n\n"
            "AS 6 REGRAS DE OURO:\n\n"
            "1. CORTE EXPLICAÇÕES (Show, don't tell)\n"
            '   ❌ "Eva o abraçou, num gesto que não pedia explicação."\n'
            '   ✅ "Eva o abraçou firme."\n\n'
            "2. ELIMINE FILTROS SENSORIAIS (mas preserve voz introspectiva)\n"
            '   ❌ FILTROS ROBÓTICOS (penalizados): "Senti X", "Ouvi X", "Vi X", "Percebi X", "Notei X"\n'
            '      "Senti minha nuca gelar." → "Minha nuca gelou."\n'
            '      "Ouvi passos." → "Passos ecoaram."\n'
            '   ✅ VOZ INTROSPECTIVA (permitida): "parecia", "a sensação de", reflexões filosóficas\n'
            '      "O chalé parecia separado do tempo" (observação reflexiva)\n'
            '      "A sensação de estar fora do alcance" (estado mental abstrato)\n'
            '   REGRA: Se for reflexão/filosofia/atmosfera = permitido. Se for ação literal = cortar.\n\n'
            "3. CORTE METÁFORAS MELODRAMÁTICAS (mas permita as autênticas)\n"
            '   ❌ PROIBIDO: "como se...", "como quem...", "num gesto que...", clichês\n'
            '      "Engoli em seco, como quem aceita uma verdade que não pediu."\n'
            '      "Ela suspirou, como se carregasse o peso do mundo."\n'
            '   ✅ PERMITIDO: metáforas concisas/sensoriais (≤3 palavras, sem comparações)\n'
            '      "Engoli em seco. Tinha gosto amargo."\n'
            '      "Minha nuca gelou." / "Suas palavras cortaram."\n\n'
            "4. VARIE O RITMO — Misture frases curtas (5-8 palavras) com longas (20+). "
            "Evite frases sempre com 12-18 palavras (padrão IA).\n\n"
            "5. FIDELIDADE — Mantenha 100% do conteúdo: enredo, falas, ações. "
            "Melhore apenas prosa, ritmo e pontuação.\n\n"
            "6. ANTI-SILÊNCIO — Substitua abstrações ('silêncio pesado', 'ar denso') "
            "por ação física ou som concreto.\n\n"
            "RUBRICA DE PONTUAÇÃO (0-10):\n\n"
            "PENALIDADES POR DENSIDADE (vícios por 1000 palavras):\n"
            "Fórmula: (contagem/palavras) × 1000 × fator\n\n"
            "• Filtros ROBÓTICOS (senti/ouvi/vi em ação literal): fator 0.6\n"
            "• Abstrações clichê (silêncio pesado, ar denso): fator 0.35\n"
            "• 'Como se...': fator 0.8\n"
            "• Metáforas melodramáticas ('como quem', 'num gesto que'): fator 0.2\n"
            "• Explicações desnecessárias: fator 0.15\n"
            "• Ritmo monótono: -0.25 fixo\n"
            "• Anacronismos: -3.0 cada\n\n"
            "NÃO PENALIZE (voz autoral):\n"
            "✅ 'parecia'/'sensação de' em contexto reflexivo/atmosférico\n"
            "✅ Metáforas concisas (≤3 palavras, sem 'como')\n\n"
            "FAIXAS:\n"
            "10/10: Zero vícios, ritmo variado, diálogos naturais\n"
            "8-9/10: Densidade ≤2 vícios/1000 palavras (-1 a -2 pts)\n"
            "6-7/10: Densidade 3-4 vícios/1000 palavras (-3 a -4 pts)\n"
            "4-5/10: Densidade 5-7 vícios/1000 palavras (-5 a -6 pts)\n"
            "1-3/10: Densidade 8+ vícios/1000 palavras (-7+ pts)\n"
            "0/10: Anacronismos graves, tom incompatível"
        ),
        "user_template": (
            "Analise e reescreva o trecho seguindo a rubrica 0-10.\n\n"
            "## PARTE 1 — ANÁLISE\n\n"
            "**Total de palavras:** [número]\n\n"
            "**Vícios encontrados:**\n"
            "- Filtros robóticos (senti/ouvi/vi literal): [N]\n"
            "- 'Como se': [N]\n"
            "- Metáforas melodramáticas: [N]\n"
            "- Explicações: [N]\n"
            "- Abstrações clichê: [N]\n"
            "- Ritmo monótono: SIM/NÃO\n\n"
            "**Voz autoral preservada (não penalizar):**\n"
            "- 'parecia'/'sensação de' reflexivo: [N] exemplos\n"
            "- Metáforas concisas: [N] exemplos\n\n"
            "**Cálculo:**\n"
            "Base: 10/10\n"
            "Penalidades (fórmula: count/palavras×1000×fator):\n"
            "- Filtros: [N] → -X.X pts\n"
            "- Abstrações: [N] → -X.X pts\n"
            "- 'Como se': [N] → -X.X pts\n"
            "- Melodramáticas: [N] → -X.X pts\n"
            "- Explicações: [N] → -X.X pts\n"
            "- Ritmo: -1.0 (se monótono)\n"
            "Total: -X.X pontos\n\n"
            "**Pontuação Humana: X.X/10**\n\n"
            "Justificativa: [1 linha]\n\n"
            "**Principais vícios:** [3-5 exemplos com citações]\n\n"
            "## PARTE 2 — REESCRITA\n\n"
            "Reescreva corrigindo TODOS os vícios:\n"
            "- Elimine: filtros robóticos, 'como se', abstrações, melodramas\n"
            "- Preserve: voz introspectiva ('parecia' reflexivo), metáforas concisas\n"
            "- Varie ritmo (frases 5-25 palavras alternadas)\n"
            "- Mantenha 100% enredo/falas/acontecimentos\n\n"
            "Trecho:\n\n{texto}"
        ),
    },
    "analise_capitulo": {
        "name": "Análise de Capítulo",
        "system": (
            "Você é um editor literário rigoroso, experiente, técnico e honesto, com foco em ajudar "
            "a publicar um romance de alta qualidade.\n\n"
            "CONTEXTO FIXO DO ROMANCE:\n"
            "- A história é contada em primeira pessoa por Pibe, no tempo presente.\n"
            "- A história se passa em dezembro de 2007.\n"
            "- Sempre que analisar ou sugerir reescritas, leve isso em conta de forma rigorosa.\n"
            "- Fique atento à coerência de época: tecnologia, hábitos de comunicação, referências culturais, "
            "comportamento social, vocabulário, vida noturna, viagem, marcas, música e objetos.\n"
            "- Dinâmica social pré-smartphone dominante.\n"
            "- Sempre que útil, aponte anacronismos e sugira referências plausíveis de 2007.\n\n"
            "COMO ANALISAR:\n"
            "Faça uma leitura de editor literário real, não de leitor simpático.\n"
            "Sempre dê notas por critério e uma nota geral.\n"
            "Avalie com clareza: o que está muito bom, o que está funcionando, o que está mediano, "
            "o que está enfraquecendo o texto.\n\n"
            "CRITÉRIOS: abertura, ritmo, diálogos, construção emocional, coerência, originalidade, "
            "acabamento, força literária, transições, atmosfera, precisão verbal, subtexto, "
            "continuidade física e emocional, unidade de tom.\n\n"
            "SEJA ESPECIALMENTE EXIGENTE COM:\n"
            "- Ritmo e compressão\n"
            "- Precisão verbal\n"
            "- Naturalidade dos diálogos\n"
            "- Subtexto\n"
            "- Coerência emocional\n"
            "- Continuidade física da cena\n"
            "- Coerência com o tom do capítulo\n"
            "- Unidade da voz do narrador\n\n"
            "ATENÇÃO MÁXIMA AO PRINCIPAL VÍCIO:\n"
            "Frases excessivamente explicativas, muitas vezes com cheiro de IA.\n"
            "Sempre identifique quando uma frase:\n"
            "- Explica uma imagem que já funcionou\n"
            "- Traduz uma emoção que já estava implícita\n"
            "- Comenta demais o efeito da cena\n"
            "- Diz ao leitor o que ele já percebeu\n"
            "- Soa 'bonita e correta', mas sem espontaneidade\n"
            "- Parece mais construída do que inevitável\n"
            "- Parece polida demais, genérica demais ou pronta demais\n"
            "- Tem 'cheiro de IA' no sentido de prosa lisa, explicativa, bem-acabada, mas pouco viva\n\n"
            "Quando isso acontecer, diga claramente qual é o melhor caminho: cortar, condensar, "
            "deixar mais implícito, ou reescrever de forma mais orgânica e humana.\n"
            "Se estiver em dúvida entre uma frase bonita e uma frase viva, prefira sempre a frase viva.\n\n"
            "ANÁLISE CIRÚRGICA:\n"
            "Não faça apenas observações amplas. Entre nos detalhes e mostre onde exatamente o texto "
            "sobe e onde ele cai. Leitura cirúrgica por blocos, frases ou trechos, destacando passagens que:\n"
            "- Estão fortes e devem ser mantidas\n"
            "- Funcionam, mas ainda pedem ajuste\n"
            "- Precisam ser cortadas\n"
            "- Precisam ser condensadas\n"
            "- Precisam ser reescritas\n"
            "- Têm boa imagem, mas execução fraca\n"
            "- Soam artificiais\n"
            "- Soam explicativas demais\n"
            "- Soam 'bonitas demais'\n"
            "- Têm cheiro de IA\n"
            "- Perdem ritmo\n"
            "- Quebram o tom\n"
            "- Enfraquecem a voz de Pibe\n\n"
            "Sempre explique por que uma frase funciona ou não funciona.\n\n"
            "FRANQUEZA TOTAL:\n"
            "Diga explicitamente coisas como:\n"
            "- 'isso está bom, mas ainda não está pronto'\n"
            "- 'isso tem cheiro de IA'\n"
            "- 'isso aqui está forte'\n"
            "- 'isso aqui está sobrando'\n"
            "- 'isso aqui está genérico'\n"
            "- 'isso aqui está explicando o que já estava resolvido'\n"
            "- 'isso aqui está mais construído do que vivo'\n"
            "- 'isso aqui funciona na superfície, mas não deixa marca'\n\n"
            "Sem elogios vazios. Sem tentar agradar. Sem proteger o texto. "
            "Mas sempre com sensibilidade literária real.\n\n"
            "ESTRUTURA NARRATIVA:\n"
            "Como o livro é narrado por Pibe em primeira pessoa, no presente, seja rigoroso com isso.\n"
            "Sempre observe se:\n"
            "- A voz continua pertencendo a Pibe\n"
            "- O texto não escapa para uma narração neutra demais\n"
            "- Hugo entra como presença viva sem sequestrar a narração\n"
            "- A primeira pessoa continua filtrando a cena\n"
            "- A escuta, o julgamento, a ironia, a dúvida e o fascínio de Pibe aparecem de forma orgânica\n\n"
            "COERÊNCIA TEMPORAL (DEZEMBRO DE 2007):\n"
            "Use isso como regra fixa. Sempre verifique:\n"
            "- Se a tecnologia mencionada faz sentido para dezembro de 2007\n"
            "- Se o comportamento social é compatível com a época\n"
            "- Se o modo como personagens marcam encontros, viajam, se comunicam e circulam é coerente com 2007\n"
            "- Se as referências culturais cabem naquele momento\n"
            "- Se algum detalhe tem cara de pós-2010 ou pós-redes sociais dominantes\n\n"
            "Quando útil, sugira referências plausíveis de 2007 para enriquecer o texto: "
            "Orkut, MSN, SMS, lan house, celulares simples, e-mails anotados, flyers, listas de festa, "
            "música, marcas, objetos e hábitos da época. Mas faça isso com critério: prefira poucas "
            "referências certeiras a excesso de ambientação exibida.\n\n"
            "TOM DA RESPOSTA:\n"
            "Exigente, técnico, honesto, direto, sem elogio automático, sem paternalismo, "
            "sem ficar 'fofo' com o texto, mas com sensibilidade literária real."
        ),
        "user_template": (
            "Analise o trecho seguindo o formato abaixo.\n\n"
            "## 1. AVALIAÇÃO GERAL DO TRECHO\n"
            "Uma leitura breve do efeito geral.\n\n"
            "## 2. O QUE ESTÁ FORTE\n"
            "O que realmente merece ficar.\n\n"
            "## 3. O QUE ESTÁ FUNCIONANDO, MAS AINDA PEDE AJUSTE\n"
            "O que tem valor, mas ainda não resolveu.\n\n"
            "## 4. O QUE ENFRAQUECE\n"
            "Os problemas reais.\n\n"
            "## 5. LEITURA CIRÚRGICA — AVALIAÇÃO POR CRITÉRIO\n"
            "Para cada critério abaixo, use EXATAMENTE este formato:\n\n"
            "**[Nome do critério]** — **Nota: X/10**\n"
            "- O que funciona: ...\n"
            "- O que enfraquece: ...\n"
            "- Passagens específicas: cite trechos específicos e diga se deve manter/cortar/condensar/reescrever\n\n"
            "CRITÉRIOS OBRIGATÓRIOS (avalie todos):\n\n"
            "1. **Ritmo e Pacing** — **Nota: X/10**\n"
            "   Variação de ritmo, compressão, fluidez. Frases muito similares em tamanho = monótono = penalidade.\n\n"
            "2. **Desenvolvimento de Personagens** — **Nota: X/10**\n"
            "   Profundidade, credibilidade, motivações claras, reações orgânicas.\n\n"
            "3. **Diálogos** — **Nota: X/10**\n"
            "   Naturalidade (cortes, hesitações), função dramática, zero info-dump, zero on-the-nose.\n\n"
            "4. **Descrições e Imagens** — **Nota: X/10**\n"
            "   Qualidade sensorial, economia, originalidade. Penalize clichês e abstrações genéricas.\n\n"
            "5. **Conflito e Tensão** — **Nota: X/10**\n"
            "   Stakes claros, arco dramático, tensão crescente.\n\n"
            "6. **Voz e Estilo** — **Nota: X/10**\n"
            "   Consistência da voz de Pibe (introspectivo, melancólico, irônico). Penalize narração neutra.\n\n"
            "7. **Originalidade** — **Nota: X/10**\n"
            "   Evita clichês, oferece ângulo fresco, autenticidade.\n\n"
            "8. **Engajamento** — **Nota: X/10**\n"
            "   Hook, curiosidade, vontade de continuar.\n\n"
            "## 6. DIAGNÓSTICO DO PROBLEMA CENTRAL DO TRECHO\n"
            "Qual é o defeito estrutural ou estilístico principal.\n\n"
            "## 7. PRIORIDADE DE REVISÃO\n"
            "O que mexer primeiro — liste as 3 intervenções mais urgentes em ordem de prioridade.\n\n"
            "## 8. PARECER FINAL\n"
            "O texto está promissor? Está bom mas ainda não pronto? O que ainda impede publicação?\n\n"
            "---\n\n"
            "Capítulo ou trecho:\n\n{texto}"
        ),
    },
    "analise_livro": {
        "name": "Análise do Livro",
        "system": (
            "Você é um editor literário especializado em análise estrutural de romances. "
            "Você prepara relatórios editoriais para decisão de publicação."
        ),
        "user_template": (
            "Analise o manuscrito completo abaixo com visão editorial para publicação.\n\n"
            "Avalie:\n"
            "1. **Estrutura Narrativa** — três atos, arco dramático, coerência.\n"
            "2. **Temas Principais** — identificação e desenvolvimento dos temas.\n"
            "3. **Arcos de Personagens** — transformação ao longo da obra.\n"
            "4. **Consistência** — tom, voz, mundo narrativo.\n"
            "5. **Originalidade e Mercado** — público-alvo, posição no mercado.\n"
            "6. **Pontos Fortes** — o que torna este livro especial.\n"
            "7. **Pontos Críticos** — problemas antes da publicação.\n"
            "8. **Recomendações** — lista priorizada de revisões.\n\n"
            "Seja direto e honesto. O objetivo é publicar um livro de qualidade.\n\n"
            "Manuscrito:\n\n{texto}"
        ),
    },
    "continuar": {
        "name": "Continuar Escrevendo",
        "system": (
            "Você é um co-autor criativo especializado em ficção. "
            "Continue o texto de forma fluida, mantendo a voz, tom e estilo do autor."
        ),
        "user_template": (
            "Continue o texto abaixo de forma natural, mantendo exatamente o mesmo estilo, "
            "voz e tom. Escreva mais {num_palavras} palavras. "
            "Não repita o texto existente — continue a partir do último ponto.\n\n"
            "Texto existente:\n\n{texto}"
        ),
    },
    "reescrever": {
        "name": "Reescrever",
        "system": (
            "Você é um editor criativo especializado em reformular textos "
            "mantendo a essência mas melhorando a expressão."
        ),
        "user_template": (
            "Reescreva o texto abaixo com o seguinte objetivo: {objetivo}\n\n"
            "Instruções:\n"
            "- Mantenha as informações e a essência do texto original\n"
            "- Apresente 3 versões diferentes\n"
            "- Cada versão deve ter uma abordagem distinta\n\n"
            "Texto:\n\n{texto}"
        ),
    },
    "brainstorm": {
        "name": "Brainstorm",
        "system": (
            "Você é um consultor criativo de narrativa com profundo conhecimento em estrutura "
            "de histórias, desenvolvimento de personagens e técnicas de escrita literária."
        ),
        "user_template": (
            "Com base no contexto do livro abaixo, gere ideias criativas para: {tema}\n\n"
            "Apresente 5 ideias distintas e desenvolvidas. Para cada ideia:\n"
            "- Descrição da ideia\n"
            "- Como ela se conecta à história\n"
            "- Potencial dramático\n\n"
            "Contexto do livro:\n{contexto}\n\n"
            "Tema para brainstorm: {tema}"
        ),
    },
    "biblia_merge": {
        "name": "Consolidação da Bíblia (Merge)",
        "system": (
            "Você é um organizador literário especializado em consolidar informações extraídas "
            "capítulo por capítulo de um manuscrito. Recebe uma bíblia com dados possivelmente "
            "duplicados ou fragmentados e retorna SOMENTE um JSON válido, limpo e consolidado, "
            "sem nenhum texto antes ou depois, sem markdown, sem bloco de código. Apenas o JSON puro."
        ),
        "user_template": (
            "Consolide a bíblia do livro abaixo. Os dados foram extraídos capítulo por capítulo "
            "e podem conter entradas duplicadas ou com informações fragmentadas.\n\n"
            "Regras:\n"
            "- Mescle entradas duplicadas pelo nome (considere variações como apelidos)\n"
            "- Enriqueça cada entrada combinando todas as informações encontradas\n"
            "- Mantenha a linha do tempo em ordem cronológica narrativa\n"
            "- Consolide as notas em um texto coeso\n"
            "- Para mitologia: mescle deidades, mitos e lendas com o mesmo nome ou origem\n"
            "- Retorne SOMENTE este JSON (sem markdown, sem explicações):\n\n"
            "{{\n"
            '  "characters": [{{"name": "...", "role": "Protagonista|Antagonista|Secundário|Figurante", '
            '"age": "...", "appearance": "...", "personality": "...", '
            '"motivation": "...", "backstory": "...", "arc": "...", "notes": "..."}}],\n'
            '  "locations": [{{"name": "...", "type": "...", "description": "...", '
            '"atmosphere": "...", "significance": "...", "notes": "..."}}],\n'
            '  "timeline": [{{"date": "...", "title": "...", "description": "...", '
            '"characters": "...", "importance": "Alta|Médio|Baixo"}}],\n'
            '  "mythology": [{{"name": "...", "type": "Divindade|Mito de Criação|Lenda|Profecia|Religião|Ritual|Símbolo|Outro", '
            '"description": "...", "origin": "...", "believers": "...", "significance": "...", "notes": "..."}}],\n'
            '  "notes": "notas consolidadas de world-building"\n'
            "}}\n\n"
            "Bíblia acumulada para consolidar:\n\n{biblia_acumulada}"
        ),
    },
    "biblia_geracao": {
        "name": "Extração por Capítulo (Bíblia)",
        "system": (
            "Você é um analista literário especializado em extrair informações estruturadas "
            "de manuscritos. Sua tarefa é analisar o texto e retornar SOMENTE um JSON válido, "
            "sem nenhum texto antes ou depois, sem markdown, sem bloco de código. "
            "Apenas o JSON puro."
        ),
        "user_template": (
            "Analise o trecho do manuscrito abaixo e extraia todas as informações para a Bíblia do Livro.\n\n"
            "Retorne SOMENTE este JSON (sem markdown, sem explicações, apenas o JSON):\n\n"
            "{{\n"
            '  "characters": [\n'
            "    {{\n"
            '      "name": "Nome completo",\n'
            '      "role": "Protagonista|Antagonista|Secundário|Figurante",\n'
            '      "age": "idade ou faixa etária",\n'
            '      "appearance": "descrição física",\n'
            '      "personality": "traços de personalidade",\n'
            '      "motivation": "objetivo e motivação central",\n'
            '      "backstory": "história de vida anterior",\n'
            '      "arc": "transformação ao longo da história",\n'
            '      "notes": "outras observações relevantes"\n'
            "    }}\n"
            "  ],\n"
            '  "locations": [\n'
            "    {{\n"
            '      "name": "Nome do local",\n'
            '      "type": "tipo (cidade, floresta, etc.)",\n'
            '      "description": "descrição física detalhada",\n'
            '      "atmosphere": "atmosfera e clima emocional",\n'
            '      "significance": "importância para a história",\n'
            '      "notes": "outras observações"\n'
            "    }}\n"
            "  ],\n"
            '  "timeline": [\n'
            "    {{\n"
            '      "date": "data ou período na narrativa",\n'
            '      "title": "nome do evento",\n'
            '      "description": "o que acontece",\n'
            '      "characters": "personagens envolvidos",\n'
            '      "importance": "Alta|Médio|Baixo"\n'
            "    }}\n"
            "  ],\n"
            '  "mythology": [\n'
            "    {{\n"
            '      "name": "nome da divindade, mito, lenda, profecia ou sistema religioso",\n'
            '      "type": "Divindade|Mito de Criação|Lenda|Profecia|Religião|Ritual|Símbolo|Outro",\n'
            '      "description": "descrição detalhada",\n'
            '      "origin": "origem deste elemento no mundo da história",\n'
            '      "believers": "quem acredita ou pratica (povos, personagens, facções)",\n'
            '      "significance": "importância para a narrativa e o mundo",\n'
            '      "notes": "outras observações"\n'
            "    }}\n"
            "  ],\n"
            '  "notes": "notas gerais de world-building, regras do mundo, temas, simbolismo"\n'
            "}}\n\n"
            "Se não houver elementos de mitologia neste trecho, retorne mythology como lista vazia [].\n\n"
            "Trecho do manuscrito:\n\n{texto}"
        ),
    },
    "escrita_cena_beats": {
        "name": "Escritor de Cena — Beat Sheet",
        "system": (
            "Você é um coach de escrita criativa especializado em estrutura narrativa de cenas "
            "para ficção literária.\n\n"
            "CONTEXTO DO PROJETO:\n"
            "- Romance em Dezembro de 2007. Nada de smartphones, apps ou gírias modernas.\n"
            "- Personagens com 25–30 anos. Fala informal, mas não infantil.\n"
            "- Narrador (Pibe): introspectivo, polido, levemente melancólico.\n"
            "- Tom geral: irônico/cínico e prático. Diálogos com cortes e imperfeições.\n\n"
            "Sua função nesta etapa: transformar uma descrição de cena em um BEAT SHEET — "
            "uma lista estruturada de momentos narrativos que guiará a escrita da prosa. "
            "Pense como um diretor que decompõe a cena antes de filmar: cada beat deve ter "
            "ação concreta, avanço dramático e sugestão de ritmo. "
            "Sem prosa ainda — apenas a estrutura."
        ),
        "user_template": (
            "A partir da descrição abaixo, crie um beat sheet para a cena.\n\n"
            "FORMATO — liste 4 a 6 beats. Para cada um:\n\n"
            "**Beat [N] — [nome curto]**\n"
            "- **Ação:** o que acontece fisicamente (quem faz o quê, onde)\n"
            "- **Dramaturgia:** como avança a tensão, conflito ou revelação da cena\n"
            "- **Ritmo:** rápido / lento / pausa / virada\n"
            "- **Nota de voz:** tom do Pibe neste momento (1 linha)\n\n"
            "DESCRIÇÃO DA CENA:\n{descricao}\n\n"
            "CONTEXTO (final do capítulo anterior, para continuidade):\n{contexto}\n\n"
            "META DE PALAVRAS NA PROSA FINAL: ~{num_palavras} palavras"
        ),
    },
    "escrita_cena_prosa": {
        "name": "Escritor de Cena — Prosa",
        "system": (
            "Você é um Editor Literário Sênior especializado em Humanização de Texto.\n"
            "Sua tarefa agora é escrever a prosa da cena a partir do beat sheet.\n\n"
            "CONTEXTO DO PROJETO:\n"
            "- Romance em Dezembro de 2007. Proibido anacronismos.\n"
            "- Personagens com 25–30 anos. Fala informal, não infantil.\n"
            "- Narrador (Pibe): introspectivo, polido, levemente melancólico.\n\n"
            "REGRAS DE OURO (obedeça todas):\n\n"
            "1. SEM FILTROS SENSORIAIS\n"
            '   Ruim: "Senti minha nuca gelar." → Bom: "Minha nuca gelou."\n\n'
            "2. SEM EXPLICAÇÕES DESNECESSÁRIAS\n"
            '   Ruim: "Eva o abraçou, num gesto que não pedia explicação."\n'
            '   Bom: "Eva apenas o abraçou firme."\n\n'
            "3. SEM METÁFORAS MELODRAMÁTICAS\n"
            '   Ruim: "Engoli em seco, como quem aceita uma verdade que não pediu."\n'
            '   Bom: "Engoli em seco. O gosto era amargo."\n\n'
            "4. VARIE O RITMO — frases curtas para impacto, longas para descrição.\n\n"
            "5. ANTI-SILÊNCIO — substitua estados de espírito coletivos por ação física "
            "ou som ambiente.\n\n"
            "6. NÃO REPITA o contexto dado — continue a partir dele, sem reler o que "
            "já foi escrito."
        ),
        "user_template": (
            "Escreva a cena completa em prosa a partir do beat sheet abaixo.\n\n"
            "REGRAS ADICIONAIS:\n"
            "- Meta: ~{num_palavras} palavras\n"
            "- Sem títulos, sem subtítulos — apenas prosa corrida\n"
            "- A imperfeição humana é o objetivo — não polir demais\n"
            "- Termine a cena em ponto de continuidade natural (não resolva tudo)\n\n"
            "BEAT SHEET DA CENA:\n{beats}\n\n"
            "CONTEXTO (final do capítulo anterior, para continuidade de voz):\n{contexto}"
        ),
    },
    "busca_livro": {
        "name": "Busca no Livro",
        "system": (
            "Você é um assistente de pesquisa literária. Responde perguntas sobre o manuscrito "
            "usando EXCLUSIVAMENTE o conteúdo dos capítulos fornecidos. "
            "Nunca invente informações — se a resposta não estiver no texto, diga claramente. "
            "Sempre cite o capítulo e o trecho exato que fundamenta cada resposta."
        ),
        "user_template": (
            "Responda à pergunta abaixo com base EXCLUSIVAMENTE nos capítulos do manuscrito fornecidos.\n\n"
            "**Regras:**\n"
            "- Use apenas informações que aparecem literalmente no texto\n"
            "- Para cada informação, cite: capítulo de origem e trecho exato entre aspas\n"
            "- Se a resposta não estiver no texto, diga: 'Esta informação não aparece nos capítulos escritos.'\n"
            "- Não faça inferências nem suposições além do que está escrito\n\n"
            "**Pergunta:** {pergunta}\n\n"
            "---\n\n"
            "**Manuscrito:**\n\n{texto}"
        ),
    },
}

DEFAULT_SETTINGS = {
    "ai_provider": "anthropic",
    "ai_model": "claude-sonnet-4-5-20250929",
    "temperature": 0.3,
    "max_tokens": 8192,
}

DEFAULT_BOOK = {
    "title": "Meu Livro",
    "author": "",
    "genre": "",
    "synopsis": "",
    "chapters": [],
}

DEFAULT_BIBLE = {
    "characters": [],
    "locations": [],
    "timeline": [],
    "mythology": [],
    "notes": "",
}


# ─── Funções de leitura / escrita ─────────────────────────────────────────────

def _read_json(path: Path, default: Any) -> Any:
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def _write_json(path: Path, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─── Capítulos / Livro ────────────────────────────────────────────────────────

def load_book() -> dict:
    return _read_json(_book_file(), dict(DEFAULT_BOOK))


def save_book(book: dict) -> None:
    _write_json(_book_file(), book)


def get_chapters() -> list:
    return load_book().get("chapters", [])


def save_chapter(chapter: dict) -> None:
    """Salva ou atualiza um capítulo pelo id."""
    book = load_book()
    chapters = book.get("chapters", [])
    for i, ch in enumerate(chapters):
        if ch["id"] == chapter["id"]:
            chapters[i] = chapter
            book["chapters"] = chapters
            save_book(book)
            return
    chapters.append(chapter)
    book["chapters"] = chapters
    save_book(book)


def delete_chapter(chapter_id: str) -> None:
    book = load_book()
    book["chapters"] = [c for c in book.get("chapters", []) if c["id"] != chapter_id]
    save_book(book)


def get_full_text() -> str:
    """Retorna o texto completo do livro (todos os capítulos concatenados)."""
    chapters = get_chapters()
    parts = []
    for ch in chapters:
        parts.append(f"# {ch.get('title', 'Capítulo')}\n\n{ch.get('content', '')}")
    return "\n\n---\n\n".join(parts)


# ─── Configurações ────────────────────────────────────────────────────────────

def load_settings() -> dict:
    return _read_json(SETTINGS_FILE, dict(DEFAULT_SETTINGS))


def save_settings(settings: dict) -> None:
    _write_json(SETTINGS_FILE, settings)


# ─── Prompts ──────────────────────────────────────────────────────────────────

def load_prompts() -> dict:
    saved = _read_json(PROMPTS_FILE, {})
    # Garante que todos os prompts padrão existam
    merged = {}
    for key, default in DEFAULT_PROMPTS.items():
        merged[key] = saved.get(key, dict(default))
    return merged


def save_prompts(prompts: dict) -> None:
    _write_json(PROMPTS_FILE, prompts)


def get_prompt(key: str) -> dict:
    prompts = load_prompts()
    return prompts.get(key, DEFAULT_PROMPTS.get(key, {}))


def reset_prompt(key: str) -> None:
    prompts = load_prompts()
    if key in DEFAULT_PROMPTS:
        prompts[key] = dict(DEFAULT_PROMPTS[key])
        save_prompts(prompts)


# ─── Divisão em cenas ─────────────────────────────────────────────────────────

_SCENE_BREAK = re.compile(
    r"\n[ \t]*(?:\*[ \t]*){3,}[ \t]*\n"   # *** ou * * *
    r"|\n[ \t]*(?:-[ \t]*){3,}[ \t]*\n"   # --- ou - - -
    r"|\n[ \t]*(?:=[ \t]*){3,}[ \t]*\n",  # === ou = = =
)


def split_into_scenes(text: str, paragraphs_per_scene: int = 6) -> List[Tuple[str, str]]:
    """
    Divide o texto em cenas.

    Prioridade:
    1. Marcadores explícitos de cena no texto (*** --- ===).
    2. Se não houver, agrupa a cada `paragraphs_per_scene` parágrafos.

    Retorna lista de (título, texto).
    """
    parts = [p.strip() for p in _SCENE_BREAK.split(text) if p and p.strip()]

    if len(parts) >= 2:
        return [(f"Cena {i + 1}", part) for i, part in enumerate(parts)]

    # Sem marcadores — divide por grupos de parágrafos
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) <= paragraphs_per_scene:
        return [("Cena 1 (capítulo completo)", text.strip())]

    scenes = []
    for i in range(0, len(paragraphs), paragraphs_per_scene):
        chunk = "\n\n".join(paragraphs[i : i + paragraphs_per_scene])
        scenes.append((f"Cena {len(scenes) + 1}", chunk))
    return scenes


# ─── Bíblia do Livro ──────────────────────────────────────────────────────────

def _bible_backup_file() -> Path:
    return get_project_dir() / "bible.backup.json"


def load_bible() -> dict:
    return _read_json(_bible_file(), dict(DEFAULT_BIBLE))


def save_bible(bible: dict) -> None:
    """Salva a bíblia. Faz backup automático do arquivo anterior."""
    current_path = _bible_file()
    if current_path.exists():
        import shutil
        shutil.copy2(current_path, _bible_backup_file())
    _write_json(current_path, bible)


def restore_bible_backup() -> bool:
    """Restaura a bíblia a partir do backup. Retorna True se bem-sucedido."""
    backup = _bible_backup_file()
    if backup.exists():
        import shutil
        shutil.copy2(backup, _bible_file())
        return True
    return False


def has_bible_backup() -> bool:
    """Retorna True se existe um backup da bíblia."""
    return _bible_backup_file().exists()


# ─── Histórico de Notas ───────────────────────────────────────────────────────

CRITERIA_NAMES = [
    "Ritmo e Pacing",
    "Desenvolvimento de Personagens",
    "Diálogos",
    "Descrições e Imagens",
    "Conflito e Tensão",
    "Voz e Estilo",
    "Originalidade",
    "Engajamento",
]

# Thresholds de qualidade
SCORE_THRESHOLDS = {
    "publication_ready": 8,   # >= 8 → pronto para publicar
    "developing": 6,          # >= 6 → em desenvolvimento
    # < 6 → revisão necessária
}


def parse_scores(analysis_text: str) -> Dict[str, int]:
    """
    Extrai as notas numéricas do texto de análise.
    Procura padrões como: Nota: X/10  ou  **Nota: X/10**
    Retorna dict {critério: nota} para os 8 critérios padrão.
    """
    # Busca todos os "Nota: X/10" no texto
    raw_scores = re.findall(r"\*{0,2}Nota:\s*(\d+)/10\*{0,2}", analysis_text, re.IGNORECASE)

    scores: dict[str, int] = {}
    for i, value in enumerate(raw_scores[:8]):
        if i < len(CRITERIA_NAMES):
            scores[CRITERIA_NAMES[i]] = min(10, max(1, int(value)))
    return scores


def load_score_history() -> dict:
    return _read_json(_scores_file(), {})


def save_score_entry(
    chapter_title: str,
    scores: dict[str, int],
    model: str,
    mode: str = "full",
    text: str = "",
) -> None:
    """Salva uma entrada de notas para o capítulo."""
    from datetime import datetime

    history = load_score_history()
    if chapter_title not in history:
        history[chapter_title] = []

    entries = history[chapter_title]
    average = round(sum(scores.values()) / len(scores), 1) if scores else 0.0

    entry: dict = {
        "timestamp": datetime.now().strftime("%d/%m %H:%M"),
        "model": model,
        "mode": mode,
        "scores": scores,
        "average": average,
        "revision": len(entries) + 1,
    }
    if text.strip():
        entry["metrics"] = compute_text_metrics(text)

    entries.append(entry)
    history[chapter_title] = entries
    _write_json(_scores_file(), history)


def get_score_history(chapter_title: str) -> List[dict]:
    history = load_score_history()
    return history.get(chapter_title, [])


def clear_score_history(chapter_title: str) -> None:
    history = load_score_history()
    history.pop(chapter_title, None)
    _write_json(_scores_file(), history)


def score_badge(score: int) -> str:
    """Retorna emoji de status baseado na nota."""
    if score >= SCORE_THRESHOLDS["publication_ready"]:
        return "🟢"
    if score >= SCORE_THRESHOLDS["developing"]:
        return "🟡"
    return "🔴"


# ─── Anti-IA: Histórico de Pontuação Humana ───────────────────────────────────

def parse_human_score(analysis_text: str) -> Optional[float]:
    """
    Extrai a Pontuação Humana do texto de análise Anti-IA.
    Procura padrões como: **Pontuação Humana: X/10** ou **Pontuação Humana: X.X/10**
    Retorna float (arredondado para 1 casa decimal) ou None se não encontrado.
    """
    match = re.search(
        r"\*{0,2}Pontuação Humana:\s*(\d+(?:\.\d+)?)/10\*{0,2}",
        analysis_text,
        re.IGNORECASE,
    )
    if match:
        score = float(match.group(1))
        return round(min(10.0, max(0.0, score)), 1)
    return None


def load_antia_score_history() -> dict:
    return _read_json(_antia_scores_file(), {})


def save_antia_score_entry(
    chapter_title: str,
    score: int,
    model: str,
    mode: str = "full",
    text: str = "",
) -> None:
    """Salva uma entrada de Pontuação Humana para o capítulo."""
    from datetime import datetime

    history = load_antia_score_history()
    if chapter_title not in history:
        history[chapter_title] = []

    entries = history[chapter_title]
    entry: dict = {
        "timestamp": datetime.now().strftime("%d/%m %H:%M"),
        "model": model,
        "mode": mode,
        "score": score,
        "revision": len(entries) + 1,
    }
    if text.strip():
        entry["metrics"] = compute_text_metrics(text)

    entries.append(entry)
    history[chapter_title] = entries
    _write_json(_antia_scores_file(), history)


def get_antia_score_history(chapter_title: str) -> List[dict]:
    history = load_antia_score_history()
    return history.get(chapter_title, [])


def clear_antia_score_history(chapter_title: str) -> None:
    history = load_antia_score_history()
    history.pop(chapter_title, None)
    _write_json(_antia_scores_file(), history)


# ─── Quality Guards (anti-overfitting) ───────────────────────────────────────


def compute_text_metrics(text: str) -> dict:
    """
    Calcula métricas estilísticas básicas para detecção de drift de voz.

    Retorna:
        avg_sentence_len  — comprimento médio de frase (em palavras)
        ttr               — Type-Token Ratio (diversidade lexical, 0-1)
        avg_word_len      — comprimento médio de palavra (em caracteres)
        word_count        — total de palavras
    """
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = text.split()
    clean_words = [re.sub(r"[.,!?;:\"'()\[\]{}]", "", w).lower() for w in words if w]
    clean_words = [w for w in clean_words if w]

    avg_sentence_len = len(words) / max(len(sentences), 1)
    unique_words = set(clean_words)
    ttr = len(unique_words) / max(len(clean_words), 1)
    avg_word_len = sum(len(w) for w in clean_words) / max(len(clean_words), 1)

    return {
        "avg_sentence_len": round(avg_sentence_len, 1),
        "ttr": round(ttr, 3),
        "avg_word_len": round(avg_word_len, 2),
        "word_count": len(words),
    }


def check_convergence(
    history: List[dict],
    min_delta: float = 0.5,
    lookback: int = 2,
) -> Optional[dict]:
    """
    Detecta platô de melhoria: se o ganho de nota nas últimas `lookback`
    revisões for menor que `min_delta`, retorna um aviso.

    Funciona tanto para histórico de Análise (usa "average") quanto
    para Anti-IA (usa "score").

    Retorna dict com {level, message} ou None.
    """
    if len(history) < lookback + 1:
        return None

    def _get_score(entry: dict) -> float:
        return float(entry.get("average") or entry.get("score") or 0)

    recent = history[-(lookback + 1):]
    improvements = [
        _get_score(recent[i + 1]) - _get_score(recent[i])
        for i in range(lookback)
    ]
    total_gain = sum(improvements)

    if total_gain < min_delta:
        current = _get_score(history[-1])
        return {
            "level": "warning",
            "type": "convergence",
            "message": (
                f"Ganho nas últimas {lookback} revisões: **{total_gain:+.1f} pontos** "
                f"(atual: {current}/10). O texto pode ter atingido um platô — "
                "revisões adicionais têm rendimento decrescente."
            ),
        }
    return None


def check_voice_drift(
    history: List[dict],
    threshold: float = 0.15,
) -> Optional[dict]:
    """
    Detecta deriva de voz comparando métricas estilísticas da v1
    com a revisão mais recente.

    Alerta se TTR ou comprimento médio de frase divergir mais de `threshold` (15%).

    Retorna dict com {level, message, details} ou None.
    """
    # Encontra primeira e última entrada com métricas registradas
    entries_with_metrics = [e for e in history if e.get("metrics")]
    if len(entries_with_metrics) < 2:
        return None

    baseline = entries_with_metrics[0]["metrics"]
    current = entries_with_metrics[-1]["metrics"]

    issues = []

    # Verifica TTR (diversidade lexical)
    base_ttr = baseline.get("ttr", 0)
    curr_ttr = current.get("ttr", 0)
    if base_ttr > 0:
        ttr_drift = abs(curr_ttr - base_ttr) / base_ttr
        if ttr_drift > threshold:
            direction = "caiu" if curr_ttr < base_ttr else "subiu"
            issues.append(
                f"Diversidade lexical (TTR) {direction} "
                f"{ttr_drift:.0%} (baseline: {base_ttr:.3f} → atual: {curr_ttr:.3f})"
            )

    # Verifica comprimento médio de frase
    base_sl = baseline.get("avg_sentence_len", 0)
    curr_sl = current.get("avg_sentence_len", 0)
    if base_sl > 0:
        sl_drift = abs(curr_sl - base_sl) / base_sl
        if sl_drift > threshold:
            direction = "encurtou" if curr_sl < base_sl else "alongou"
            issues.append(
                f"Frases {direction} em média "
                f"{sl_drift:.0%} (baseline: {base_sl:.1f} → atual: {curr_sl:.1f} palavras)"
            )

    if issues:
        return {
            "level": "warning",
            "type": "voice_drift",
            "message": (
                "A voz do texto pode estar derivando das características originais do autor:\n"
                + "\n".join(f"- {issue}" for issue in issues)
            ),
            "details": {"baseline": baseline, "current": current},
        }
    return None


# ─── Session State helpers ────────────────────────────────────────────────────

def init_session_state() -> None:
    """Inicializa o session_state do Streamlit com dados persistidos."""
    if "initialized" not in st.session_state:
        settings = load_settings()
        st.session_state.ai_provider = settings.get("ai_provider", "anthropic")
        st.session_state.ai_model = settings.get("ai_model", "claude-sonnet-4-5-20250929")
        st.session_state.temperature = settings.get("temperature", 0.7)
        st.session_state.max_tokens = settings.get("max_tokens", 4096)
        st.session_state.api_keys = settings.get("api_keys", {})
        st.session_state.initialized = True
