<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge&logo=python" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/OpenCode%20Zen-Big%20Pickle-8A2BE2?style=for-the-badge&logo=openai" alt="OpenCode Zen Big Pickle">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License">
</p>

<h1 align="center">Rafael Code</h1>
<p align="center">
  <em>Assistente multiagente de engenharia de software — cloud ou local, 100% open-source.</em>
</p>

---

## Introducao

**Rafael Code** e um sistema multiagente inspirado no Claude Code da Anthropic, projetado para executar pipelines completos de engenharia de software usando modelos de linguagem.

Por padrao, utiliza o modelo **Big Pickle** gratuito via **OpenCode Zen** na nuvem — sem necessidade de GPU, sem custo por token. Tambem e possivel usar modelos locais via Ollama (Qwen, Llama, etc.) alterando as variaveis de ambiente.

Com **7 agentes especializados** organizados em uma esteira de processamento com **duplo loop de correcao** (qualidade + seguranca), ele e capaz de interpretar pedidos complexos, planejar, pesquisar, executar, consolidar, revisar e garantir a seguranca das respostas.

---

## Benchmark de Performance

| Modelo | Agentes | Tempo Total | Infra | Custo |
|--------|---------|-------------|-------|-------|
| **Big Pickle (OpenCode Zen)** | 7 | **~30 seg** | Cloud (gratuita) | **Gratuito** |
| Qwen 2.5 Coder 1.5B (Ollama) | 7 | ~4 min | CPU-only, ~4 GB RAM | Gratuito |
| Qwen 2.5 Coder 7B (Ollama) | 7 | ~30 min | GPU recomendada | Gratuito |
| Claude Code (Anthropic) | N/A | ~30 seg | Cloud | Pago por token |

O modelo **Big Pickle** via OpenCode Zen oferece a melhor experiencia: execucao em nuvem sem consumir recursos locais, resposta rapida e custo zero.

---

## Arquitetura dos 7 Agentes

<img width="1344" height="2306" alt="fluxograma-pipeline" src="https://github.com/user-attachments/assets/77e74239-c5ba-4b09-aadf-3ae51a3cb234" />

### Agente 1 — Alinhador (Orchestrator)
Recebe o pedido bruto do usuario, remove ambiguidades e estrutura o problema em um formato padronizado. Extrai objetivo principal, restricoes tecnicas e regras de negocio.

### Agente 2 — Planejador (Planner)
Divide o problema em passos sequenciais com criterios de aceitacao rigorosos. Planeja exclusivamente arquivos e funcoes a serem criados/modificados.

### Agente 3 — Pesquisador (Research)
Simula pesquisa tecnica sobre as bibliotecas e ferramentas necessarias (FastAPI, LangChain, Pydantic, SQLAlchemy), retornando dados factuais estruturados.

### Agente 4 — Executor (Coding Specialist)
Gera o codigo completo: models, schemas Pydantic, endpoints FastAPI, chains LangChain, testes e arquivos de configuracao.

### Agente 5 — Consolidador (Synthesizer)
Organiza o codigo e a documentacao gerados em uma saida Markdown tecnica, clara e profissional. Tambem atua em modo de correcao de seguranca.

### Agente 6 — Avaliador / Critico (QA)
Analisa exclusivamente se o codigo gerado faz sentido sintatico, trata erros corretamente e resolve o problema tecnico. Pode **reprovar** o ciclo, disparando uma nova iteracao com feedback detalhado.

### Agente 7 — Guardiao de Seguranca (Guardrail)
Varredura rigorosa de seguranca: detecta chaves vazadas, senhas hardcoded, SQL injection e alucinacoes perigosas. Pode **bloquear** a resposta e acionar o Consolidador para correcao.

---

## Instalacao (Windows)

### Pre-requisitos

- [Python 3.12+](https://www.python.org/downloads/)

### Obter chave da API OpenCode Zen

1. Acesse [opencode.ai](https://opencode.ai) e crie sua conta
2. Gere uma API Key no painel do OpenCode Zen
3. Defina a chave como variavel de ambiente:

```powershell
$env:OPENCODE_ZEN_KEY = "sua-chave-aqui"
```

> Para persistir a chave, adicione ao seu perfil do PowerShell ou use o sistema de variaveis de ambiente do Windows.

### Passo a passo

```powershell
# 1. Clone o repositorio
git clone https://github.com/rafaelclins/Rafael-Code.git
cd Rafael-Code

# 2. Crie e ative o ambiente virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Instale as dependencias
pip install -r requirements.txt

# 4. Defina sua chave de API
$env:OPENCODE_ZEN_KEY = "sua-chave-aqui"

# 5. Execute
python main.py
```

### Linha de comando

```powershell
python main.py                           # modo interativo
python main.py --diretorio "C:\Projeto"  # analisa diretorio especifico
python main.py --verbose                 # exibe JSON bruto das chamadas
python main.py --version                 # exibe a versao (1.0.0)
```

O pipeline retorna codigo de saida `0` em caso de sucesso e `1` em caso de falha.

### Configurar comando global `rafael_code`

Para executar o Rafael Code de qualquer pasta no terminal:

```powershell
# Crie o arquivo .bat com o caminho do seu projeto
@"
@echo off
set "ORIGINAL_DIR=%CD%"
cd /d "C:\caminho\para\Rafael-Code"
"C:\caminho\para\python.exe" main.py --diretorio "%ORIGINAL_DIR%"
cd /d "%ORIGINAL_DIR%"
"@ | Out-File -FilePath "$env:USERPROFILE\AppData\Local\Microsoft\WindowsApps\rafael_code.bat" -Encoding ASCII
```

> Ajuste os caminhos para refletir a localizacao do seu Python e do projeto.

Apos configurar, **feche e reabra o terminal**. Digite `rafael_code` em qualquer pasta para iniciar o pipeline.

> Um arquivo de exemplo `rafael_code.bat.example` esta incluido no repositorio.

---

## Configuracao

O comportamento e controlado por variaveis de ambiente:

| Variavel | Padrao | Descricao |
|----------|--------|-----------|
| `OPENCODE_ZEN_KEY` | `""` | Chave de API do OpenCode Zen |
| `ZEN_API_URL` | `https://opencode.ai/zen/v1/responses` | Endpoint da API |
| `ZEN_MODEL` | `big-pickle` | Modelo a ser usado |
| `ZEN_TIMEOUT` | `600` | Timeout em segundos |
| `TEMPERATURA_INICIAL` | `0.1` | Temperatura inicial do modelo |
| `TEMPERATURA_INCREMENTO` | `0.2` | Incremento de temperatura a cada tentativa |
| `LOG_LEVEL` | `INFO` | Nivel de log (DEBUG, INFO, WARNING, ERROR) |
| `MAX_TENTATIVAS_MODELO` | `1` | Tentativas por agente |
| `MAX_REPROVACAO_QUALIDADE` | `3` | Reprovacoes de qualidade |
| `MAX_REPROVACAO_SEGURANCA` | `2` | Bloqueios de seguranca |

### Usar modelo local (Ollama)

Se preferir rodar localmente com Ollama, reinstale as variaveis:

```powershell
$env:ZEN_API_URL = "http://localhost:11434/api/chat"
$env:ZEN_MODEL = "qwen2.5-coder:1.5b"
# Neste caso a OPENCODE_ZEN_KEY nao e necessaria
```

---

## Funcionamento Interno

### Pipeline

1. **Alinhamento** → entrada do usuario e estruturada em JSON
2. **Planejamento** → plano de acao com passos e criterios
3. **Pesquisa** → dados tecnicos coletados sobre bibliotecas
4. **Execucao** → codigo gerado pelo modelo
5. **Consolidacao** → codigo organizado em Markdown
6. **Avaliacao (QA)** → loop de qualidade: aprova ou reprova com feedback
7. **Seguranca (Guardrail)** → loop de seguranca: libera ou bloqueia com correcao

### Tratamento de erros

- **Timeout progressivo**: ate 600s de espera com spinner mostrando o tempo decorrido
- **Auto-retry**: se a resposta vier vazia, re-tenta automaticamente com temperature=0.2
- **Parsing defensivo**: extracao de JSON por 3 estrategias (direto, profundidade, regex)
- **Retry HTTP**: 502/503/504 com backoff exponencial
- **Feedback ciclico**: falha de agente vira reprovacao no loop de qualidade

---

## Roadmap

- [ ] Suporte a modelos 7B/14B para tarefas complexas
- [ ] Plugin para VS Code com atalho de teclado
- [ ] Historico de sessoes com SQLite
- [ ] Modo headless para integracao CI/CD
- [ ] Templates de prompt customizaveis

---

## Licenca

Distribuido sob a licenca MIT. Veja `LICENSE` para mais informacoes.

---

<p align="center">
  Feito com ❤️ por <a href="https://github.com/rafaelclins">@rafaelclins</a>
</p>
