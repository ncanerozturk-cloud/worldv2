# worldv2

**A Personal AI Agent Ecosystem — Built for One Person, by One Person.**

> *Your life, your data, your intelligence layer.*

---

## Overview

**worldv2** is a deployable AI agent ecosystem that gives you a private, self-hosted intelligence layer across health, fitness, finance, and career domains. Unlike generic AI assistants that serve millions with one-size-fits-all responses, worldv2 is architected for a single user: **You**.

Deploy it once. It learns your history, understands your patterns, and compounds context with every interaction — permanently. No more fish-memory chat windows that forget everything the moment you close the tab. worldv2 stores everything in a local vector database, building a permanent, searchable record of your life. Your data never leaves your machine. Your agent works exclusively for you.

This isn't a chatbot. This is **your own personal intelligence infrastructure**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SLACK  (Socket Mode)                                │
│                      Natural Language Interface                             │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PYTHON ORCHESTRATOR                                 │
│                    main.py — routing, file ingestion                        │
└──────────────┬──────────────────────┬──────────────────────┬────────────────┘
               │                      │                      │
               ▼                      ▼                      ▼
 ┌─────────────────────┐  ┌───────────────────────┐  ┌──────────────────────┐
 │  HEALTH/SPORT AGENT │  │    QDRANT  (Docker)   │  │  WEBSOCKET  :8765    │
 │  claude-opus-4-6    │  │    caneros_memory      │  │  dashboard.html      │
 │  auto-fact extract  │◄─►  vector search+store  │  │  pixel art monitor   │
 │  context injection  │  │  OpenAI embeddings     │  │  real-time events    │
 └─────────────────────┘  └───────────────────────┘  └──────────────────────┘
               │                      │
               ▼                      ▼
        Anthropic API           Local filesystem
        (LLM reasoning)         (100% private)
```

---

## Tech Stack

| Layer                | Technology                  | Purpose                                             |
|----------------------|-----------------------------|-----------------------------------------------------|
| **Interface**        | Slack Socket Mode           | Natural language entry point, file uploads          |
| **LLM Reasoning**    | Anthropic Claude Opus 4.6   | Agent intelligence, context-aware responses         |
| **Fact Extraction**  | Anthropic Claude Haiku 4.5  | Auto-extract personal facts after every response    |
| **Embeddings**       | OpenAI text-embedding-3-small | Semantic vector search over personal memory       |
| **Vector Memory**    | Qdrant (local Docker)       | Persistent personal context, semantic retrieval     |
| **Core Language**    | Python 3.9+                 | Agent logic, integrations, ingestion pipelines      |
| **Dashboard**        | WebSocket + HTML Canvas     | Real-time pixel art agent activity monitor          |
| **Storage**          | Local filesystem            | Full data sovereignty, zero cloud dependency        |

---

## Agent Modules

### Active

| Agent                   | Slack Channel       | Capabilities                                                                          |
|-------------------------|---------------------|---------------------------------------------------------------------------------------|
| **Health/Sport Agent**  | `#md_health_agent`  | Bloodwork analysis, nutrition, sleep, supplements, longevity, HRV, biomarkers        |
|                         | `#coach_sport_agent`| Training plans, recovery, performance tracking, body composition, periodisation      |

Both channels route to the same unified agent — health and sport are treated as one interconnected system.

### Roadmap

| Agent            | Domain              | Planned Capabilities                                          |
|------------------|---------------------|---------------------------------------------------------------|
| **Finance Agent**| Personal Finance    | Expense categorization, savings goals, investment tracking    |
| **Career Agent** | Professional Growth | Skill gap analysis, learning paths, opportunity matching      |

---

## Memory System

worldv2 uses a three-layer memory ingestion pipeline — all stored in a single Qdrant collection (`caneros_memory`):

| Method           | Trigger                               | What gets saved                                      |
|------------------|---------------------------------------|------------------------------------------------------|
| **Auto-save**    | After every agent response            | Personal facts extracted by Claude Haiku from the conversation |
| **File upload**  | PDF or text file shared in Slack      | Full document content, chunked by page/paragraph     |
| **Manual CLI**   | `python3 ingest.py --file / --text`   | Arbitrary health data, notes, lab results            |

---

## Core Principles

```
┌────────────────────────────────────────────────────────────────────┐
│  1. DATA SOVEREIGNTY                                               │
│     All personal data stays local. Nothing leaves without          │
│     explicit consent. Your intelligence, your rules.               │
├────────────────────────────────────────────────────────────────────┤
│  2. ZERO GENERIC RESPONSES                                         │
│     Every answer is grounded in personal context. No "based on     │
│     general best practices" — only "based on YOUR history."        │
├────────────────────────────────────────────────────────────────────┤
│  3. PROACTIVE > REACTIVE                                           │
│     Agents don't wait to be asked. They surface insights,          │
│     warnings, and opportunities before you think to look.          │
├────────────────────────────────────────────────────────────────────┤
│  4. PERSISTENT MEMORY                                              │
│     Context compounds. Every interaction enriches the system's     │
│     understanding. Your AI remembers what matters.                 │
└────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- [Docker](https://docker.com) — for Qdrant vector database
- Python 3.9+
- A Slack app with **Socket Mode** enabled and the following bot event subscriptions: `message.channels`, `app_mention`, `file_shared`

### Setup

```bash
# 1. Clone
git clone https://github.com/ncanerozturk-cloud/worldv2.git
cd worldv2

# 2. Start Qdrant (vector memory)
docker run -d -p 6333:6333 qdrant/qdrant

# 3. Configure environment
cp .env.example .env
# Fill in: ANTHROPIC_API_KEY, SLACK_BOT_TOKEN, SLACK_APP_TOKEN, OPENAI_API_KEY

# 4. Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Run the system
python3 main.py

# 6. Open the live dashboard
open dashboard.html
```

### Manual Ingestion

```bash
# Ingest a PDF (e.g. blood test results)
python3 ingest.py --file bloodwork.pdf --tag bloodwork --tag 2026-02

# Ingest a text note
python3 ingest.py --text "Vitamin D is 32 ng/mL as of February 2026"
```

---

## Project Structure

```
worldv2/
├── agents/
│   └── health_agent.py      # Unified Health & Sport Agent (Claude Opus 4.6)
├── memory/
│   ├── qdrant_client.py     # Vector memory: save, search, scroll
│   └── file_ingestor.py     # PDF & text ingestion pipeline
├── slack/                   # Slack integration (via main.py)
├── main.py                  # Entry point: Slack bot + WebSocket server
├── ws_server.py             # WebSocket broadcast server (port 8765)
├── ingest.py                # Manual ingestion CLI
├── dashboard.html           # Pixel art real-time agent monitor
├── requirements.txt
└── .env.example
```

---

## Roadmap

### Phase 1: Foundation
- [x] Project architecture design
- [x] Qdrant vector database setup (local Docker)
- [x] Anthropic Claude integration
- [x] OpenAI embeddings (text-embedding-3-small)
- [x] Slack Socket Mode pipeline
- [x] Health & Sport Agent — unified, context-aware

### Phase 2: Memory & Ingestion
- [x] Auto-save — personal facts extracted after every response
- [x] File ingestion — PDF/text upload via Slack
- [x] Manual ingestion CLI (`ingest.py`)
- [x] Semantic search with agent-scoped filtering
- [x] Recent document surfacing (always in context)

### Phase 3: Observability
- [x] WebSocket real-time event broadcasting
- [x] Pixel art agent dashboard (`dashboard.html`)
- [x] Live event stream: message → search → respond → save

### Phase 4: Intelligence Expansion
- [ ] Finance Agent — expense tracking, savings goals
- [ ] Career Agent — skill gaps, learning paths
- [ ] Cross-agent insight correlation
- [ ] Proactive notifications (scheduled health/sport alerts)
- [ ] Weekly automated life reports

### Phase 5: Polish
- [ ] Mobile-friendly Slack workflows
- [ ] Voice input support
- [ ] Backup & restore tooling
- [ ] Multi-language support (TR/EN)

---

## Why "worldv2"?

Because the first version of managing life was manual — spreadsheets, notes, fragmented apps, forgotten insights.

**worldv2** is the upgrade: a unified, intelligent, private system that learns, remembers, and acts.

---

## Author

**N. Caner Ozturk**
Building personal infrastructure for the AI age.

---

<div align="center">

*"If you can architect enterprise networks, you can architect your own intelligence stack."*

</div>
