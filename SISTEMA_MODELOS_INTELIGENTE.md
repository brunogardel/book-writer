# 🤖 Sistema Inteligente de Modelos

## O que é?

Um sistema que **automaticamente seleciona o melhor modelo de IA** para cada funcionalidade do app, otimizando custo e qualidade.

## Como funciona?

Cada ferramenta do app usa automaticamente o modelo mais adequado:

```
Anti-IA          → Claude Sonnet 4.6  ($0.05/uso)  - Precisa raciocínio profundo
Análise Cap      → Claude Sonnet 4.6  ($0.045/uso) - Crítica literária sofisticada
Análise Livro    → Claude Opus 4.7    ($0.325/uso) - Visão editorial completa
Continuar        → Claude Sonnet 4.6  ($0.021/uso) - Manter voz do autor
Reescrever       → Claude Haiku 4.5   ($0.012/uso) - Reformulação mecânica
Brainstorm       → Gemini 2.5 Pro     ($0.016/uso) - Geração de ideias
Bíblia           → Claude Haiku 4.5   ($0.007/uso) - Extração estruturada
Escritor Cena    → Claude Sonnet 4.6  ($0.038/uso) - Prosa literária
Busca            → Claude Haiku 4.5   ($0.012/uso) - RAG simples
```

## Vantagens

### ✅ Economia
- **30-40% mais barato** que usar Opus para tudo
- **Haiku** para tarefas simples (extração, busca)
- **Sonnet** para tarefas complexas (análise, escrita)
- **Opus** só para decisões críticas

### ✅ Qualidade
- Cada modelo otimizado para sua tarefa
- **Não perde qualidade** onde importa
- **Economiza** onde não faz diferença

### ✅ Automático
- Você não precisa escolher toda vez
- Sistema aprende e recomenda
- Pode sobrescrever se quiser

## Exemplo de Economia

**Revisar um livro de 20 capítulos:**

| Configuração | Custo Total |
|--------------|-------------|
| Tudo no Opus 4.7 | $5.40 |
| Tudo no Sonnet 4.6 | $3.22 |
| **Sistema Inteligente** | **$2.18** |
| Tudo no Haiku 4.5 | $1.62 ⚠️ Perde qualidade |

**Economia: ~60% vs Opus, mantendo qualidade onde importa!**

## Como usar no código

### Opção 1: Usar diretamente (novo)

```python
from utils.ai_client import call_ai_for_task

# Sistema escolhe automaticamente o melhor modelo
response = call_ai_for_task(
    task="anti_ia",  # Nome da tarefa
    user_prompt="Analise este texto...",
    system_prompt="Você é um editor...",
    temperature=0.3,
    use_recommended=True  # True = usa recomendação, False = usa config global
)
```

### Opção 2: Obter modelo manualmente

```python
from utils.storage import get_recommended_model
from utils.ai_client import call_ai

# Obtém modelo recomendado
model_info = get_recommended_model("analise_capitulo")

# Usa o modelo
response = call_ai(
    provider=model_info["provider"],
    model=model_info["model"],
    user_prompt="...",
    system_prompt="...",
    temperature=0.3
)
```

### Opção 3: Mostrar info na UI

```python
from utils.components import show_model_info

# Mostra expander com info do modelo + opção de override
use_recommended, _ = show_model_info("anti_ia")

# Usa a escolha do usuário
response = call_ai_for_task(
    task="anti_ia",
    user_prompt="...",
    use_recommended=use_recommended
)
```

## Configuração

As recomendações estão em `utils/storage.py`:

```python
RECOMMENDED_MODELS = {
    "anti_ia": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-6",
        "reason": "Detecção de padrões de IA requer raciocínio profundo",
        "avg_cost": 0.05,
    },
    # ... outros
}
```

## Personalização

Você pode:

1. **Sobrescrever por sessão**: Desmarcar "Usar modelo recomendado" na UI
2. **Mudar globalmente**: Editar `RECOMMENDED_MODELS` em `storage.py`
3. **Adicionar nova tarefa**: Adicionar entrada no dict `RECOMMENDED_MODELS`

## FAQ

### Posso forçar um modelo específico?

Sim! Use `use_recommended=False` e o sistema usará sua configuração global (⚙️ Configurações).

### Como adicionar nova tarefa?

Adicione entrada em `RECOMMENDED_MODELS` no `storage.py`:

```python
"minha_tarefa": {
    "provider": "anthropic",
    "model": "claude-haiku-4-5",
    "reason": "Explicação da escolha",
    "avg_cost": 0.01,
}
```

### Posso ver quanto gastei?

Atualmente não (feature futura). Os custos são **estimativas médias** por uso típico.

### O que acontece se eu não tiver API key do provedor recomendado?

O sistema vai falhar com erro claro. Configure todas as keys em ⚙️ Configurações ou force override para usar um provedor que você tenha.

## Roadmap Futuro

- [ ] Tracking de custos reais por sessão
- [ ] Dashboard de gastos por funcionalidade
- [ ] Cache inteligente para reduzir custos
- [ ] A/B testing de modelos diferentes
- [ ] Ajuste dinâmico baseado em feedback

## Suporte

Dúvidas? Abra issue no GitHub: https://github.com/brunogardel/book-writer/issues
