# 📊 Guia de Modelos de IA - Custo vs Qualidade

## 💰 Tabela de Preços (por milhão de tokens - Maio 2026)

| Provedor | Modelo | Input | Output | Contexto | Melhor Para |
|----------|--------|-------|--------|----------|-------------|
| **Google** | Gemini 2.0 Flash | $0.10 | $0.40 | 1M | ⚠️ Deprecado jun/2026 |
| **Google** | Gemini 2.5 Pro | $1.25 | $10.00 | 1M | Tarefas gerais |
| **Anthropic** | Haiku 4.5 | $1.00 | $5.00 | 200K | Alto volume, respostas rápidas |
| **OpenAI** | GPT-4o | $2.50 | $10.00 | 128K | Equilíbrio custo/qualidade |
| **Anthropic** | Sonnet 4.6 | $3.00 | $15.00 | 200K | **Padrão recomendado** |
| **Anthropic** | Opus 4.7 | $5.00 | $25.00 | 200K | Máxima qualidade |

---

## 🎯 Recomendações por Funcionalidade

### 1. 🤖 **Anti-IA** (Detecção e Humanização)
**Complexidade:** Muito Alta
**Recomendado:** Claude Sonnet 4.6 ou Opus 4.7

**Por quê:**
- Precisa raciocínio profundo sobre estilo e voz
- Detecta padrões sutis de escrita IA
- Reescreve mantendo autenticidade

**Custo estimado por uso:**
- Input: ~2.000 tokens (trecho de texto)
- Output: ~3.000 tokens (análise + reescrita)
- **Sonnet 4.6:** ~$0.05 por análise
- **Opus 4.7:** ~$0.085 por análise

**Recomendação:** Use **Sonnet 4.6** como padrão. Opus 4.7 só se realmente precisar do absoluto melhor.

---

### 2. 🔍 **Análise de Capítulo** (Feedback Editorial)
**Complexidade:** Alta
**Recomendado:** Claude Sonnet 4.6

**Por quê:**
- Análise literária sofisticada
- 8 critérios detalhados com notas
- Leitura cirúrgica e contextual

**Custo estimado por uso:**
- Input: ~5.000 tokens (capítulo de 3.000 palavras)
- Output: ~2.000 tokens (análise detalhada)
- **Sonnet 4.6:** ~$0.045 por análise
- **GPT-4o:** ~$0.032 por análise (alternativa mais barata)

**Recomendação:** **Sonnet 4.6** - melhor para crítica literária

---

### 3. 📚 **Análise do Livro** (Visão Geral)
**Complexidade:** Muito Alta
**Recomendado:** Claude Opus 4.7 ou Sonnet 4.6

**Por quê:**
- Precisa processar manuscrito completo (até 200K tokens!)
- Análise estrutural profunda
- Visão editorial de mercado

**Custo estimado por uso:**
- Input: ~50.000 tokens (livro completo de 30.000 palavras)
- Output: ~3.000 tokens (relatório)
- **Sonnet 4.6:** ~$0.195 por análise
- **Opus 4.7:** ~$0.325 por análise

**Recomendação:** **Sonnet 4.6** (usa menos, economize) → **Opus 4.7** (análise final pré-publicação)

---

### 4. ✨ **Continuar Escrevendo**
**Complexidade:** Média-Alta
**Recomendado:** Claude Sonnet 4.6 ou GPT-4o

**Por quê:**
- Precisa manter voz e estilo do autor
- Geração criativa fluida
- Coerência narrativa

**Custo estimado por uso:**
- Input: ~2.000 tokens (contexto)
- Output: ~1.000 tokens (continuação de 500 palavras)
- **Sonnet 4.6:** ~$0.021 por geração
- **GPT-4o:** ~$0.015 por geração

**Recomendação:** **Sonnet 4.6** para melhor manutenção de voz

---

### 5. 🔄 **Reescrever**
**Complexidade:** Média
**Recomendado:** Claude Haiku 4.5 ou GPT-4o

**Por quê:**
- Reformulação mais mecânica
- 3 versões diferentes
- Não precisa raciocínio tão profundo

**Custo estimado por uso:**
- Input: ~1.500 tokens (texto + instruções)
- Output: ~2.000 tokens (3 versões)
- **Haiku 4.5:** ~$0.012 por reescrita
- **GPT-4o:** ~$0.024 por reescrita
- **Gemini 2.5 Pro:** ~$0.022 por reescrita

**Recomendação:** **Haiku 4.5** - melhor custo-benefício

---

### 6. 💡 **Brainstorm**
**Complexidade:** Média
**Recomendado:** GPT-4o ou Gemini 2.5 Pro

**Por quê:**
- Geração de ideias variadas
- Não precisa profundidade literária extrema
- Volume de output moderado

**Custo estimado por uso:**
- Input: ~1.000 tokens (contexto + tema)
- Output: ~1.500 tokens (5 ideias desenvolvidas)
- **GPT-4o:** ~$0.018 por sessão
- **Gemini 2.5 Pro:** ~$0.016 por sessão
- **Haiku 4.5:** ~$0.009 por sessão

**Recomendação:** **Gemini 2.5 Pro** ou **Haiku 4.5** para economizar

---

### 7. 📖 **Bíblia do Livro** (Extração de Personagens/Locais)
**Complexidade:** Média-Baixa
**Recomendado:** Claude Haiku 4.5 ou Gemini 2.5 Pro

**Por quê:**
- Extração estruturada (JSON)
- Não precisa raciocínio profundo
- Task repetitiva, previsível

**Custo estimado por uso:**
- Input: ~3.000 tokens (capítulo)
- Output: ~800 tokens (JSON estruturado)
- **Haiku 4.5:** ~$0.007 por extração
- **Gemini 2.5 Pro:** ~$0.012 por extração

**Recomendação:** **Haiku 4.5** - ideal para processamento em lote

---

### 8. 📝 **Escritor de Cena** (Geração de Prosa)
**Complexidade:** Alta
**Recomendado:** Claude Sonnet 4.6

**Por quê:**
- Criação de prosa literária humanizada
- Manutenção de voz narrativa
- Evitar vícios de IA

**Custo estimado por uso:**
- Input: ~2.500 tokens (beat sheet + contexto)
- Output: ~2.000 tokens (cena de ~1.000 palavras)
- **Sonnet 4.6:** ~$0.038 por cena
- **Opus 4.7:** ~$0.063 por cena

**Recomendação:** **Sonnet 4.6** - sweet spot para escrita criativa

---

### 9. 🔎 **Busca no Livro**
**Complexidade:** Baixa
**Recomendado:** Claude Haiku 4.5 ou Gemini 2.5 Pro

**Por quê:**
- Resposta baseada em conteúdo
- RAG simples (Retrieval Augmented Generation)
- Respostas curtas

**Custo estimado por uso:**
- Input: ~10.000 tokens (capítulos relevantes)
- Output: ~500 tokens (resposta)
- **Haiku 4.5:** ~$0.012 por busca
- **Gemini 2.5 Pro:** ~$0.018 por busca

**Recomendação:** **Haiku 4.5** - rápido e barato

---

## 🎯 Resumo: Configuração Recomendada

### 💎 **Configuração "Premium" (Melhor Qualidade)**
- **Padrão:** Claude Sonnet 4.6
- **Análise de Livro Completo:** Opus 4.7
- **Custo médio mensal:** ~$15-30 (uso moderado de 300-600 análises/mês)

### ⚖️ **Configuração "Balanceada" (Recomendada)**
- **Tarefas Complexas:** Sonnet 4.6 (Anti-IA, Análise Cap, Escritor Cena)
- **Tarefas Médias:** GPT-4o ou Haiku 4.5 (Reescrever, Brainstorm)
- **Tarefas Simples:** Haiku 4.5 (Bíblia, Busca)
- **Custo médio mensal:** ~$8-15 (uso moderado)

### 💰 **Configuração "Econômica"**
- **Padrão:** Gemini 2.5 Pro ou Haiku 4.5
- **Análises críticas:** Sonnet 4.6 (só quando realmente precisar)
- **Custo médio mensal:** ~$3-8 (uso moderado)

---

## 📈 Comparação de Custos Reais

**Cenário: Revisar um livro de 20 capítulos**

| Tarefa | Vezes | Sonnet 4.6 | Opus 4.7 | GPT-4o | Haiku 4.5 |
|--------|-------|------------|----------|--------|-----------|
| Anti-IA (20 caps) | 20x | $1.00 | $1.70 | $0.70 | $0.40 |
| Análise Cap (20) | 20x | $0.90 | $1.50 | $0.64 | $0.48 |
| Análise Livro | 1x | $0.20 | $0.33 | $0.18 | $0.12 |
| Reescrever (40) | 40x | $0.84 | $1.40 | $0.96 | $0.48 |
| Bíblia (20 caps) | 20x | $0.28 | $0.47 | $0.20 | $0.14 |
| **TOTAL** | | **$3.22** | **$5.40** | **$2.68** | **$1.62** |

**Conclusão:** Para o seu caso (1 livro), a diferença entre Haiku e Opus é ~$4. Use Sonnet como padrão e Opus só para decisões finais.

---

## 🚀 Minha Recomendação Final

### Para o seu caso (escritor usando sozinho):

**NÃO use Opus 4.7 como padrão** - é caro demais para iterações frequentes.

**Configuração ideal:**

```python
# Configuração por funcionalidade
MODELOS_RECOMENDADOS = {
    "anti_ia": "claude-sonnet-4-6",           # Precisa qualidade alta
    "analise_capitulo": "claude-sonnet-4-6",  # Feedback editorial preciso
    "analise_livro": "claude-opus-4-7",       # Use 1x só, vale a pena
    "continuar": "claude-sonnet-4-6",         # Manter voz do autor
    "reescrever": "claude-haiku-4-5",         # Reformulação mais simples
    "brainstorm": "gemini-2-5-pro",           # Ideias = não precisa ser top
    "biblia": "claude-haiku-4-5",             # Extração estruturada
    "escrita_cena": "claude-sonnet-4-6",      # Prosa literária
    "busca": "claude-haiku-4-5"               # RAG simples
}
```

**Custo mensal estimado:** $8-15 (300-500 interações/mês)

Quer que eu implemente um sistema de "modelo por funcionalidade" no seu app?
