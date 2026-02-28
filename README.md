# worldv2

**A Personal AI Agent Ecosystem — Built for One Person, by One Person.**

> *Your life, your data, your intelligence layer.*

---

## Overview

**worldv2** is a modular AI agent ecosystem designed to augment daily decision-making across health, fitness, finance, and career domains. Unlike generic AI assistants that serve millions with one-size-fits-all responses, worldv2 is architected for a single user: **Caner**.

Every interaction is contextualized. Every response is personalized. Every piece of data stays local.

This isn't just an assistant — it's a **personal intelligence infrastructure**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SLACK INTERFACE                                │
│                         (Natural Language Layer)                            │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLAUDE CODE CLI                                   │
│                      (Orchestration & Reasoning)                            │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
          ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
          │  HEALTH AGENT   │ │  SPORT AGENT    │ │  FINANCE AGENT  │
          │    [ACTIVE]     │ │    [ACTIVE]     │ │   [ROADMAP]     │
          └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
                   │                   │                   │
                   └───────────────────┼───────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              QDRANT (Docker)                                │
│                      Vector Memory / Personal Context                       │
│                                                                             │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                   │
│   │ Health Memory │  │ Sport Memory  │  │ Career Memory │  ...              │
│   └───────────────┘  └───────────────┘  └───────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                           ┌───────────────────┐
                           │   LOCAL STORAGE   │
                           │  (100% Private)   │
                           └───────────────────┘
```

---

## Tech Stack

| Layer              | Technology         | Purpose                                      |
|--------------------|--------------------|----------------------------------------------|
| **Interface**      | Slack              | Natural conversation entry point             |
| **Orchestration**  | Claude Code CLI    | Agent coordination & advanced reasoning      |
| **Core Language**  | Python 3.11+       | Agent logic, integrations, data pipelines    |
| **Vector Memory**  | Qdrant (Docker)    | Semantic search over personal context        |
| **Storage**        | Local filesystem   | Full data sovereignty, zero cloud dependency |

---

## Agent Modules

### Active

| Agent           | Domain           | Capabilities                                                        |
|-----------------|------------------|---------------------------------------------------------------------|
| **Health Agent**| Wellness & Vitals| Sleep analysis, nutrition tracking, supplement reminders, mood logs |
| **Sport Agent** | Fitness & Training| Workout planning, recovery insights, performance trends             |

### Roadmap

| Agent            | Domain              | Planned Capabilities                                          |
|------------------|---------------------|---------------------------------------------------------------|
| **Finance Agent**| Personal Finance    | Expense categorization, savings goals, investment tracking    |
| **Career Agent** | Professional Growth | Skill gap analysis, learning paths, opportunity matching      |

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

## Roadmap

### Phase 1: Foundation
- [x] Project architecture design
- [x] Qdrant vector database setup (Docker)
- [x] Claude Code CLI integration
- [x] Slack bot configuration
- [x] Health Agent — core implementation
- [x] Sport Agent — core implementation

### Phase 2: Expansion
- [ ] Finance Agent — expense tracking module
- [ ] Finance Agent — savings goal engine
- [ ] Career Agent — skill inventory system
- [ ] Career Agent — learning path generator
- [ ] Cross-agent insight correlation

### Phase 3: Intelligence
- [ ] Proactive notification system
- [ ] Weekly automated life reports
- [ ] Predictive health/fitness alerts
- [ ] Natural language memory queries
- [ ] Agent-to-agent communication layer

### Phase 4: Polish
- [ ] Mobile-friendly Slack workflows
- [ ] Voice input support
- [ ] Dashboard visualization (local web UI)
- [ ] Backup & restore tooling
- [ ] Documentation & architecture diagrams

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/ncanerozturk-cloud/worldv2.git
cd worldv2

# Start Qdrant (vector memory)
docker run -p 6333:6333 qdrant/qdrant

# Set up Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your Slack tokens and preferences

# Run the agent ecosystem
python main.py
```

---

## Project Structure

```
worldv2/
├── agents/
│   ├── health/          # Health & wellness agent
│   ├── sport/           # Fitness & training agent
│   ├── finance/         # Personal finance agent (roadmap)
│   └── career/          # Career development agent (roadmap)
├── memory/
│   └── qdrant/          # Vector memory configurations
├── integrations/
│   └── slack/           # Slack bot handlers
├── core/
│   ├── orchestrator.py  # Agent coordination logic
│   └── context.py       # Personal context management
├── data/                # Local data storage (gitignored)
├── main.py              # Entry point
└── README.md
```

---

## Why "worldv2"?

Because the first version of managing life was manual — spreadsheets, notes, fragmented apps, forgotten insights.

**worldv2** is the upgrade: a unified, intelligent, private system that learns, remembers, and acts.

---

## Author

**Caner Ozturk**
Building personal infrastructure for the AI age.

---

<div align="center">

*"If you can architect enterprise networks, you can architect your own intelligence stack."*

</div>
