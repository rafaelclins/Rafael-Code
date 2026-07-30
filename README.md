<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge&logo=python" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/Ollama-Qwen%202.5%20Coder%201.5B-8A2BE2?style=for-the-badge&logo=ollama" alt="Ollama Qwen 2.5 Coder">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License">
</p>

<h1 align="center">🤖 Rafael Code</h1>
<p align="center">
  <em>Assistente multiagente de engenharia de software — 100% local, 100% open-source.</em>
</p>

---

## 📖 Introdução

**Rafael Code** é um sistema multiagente inspirado no Claude Code da Anthropic, projetado para executar pipelines completos de engenharia de software usando modelos de linguagem locais via Ollama.

Diferente de soluções proprietárias que exigem internet e pagamento por token, o Rafael Code roda **integralmente na sua máquina** — sem enviar código para terceiros, sem custo por chamada, e sem depender de GPUs caras.

Com **7 agentes especializados** organizados em uma esteira de processamento com **duplo loop de correção** (qualidade + segurança), ele é capaz de interpretar pedidos complexos, planejar, pesquisar, executar, consolidar, revisar e garantir a segurança das respostas — tudo isso em **~4 minutos** com modelos leves (1.5B).

---

## 🏆 Benchmark de Performance

| Modelo | Agentes | Tempo Total | RAM | GPU | Custo |
|--------|---------|-------------|-----|-----|-------|
| **Qwen 2.5 Coder 1.5B** | 7 | **~4 min** | ~4 GB | CPU-only | **Gratuito** |
| Qwen 2.5 Coder 7B | 7 | ~30 min | ~12 GB | GPU recomendada | Gratuito |
| Claude Code (Anthropic) | N/A | ~30 seg | N/A | Cloud | Pago por token |

O modelo **1.5B** oferece o melhor custo-benefício para desenvolvimento local: executa em qualquer notebook sem GPU, consome pouca RAM, e entrega resultados técnicos sólidos em uma fração do tempo de modelos maiores.

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
- [Ollama](https://ollama.com/download/windows)
- Modelo Qwen 2.5 Coder 1.5B baixado via Ollama

```powershell
# Baixe o modelo
ollama pull qwen2.5-coder:1.5b
```

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

# 4. Teste a execução direta
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

## 🎥 Demonstração

<p align="center">
  <a href="https://www.youtube.com/watch?v=SEU_VIDEO_ID">
    <img src="https://img.shields.io/badge/▶️%20Assistir%20Demo-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="Vídeo de demonstração no YouTube">
  </a>
</p>

<!-- Substitua o link acima pelo URL do seu vídeo de demonstração. -->
<!-- Exemplo de vídeo incorporado:
[![Rafael Code em ação](https://img.youtube.com/vi/SEU_VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=SEU_VIDEO_ID)
-->

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
