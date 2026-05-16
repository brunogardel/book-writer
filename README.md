# ✍️ Escritor

Um aplicativo completo de suporte à escrita e edição de livros, construído com Streamlit e integrado com múltiplos modelos de IA (OpenAI, Anthropic, Google).

## 🎯 Funcionalidades

### Edição e Organização
- **📝 Editor**: Escreva e organize seus capítulos com interface intuitiva
- **📥 Importar**: Importe manuscritos existentes (DOCX, PDF, TXT)
- **📄 Manuscrito**: Visualize e gerencie seu manuscrito completo
- **📁 Projetos**: Gerencie múltiplos projetos de livros

### Análise e Feedback
- **🤖 Anti-IA**: Detecta padrões de escrita gerados por IA e sugere melhorias para tornar o texto mais humano e único
- **🔍 Análise de Capítulo**: Avaliação editorial detalhada com notas sobre ritmo, personagens, diálogo e tensão
- **📚 Análise do Livro**: Visão geral do manuscrito completo incluindo estrutura, temas, arcos e análise de mercado editorial
- **📊 Dashboard**: Estatísticas e métricas do seu projeto

### Ferramentas de Escrita
- **✨ Continuar Escrevendo**: IA continua seu texto mantendo estilo e voz
- **🔄 Reescrever**: Reformula trechos com diferentes tons e estilos
- **💡 Brainstorm**: Gera ideias para trama, personagens, cenas e conflitos
- **📖 Escritor de Cena**: Auxilia na escrita de cenas específicas

### Organização do Universo
- **📖 Bíblia do Livro**: Gerencie fichas de personagens, locais, linha do tempo e notas do mundo
- **🔎 Busca**: Busca avançada em todo o manuscrito

## 🚀 Instalação

### Pré-requisitos
- Python 3.8+
- pip

### Passos

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/book-writer.git
cd book-writer
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure suas chaves de API:
   - Copie `data/settings.json.example` para `data/settings.json`
   - Adicione suas chaves de API da OpenAI, Anthropic e/ou Google

4. Execute o aplicativo:
```bash
streamlit run app.py
```

## ⚙️ Configuração

O aplicativo suporta múltiplos provedores de IA:
- **OpenAI** (GPT-4, GPT-3.5)
- **Anthropic** (Claude)
- **Google** (Gemini)

Configure suas preferências em **⚙️ Configurações** no menu lateral.

## 📁 Estrutura do Projeto

```
book-writer/
├── app.py                 # Página principal
├── pages/                 # Páginas do Streamlit
│   ├── 0_Importar.py
│   ├── 1_Editor.py
│   ├── 2_Anti_IA.py
│   ├── 3_Analise_Capitulo.py
│   ├── 4_Analise_Livro.py
│   ├── 5_Continuar.py
│   ├── 6_Reescrever.py
│   ├── 7_Brainstorm.py
│   ├── 8_Biblia.py
│   └── 9_Configuracoes.py
├── utils/                 # Utilitários
│   ├── ai.py             # Integração com APIs de IA
│   └── storage.py        # Gerenciamento de dados
└── data/                  # Dados do projeto
    ├── book.json         # Dados do livro
    └── projects/         # Projetos individuais
```

## 🔒 Segurança

- Nunca commite o arquivo `data/settings.json` (contém suas API keys)
- Use o arquivo `.env` para variáveis de ambiente sensíveis
- O `.gitignore` já está configurado para proteger dados sensíveis

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:
1. Fazer fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abrir um Pull Request

## 📝 Licença

Este projeto é de uso pessoal.

## 👤 Autor

Bruno Gardel - bruno.s.gardel@gmail.com
