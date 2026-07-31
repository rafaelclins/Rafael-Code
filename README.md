<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge&logo=python" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/OpenCode%20Zen-Big%20Pickle-8A2BE2?style=for-the-badge&logo=openai" alt="OpenCode Zen Big Pickle">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License">
</p>

<h1 align="center">Rafael Code</h1>
<p align="center">
  <em>Framework de orquestração multiagente para engenharia de software assistida por IA — cloud ou local, 100% open-source.</em>
</p>

---

## Introdução

**Rafael Code** é um framework de orquestração multiagente para engenharia de software assistida por IA. Ele coordena um pipeline autônomo de agentes especializados — alinhamento, planejamento, pesquisa, execução, consolidação, revisão e segurança — que interpretam pedidos complexos e produzem software validado de ponta a ponta.

A arquitetura foi projetada para autonomia, resiliência e controle de fluxo: cada etapa troca dados por esquemas validados, o pipeline se auto-corrige em duplo loop (qualidade + segurança) e o processo é rastreável e determinístico, com scanner AST, histórico persistente e integração contínua.

Por padrão, utiliza o modelo **Big Pickle** gratuito via **OpenCode Zen** na nuvem — sem necessidade de GPU, sem custo por token. Também é possível usar modelos locais via Ollama (Qwen, Llama, etc.) alterando as variáveis de ambiente.

---

## 🎯 Por que este projeto foi criado?

O objetivo do Rafael Code é estudar e demonstrar arquiteturas multiagentes para engenharia de software assistida por IA. O projeto busca explorar como agentes especializados podem colaborar de forma autônoma para planejar, implementar, revisar e validar software utilizando modelos de linguagem locais e em nuvem, mantendo uma arquitetura modular, transparente e extensível com garantias de segurança e validação determinística (AST, CI/CD e histórico persistente).

---

## Funcionalidades

- **7 agentes especializados** com direção tecnológica adaptativa: código simples em Python puro, sistemas corporativos ou RAG apenas quando fizer sentido técnico
- **Duplo loop de correção**: qualidade (Agente 6) e segurança (Agente 7)
- **Modo interativo PLAN ↔ BUILD**: converse livremente com o Gerente em texto corrido (sem JSON) para refinar o plano e alterne para o modo BUILD com a tecla **TAB**, disparando a esteira completa A1→A7 com o contexto da conversa
- **Renderização Markdown** das respostas: negrito, itálico, listas e blocos de código são exibidos estilizados nos painéis do Rich (Gerente, agentes e resultado final)
- **Histórico de sessões com SQLite** (`rafael_code.db`): pedidos anteriores são injetados como contexto no Agente 1
- **Scanner AST para RAG local** (`repo_scanner.py`): mapa das classes, funções e docstrings do projeto injetado nos Agentes 3 e 4
- **Gravação segura no HD** (`--criar`): FileManager com validação de path traversal e backups automáticos em `.rafael_backups`
- **Modo Headless** para CI/CD: sem `input()`, sem spinner, falha rápida com códigos de saída precisos
- **Interface em Português do Brasil**: terminal configurado em UTF-8 puro, logs e prompts de sistema com acentuação correta
- **Saída em JSON validada** por schemas Pydantic com parsing defensivo
- **Cláusula de escape no Avaliador**: textos puros (sem código) são aprovados automaticamente

---

## Benchmark de Performance

| Modelo | Agentes | Tempo Total | Infra | Custo |
|--------|---------|-------------|-------|-------|
| **Big Pickle (OpenCode Zen)** | 7 | **~30 seg** | Cloud (gratuita) | **Gratuito** |
| Qwen 2.5 Coder 1.5B (Ollama) | 7 | ~4 min | CPU-only, ~4 GB RAM | Gratuito |
| Qwen 2.5 Coder 7B (Ollama) | 7 | ~30 min | GPU recomendada | Gratuito |
| Claude Code (Anthropic) | N/A | ~30 seg | Cloud | Pago por token |

O modelo **Big Pickle** via OpenCode Zen oferece a melhor experiência: execução em nuvem sem consumir recursos locais, resposta rápida e custo zero.

---

## Arquitetura dos 7 Agentes

<img width="1344" height="2306" alt="fluxograma-pipeline" src="https://github.com/user-attachments/assets/77e74239-c5ba-4b09-aadf-3ae51a3cb234" />

### Agente 1 — Alinhador (Orchestrator)
Recebe o pedido bruto do usuário, remove ambiguidades e estrutura o problema em um formato padronizado. Extrai objetivo principal, restrições técnicas e regras de negócio. Antes de processar, injeta como contexto o **histórico da conversa PLAN** (quando o pipeline é disparado pelo modo BUILD) ou, na ausência dele, os **últimos 2 pedidos salvos no SQLite**.

### Agente 2 — Planejador (Planner)
Divide o problema em passos sequenciais com critérios de aceitação rigorosos. Planeja exclusivamente arquivos e funções a serem criados/modificados.

### Agente 3 — Pesquisador (Research)
Simula pesquisa técnica sobre as bibliotecas e ferramentas necessárias, retornando dados factuais estruturados. A tecnologia é escolhida conforme o pedido, não imposta. Recebe o **mapa do repositório (Scanner AST)** como contexto e propõe integração com o código já existente em vez de duplicação.

### Agente 4 — Executor (Coding Specialist)
Gera o código completo: models, schemas Pydantic, endpoints, testes e arquivos de configuração — na stack mais adequada ao pedido. Reutiliza funções, classes e variáveis já existentes listadas no mapa do repositório fornecido na entrada.

### Agente 5 — Consolidador (Synthesizer)
Organiza o código e a documentação gerados em uma saída Markdown técnica, clara e profissional, sempre com **ortografia e acentuação corretas em PT-BR**. Também lista os arquivos a criar ou modificar na chave `arquivos` (com `caminho`, `acao` e `conteudo` completo), habilitando a gravação segura com `--criar`. Atua ainda em modo de correção de segurança.

### Agente 6 — Avaliador / Crítico (QA)
Analisa se o código gerado trata erros corretamente e resolve o problema técnico. Pode **reprovar** o ciclo, disparando uma nova iteração com feedback detalhado. Se o pedido **não envolver código** (apenas textos, relatórios ou Markdown), o checklist de segurança é ignorado e o documento é aprovado imediatamente.

### Agente 7 — Guardião de Segurança (Guardrail)
Varredura rigorosa de segurança: detecta chaves vazadas, senhas hardcoded, SQL injection e alucinações perigosas. Pode **bloquear** a resposta e acionar o Consolidador para correção.

---

## Instalação (Windows)

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

### Linha de comando

```powershell
python main.py                                    # modo interativo: chat PLAN + TAB para BUILD
python main.py --diretorio "C:\Projeto"           # analisa diretório específico
python main.py --criar                            # grava os arquivos propostos no HD
python main.py --headless                         # modo CI/CD sem interação
python main.py --verbose                          # exibe os painéis dos agentes em Rich (Markdown)
python main.py --version                          # exibe a versão (1.2.0)
```

O pipeline retorna código de saída `0` em caso de sucesso total (Aprovado + Seguro) e `1` em caso de falha (Avaliador reprovou ou Guardião bloqueou).

---

## Modo Interativo (PLAN ↔ BUILD)

O modo interativo (`python main.py`) funciona em duas fases alternadas pela tecla **TAB**:

1. **PLAN** — o prompt exibe o indicador `[PLAN] >`. Você conversa livremente com o **Gerente** em texto corrido (sem JSON e sem invocar a esteira): refine requisitos, discuta ideias e pergunte quando o plano estiver pronto. O Gerente resume o plano proposto e sugere quando entrar no BUILD.
2. **BUILD** — pressione **TAB** para alternar (indicador `[BUILD] >`) e **Enter** para disparar a esteira completa A1→A7. Todo o histórico da conversa PLAN é injetado como contexto no Agente 1 (Alinhador). Após o pipeline, o modo volta automaticamente para PLAN.

Detalhes:

- A barra inferior do prompt mostra o modo ativo e a dica de atalho (TAB alterna o modo).
- Na primeira rodada, um Enter vazio usa um pedido de exemplo (portfólio React + Tailwind com deploy gratuito).
- `Ctrl+C` / `Ctrl+D` encerram o programa a qualquer momento.
- As respostas do Gerente, dos agentes e o resultado final são exibidos em **painéis Rich com Markdown renderizado** (negrito, itálico, listas e blocos de código).

```powershell
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
"C:\caminho\para\python.exe" main.py --diretorio "%ORIGINAL_DIR%" %*
cd /d "%ORIGINAL_DIR%"
"@ | Out-File -FilePath "$env:USERPROFILE\AppData\Local\Microsoft\WindowsApps\rafael_code.bat" -Encoding ASCII
```

> Ajuste os caminhos para refletir a localização do seu Python e do projeto. O `%*` repassa todos os argumentos extras (como `--headless`) para o `main.py`.

Após configurar, **feche e reabra o terminal**. Digite `rafael_code` em qualquer pasta para iniciar o pipeline.

> Um arquivo de exemplo `rafael_code.bat.example` está incluído no repositório.

---

## Modo Headless (CI/CD)

O modo headless automatiza a verificação do repositório em servidores de integração contínua:

```powershell
python main.py --headless
```

Nesse modo:

- **Não chama** `input()` — o pedido padrão é fixado como: *"Analise todos os arquivos de código deste diretório atual e valide se existem bugs de sintaxe, erros de lógica ou brechas de segurança."*
- **Desativa o spinner** visual, exibindo apenas logs limpos e diretos
- **Sucesso total** (Aprovado + Seguro) → `sys.exit(0)`
- **Avaliador reprovou** ou **Guardião bloqueou** → `sys.exit(1)` imediato, sem retentativas, fazendo o servidor de CI/CD falhar e bloquear o Pull Request

### GitHub Actions

O repositório inclui o workflow `.github/workflows/rafael_code_ci.yml`, que roda em todo Push/Pull Request na branch `main`:

1. Checkout do código (`actions/checkout@v4`)
2. Python 3.12 no `ubuntu-latest` (`actions/setup-python@v5`)
3. Instalação das dependências do `requirements.txt`
4. Execução de `python main.py --headless` com a variável `OPENCODE_ZEN_KEY` vinda dos GitHub Secrets

Para configurar no GitHub, adicione sua chave em **Settings → Secrets and variables → Actions** com o nome `OPENCODE_ZEN_KEY`.

---

## Histórico de Sessões (SQLite)

O banco `rafael_code.db` é criado automaticamente na raiz do projeto com duas tabelas:

| Tabela | Colunas |
|--------|---------|
| `sessoes` | `id`, `timestamp`, `pedido_usuario` |
| `logs_agentes` | `id`, `sessao_id`, `agente`, `texto_gerado` |

Fluxo:

1. `init_db()` cria o banco e as tabelas ao iniciar o pipeline
2. `criar_sessao(pedido_usuario)` salva o input do usuário no início do pipeline
3. `salvar_log_agente(sessao_id, agente, texto_gerado)` registra o output JSON de cada agente assim que concluído
4. `ultimos_pedidos(limite=2)` lê os últimos pedidos anteriores e os injeta no Agente 1 (Alinhador) como contexto histórico

---

## Gravação Segura no HD (`--criar`)

O Agente 5 (Consolidador) pode listar arquivos a criar ou modificar na chave `arquivos` do JSON, com `caminho`, `acao` (criar/modificar) e `conteudo` completo. Com a flag `--criar`, o pipeline grava esses arquivos no disco de forma segura:

- **Validação de caminho**: apenas arquivos dentro do repositório são aceitos — tentativas de `../` (path traversal) ou caminhos absolutos fora do projeto são bloqueadas
- **Backup automático**: antes de sobrescrever ou excluir um arquivo, o original é copiado para `.rafael_backups/<TIMESTAMP>/`
- **UTF-8 puro**: arquivos gravados com codificação `utf-8` e quebras de linha Unix
- **Confirmação interativa**: pergunta `Deseja confirmar a gravação no HD? (S/n)`; no modo `--headless` a gravação é executada sem confirmação
- **Relatório de alterações**: exibe o status (sucesso/erro) de cada arquivo ao final da gravação

```powershell
python main.py --criar
```

---

## Scanner AST — RAG Local (`repo_scanner.py`)

No início do pipeline, o repositório é escaneado e um **mapa estrutural** em Markdown é gerado para servir de contexto local (RAG) aos agentes:

- Varre todos os arquivos `.py` com `ast.parse`, extraindo **classes, métodos e funções** com assinaturas e docstrings
- Ignora `.git`, `.venv`, `__pycache__`, `.rafael_backups`, `.github` e pastas ocultas
- O mapa é injetado no **Agente 3 (Pesquisador)** e no **Agente 4 (Executor)**, orientando a reutilização do código já existente em vez de duplicação
- Arquivos com erro de sintaxe ou encoding inválido são ignorados com aviso no log
- Sem dependências externas — apenas a biblioteca padrão (`ast`, `pathlib`)
- Saída limitada a 8000 caracteres para não estourar o contexto do modelo

Função pública: `escanear_repositorio(root_dir=".") -> str`.

---

## Configuração

O comportamento é controlado por variáveis de ambiente:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OPENCODE_ZEN_KEY` | `""` | Chave de API do OpenCode Zen |
| `ZEN_API_URL` | `https://opencode.ai/zen/v1/responses` | Endpoint da API |
| `ZEN_MODEL` | `big-pickle` | Modelo a ser usado |
| `ZEN_TIMEOUT` | `600` | Timeout em segundos |
| `OLLAMA_API_URL` | `http://localhost:11434/api/chat` | Endpoint local usado no fallback automático |
| `OLLAMA_MODEL` | `qwen2.5-coder` | Modelo local usado no fallback quando a API Zen falha |
| `TEMPERATURA_INICIAL` | `0.1` | Temperatura inicial do modelo |
| `TEMPERATURA_INCREMENTO` | `0.2` | Incremento de temperatura a cada tentativa |
| `LOG_LEVEL` | `INFO` | Nível de log (DEBUG, INFO, WARNING, ERROR) |
| `MAX_TENTATIVAS_MODELO` | `3` | Tentativas por agente na API Zen |
| `MAX_REPROVACAO_QUALIDADE` | `3` | Reprovações de qualidade |
| `MAX_REPROVACAO_SEGURANCA` | `2` | Bloqueios de segurança |
| `OLLAMA_FALLBACK_ATIVADO` | `true` | Habilita o fallback para Ollama local após esgotar as tentativas na Zen |

### Usar modelo local (Ollama)

Se preferir rodar localmente com Ollama, redefina as variáveis:

```powershell
$env:ZEN_API_URL = "http://localhost:11434/api/chat"
$env:ZEN_MODEL = "qwen2.5-coder:1.5b"
# Neste caso a OPENCODE_ZEN_KEY não é necessária
```

---

## Funcionamento Interno

### Pipeline

O pipeline tem duas fases:

- **Fase PLAN** — ocorre no modo interativo: o Gerente conversa com o usuário em texto corrido para refinar o plano, sem invocar os agentes da esteira.
- **Fase BUILD** — dispara a esteira A1→A7 a partir de um pedido e do **contexto da conversa PLAN** acumulada (ou de um pedido direto via `--headless`).

Na fase BUILD, a esteira inicia com um **scan estrutural** do repositório (Scanner AST), gerando o mapa local que é injetado nos agentes de pesquisa e execução:

1. **Alinhamento** → entrada do usuário é estruturada em JSON, com o contexto da conversa PLAN ou os últimos pedidos do SQLite
2. **Planejamento** → plano de ação com passos e critérios
3. **Pesquisa** → dados técnicos coletados sobre as bibliotecas adequadas ao pedido
4. **Execução** → código gerado pelo modelo
5. **Consolidação** → código organizado em Markdown com PT-BR correto
6. **Avaliação (QA)** → loop de qualidade: aprova ou reprova com feedback (aprovado imediato se não houver código)
7. **Segurança (Guardrail)** → loop de segurança: libera ou bloqueia com correção

Durante a esteira (com `--verbose`), as fases `[PLAN]`/`[BUILD]` e as respostas de cada agente são exibidas em painéis Rich com Markdown renderizado.

### Tratamento de erros

- **Timeout progressivo**: até 600s de espera com spinner mostrando o tempo decorrido
- **Auto-retry**: se a resposta vier vazia, re-tenta automaticamente com temperature=0.2
- **Parsing defensivo**: extração de JSON por 3 estratégias (direto, profundidade, regex)
- **Retry HTTP**: 502/503/504 com backoff exponencial
- **Feedback cíclico**: falha de agente vira reprovação no loop de qualidade
- **Path traversal bloqueado**: na gravação (`--criar`), arquivos fora do repositório ou com caminho absoluto são rejeitados pelo FileManager
- **UTF-8 puro**: terminal forçado a UTF-8 para suportar acentos do Português do Brasil
- **max_tokens alto**: respostas longas sem cortes no meio da frase

---

## Roadmap

- [x] Histórico de sessões com SQLite
- [x] Scanner AST para RAG local (contexto do repositório nos agentes)
- [x] Gravação segura no HD com backups automáticos (`--criar`)
- [x] Modo headless para integração CI/CD
- [x] GitHub Actions automatizado
- [x] Modo interativo PLAN ↔ BUILD com chat livre e alternância via TAB
- [x] Renderização Markdown das respostas nos painéis do Rich
- [ ] Suporte a modelos 7B/14B para tarefas complexas
- [ ] Plugin para VS Code com atalho de teclado
- [ ] Templates de prompt customizáveis
- [ ] Logs de agentes visualizáveis em uma página web

---

## Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

---

<p align="center">
  Feito com ❤️ por <a href="https://github.com/rafaelclins">@rafaelclins</a>
</p>
