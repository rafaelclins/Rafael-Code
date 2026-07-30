<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge&logo=python" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/OpenCode%20Zen-Big%20Pickle-8A2BE2?style=for-the-badge&logo=openai" alt="OpenCode Zen Big Pickle">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License">
</p>

<h1 align="center">🤖 Rafael Code</h1>
<p align="center">
  <em>Assistente multiagente de engenharia de software — cloud ou local, 100% open-source.</em>
</p>

---

## 📖 Introdução

**Rafael Code** é um sistema multiagente inspirado no Claude Code da Anthropic, projetado para executar pipelines completos de engenharia de software usando modelos de linguagem.

Por padrão, utiliza o modelo **Big Pickle** gratuito via **OpenCode Zen** na nuvem — sem necessidade de GPU, sem custo por token. Também é possível usar modelos locais via Ollama (Qwen, Llama, etc.) alterando as variáveis de ambiente.

Com **7 agentes especializados** organizados em uma esteira de processamento com **duplo loop de correção** (qualidade + segurança), ele é capaz de interpretar pedidos complexos, planejar, pesquisar, executar, consolidar, revisar e garantir a segurança das respostas.

---

## 🏆 Benchmark de Performance

| Modelo | Agentes | Tempo Total | Infra | Custo |
|--------|---------|-------------|-------|-------|
| **Big Pickle (OpenCode Zen)** | 7 | **~30 seg** | Cloud (gratuita) | **Gratuito** |
| Qwen 2.5 Coder 1.5B (Ollama) | 7 | ~4 min | CPU-only, ~4 GB RAM | Gratuito |
| Qwen 2.5 Coder 7B (Ollama) | 7 | ~30 min | GPU recomendada | Gratuito |
| Claude Code (Anthropic) | N/A | ~30 seg | Cloud | Pago por token |

O modelo **Big Pickle** via OpenCode Zen oferece a melhor experiência: execução em nuvem sem consumir recursos locais, resposta rápida e custo zero.

---

## 🧠 Arquitetura dos 7 Agentes




<img width="1344" height="2306" alt="fluxograma-pipeline" src="https://github.com/user-attachments/assets/77e74239-c5ba-4b09-aadf-3ae51a3cb234" />




### Agente 1 — Alinhador (Orchestrator)
Recebe o pedido bruto do usuário, remove ambiguidades e estrutura o problema em um formato padronizado. Extrai objetivo principal, restrições técnicas e regras de negócio.

### Agente 2 — Planejador (Planner)
Divide o problema em passos sequenciais com critérios de aceitação rigorosos. Planeja exclusivamente arquivos e funções a serem criados/modificados.

### Agente 3 — Pesquisador (Research)
Simula pesquisa técnica sobre as bibliotecas e ferramentas necessárias (FastAPI, LangChain, Pydantic, SQLAlchemy), retornando dados factuais estruturados.

### Agente 4 — Executor (Coding Specialist)
Gera o código completo: models, schemas Pydantic, endpoints FastAPI, chains LangChain, testes e arquivos de configuração.

### Agente 5 — Consolidador (Synthesizer)
Organiza o código e a documentação gerados em uma saída Markdown técnica, clara e profissional. Também atua em modo de correção de segurança.

### Agente 6 — Avaliador / Crítico (QA)
Analisa exclusivamente se o código gerado faz sentido sintático, trata erros corretamente e resolve o problema técnico. Pode **reprovar** o ciclo, disparando uma nova iteração com feedback detalhado.

### Agente 7 — Guardião de Segurança (Guardrail)
Varredura rigorosa de segurança: detecta chaves vazadas, senhas hardcoded, SQL injection e alucinações perigosas. Pode **bloquear** a resposta e acionar o Consolidador para correção.

---

## ⚙️ Instalação (Windows)

### Pré-requisitos

- [Python 3.12+](https://www.python.org/downloads/)

### Obter chave da API OpenCode Zen

1. Acesse [opencode.ai](https://opencode.ai) e crie sua conta
2. Gere uma API Key no painel do OpenCode Zen
3. Defina a chave como variável de ambiente:

```powershell
$env:OPENCODE_ZEN_KEY = "sua-chave-aqui"
```

> Para persistir a chave, adicione ao seu perfil do PowerShell ou use o sistema de variáveis de ambiente do Windows.

### Passo a passo

```powershell
# 1. Clone o repositório
git clone https://github.com/rafaelclins/Rafael-Code.git
cd Rafael-Code

# 2. Crie e ative o ambiente virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Defina sua chave de API
$env:OPENCODE_ZEN_KEY = "sua-chave-aqui"

# 5. Execute
python main.py
```

### Configurar comando global `rafael_code`

Para executar o Rafael Code de qualquer pasta no terminal:

```powershell
# Crie o arquivo .bat com o caminho do seu projeto
@"
@echo off
set "ORIGINAL_DIR=%CD%"
cd /d "C:\caminho\para\Rafael-Code"
"\caminho\para\python.exe" main.py --diretorio "%ORIGINAL_DIR%"
cd /d "%ORIGINAL_DIR%"
"@ | Out-File -FilePath "$env:USERPROFILE\AppData\Local\Microsoft\WindowsApps\rafael_code.bat" -Encoding ASCII
```

> Ajuste os caminhos para refletir a localização do seu Python e do projeto.

Após configurar, **feche e reabra o terminal**. Digite `rafael_code` em qualquer pasta para iniciar o pipeline.

---

## 🔧 Configuração

O comportamento é controlado por variáveis de ambiente:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OPENCODE_ZEN_KEY` | `""` | Chave de API do OpenCode Zen |
| `ZEN_API_URL` | `https://opencode.ai/zen/v1/responses` | Endpoint da API |
| `ZEN_MODEL` | `big-pickle` | Modelo a ser usado |
| `ZEN_TIMEOUT` | `600` | Timeout em segundos |
| `TEMPERATURA_INICIAL` | `0.1` | Temperatura inicial do modelo |
| `MAX_TENTATIVAS_MODELO` | `1` | Tentativas por agente |
| `MAX_REPROVACAO_QUALIDADE` | `3` | Reprovações de qualidade |
| `MAX_REPROVACAO_SEGURANCA` | `2` | Bloqueios de segurança |

### Usar modelo local (Ollama)

Se preferir rodar localmente com Ollama, reinstale as variáveis Ollama:

```powershell
$env:ZEN_API_URL = "http://localhost:11434/api/chat"
$env:ZEN_MODEL = "qwen2.5-coder:1.5b"
# Neste caso a OPENCODE_ZEN_KEY nao e necessaria
```

---

## 🗺️ Roadmap

- [ ] Suporte a modelos 7B/14B para tarefas complexas
- [ ] Plugin para VS Code com atalho de teclado
- [ ] Histórico de sessões com SQLite
- [ ] Modo headless para integração CI/CD
- [ ] Templates de prompt customizáveis

---

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

---

<p align="center">
  Feito com ❤️ por <a href="https://github.com/rafaelclins">@rafaelclins</a>
</p>
