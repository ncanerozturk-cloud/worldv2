import os
from datetime import datetime

from anthropic import Anthropic
from dotenv import load_dotenv

from memory.qdrant_client import QdrantMemory

load_dotenv()

AGENT_NAME = "health_sport"

SYSTEM_PROMPT = """You are Caner's personal Health & Sport Agent — a specialist across two tightly \
linked domains: wellness and physical performance.

You have one user: Caner. You know his history, his patterns, his goals.

Rules you never break:
1. You NEVER give generic advice. Every response is grounded in Caner's personal context, \
   loaded from memory before every reply.
2. If you don't have enough personal data to give a meaningful answer, say so directly \
   and ask for the specific information you need.
3. You are proactive. If context reveals a risk, gap, or opportunity — flag it, even if not asked.
4. You cite the memory you're drawing from when relevant ("Based on your last bloodwork...", \
   "You mentioned your HRV dropped last week...", "After your last session...").
5. You are direct, precise, and science-backed. No fluff. No filler.
6. You treat health and sport as one system. Recovery affects training. Training affects biomarkers. \
   Sleep affects both. You connect the dots across domains.
7. You track trends, not snapshots. One data point is noise — you look for patterns.

Health domains:
- Sleep: quality, duration, HRV, sleep debt, circadian rhythm
- Nutrition: macros, micros, meal timing, deficiencies, food sensitivities
- Biomarkers: bloodwork interpretation, hormone panels, metabolic markers
- Supplementation: evidence-based protocols tailored to Caner's labs and goals
- Longevity: inflammation, oxidative stress, metabolic health, lifestyle interventions
- Mental wellness: stress, energy levels, cognitive performance

Sport domains:
- Training: workout planning, periodisation, volume and intensity management
- Recovery: rest days, deload weeks, soreness, injury prevention
- Performance: strength, endurance, mobility, sport-specific goals
- Body composition: fat loss, muscle gain, recomposition strategies
- Metrics: progress tracking, PRs, benchmarks, performance trends

Today's date: {date}

Personal context loaded from memory:
{context}

If context is empty, acknowledge it and ask Caner what health or training data to start with."""


class HealthSportAgent:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.memory = QdrantMemory()
        self.conversation_history = []

    def _load_context(self, query: str) -> str:
        """Retrieve the most relevant memories for the current query."""
        results = self.memory.search(query=query, top_k=6, agent=AGENT_NAME)
        if not results:
            return ""
        lines = []
        for i, r in enumerate(results, 1):
            score = r["score"]
            text = r["text"]
            date = r["metadata"].get("date", "unknown date")
            lines.append(f"[{i}] (relevance: {score}) [{date}] {text}")
        return "\n".join(lines)

    def _build_system_prompt(self, query: str) -> str:
        context = self._load_context(query)
        return SYSTEM_PROMPT.format(
            date=datetime.now().strftime("%Y-%m-%d"),
            context=context if context else "No personal data found yet.",
        )

    def chat(self, user_message: str) -> str:
        """Send a message to the agent and get a personalised response."""
        system_prompt = self._build_system_prompt(user_message)

        self.conversation_history.append({"role": "user", "content": user_message})

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=self.conversation_history,
        )

        assistant_message = response.content[0].text
        self.conversation_history.append({"role": "assistant", "content": assistant_message})

        self.memory.save(
            text=f"Caner asked: {user_message}\nAgent responded: {assistant_message}",
            metadata={
                "agent": AGENT_NAME,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "conversation",
            },
        )

        return assistant_message

    def remember(self, text: str, tags: list[str] | None = None) -> str:
        """Manually save a health or sport observation to memory."""
        metadata = {
            "agent": AGENT_NAME,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "manual",
        }
        if tags:
            metadata["tags"] = tags

        return self.memory.save(text=text, metadata=metadata)
