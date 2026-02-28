import os
import json
import logging
from datetime import datetime
from typing import Optional

from anthropic import Anthropic
from dotenv import load_dotenv

from memory.qdrant_client import QdrantMemory

load_dotenv()

log = logging.getLogger(__name__)

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

FACT_EXTRACTION_PROMPT = """You are a personal data extraction assistant. Extract all concrete personal facts \
about Caner from the conversation below.

Include: health metrics, biomarkers, symptoms, diagnoses, medications, supplements, training data, \
nutrition habits, sleep data, body composition, goals, injuries, lifestyle details.

Return ONLY a valid JSON array of strings. Each string is one specific fact.
If no personal facts exist, return an empty array: []

Examples of good facts:
- "Caner's vitamin D level is 28 ng/mL as of 2026-02"
- "Caner takes magnesium glycinate 400mg before sleep"
- "Caner ran 8km on 2026-02-28, felt strong"
- "Caner's goal is to lose 5kg by summer 2026"
- "Caner sleeps around 6.5 hours per night"

Conversation:
User: {user_message}
Agent: {agent_response}

JSON array of facts:"""


class HealthSportAgent:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.memory = QdrantMemory()
        self.conversation_history = []

    def _load_context(self, query: str) -> str:
        """
        Retrieve context from two sources:
        1. Semantic search over all memories (query-relevant)
        2. All recently ingested file chunks (always included, regardless of semantic score)
        """
        lines = []

        # 1. Semantic search
        results = self.memory.search(query=query, top_k=6, agent=AGENT_NAME)
        if results:
            lines.append("=== Relevant Memories ===")
            for i, r in enumerate(results, 1):
                date = r["metadata"].get("date", "unknown date")
                lines.append(f"[{i}] (score: {r['score']}) [{date}] {r['text']}")

        # 2. Recently ingested files (always surfaced so uploads are never missed)
        ingested = self.memory.get_recent_ingested(limit=10)
        if ingested:
            lines.append("\n=== Uploaded Documents ===")
            for r in ingested:
                source = r["metadata"].get("file_name") or r["metadata"].get("source_file", "unknown")
                date = r["metadata"].get("date", "unknown date")
                lines.append(f"[{source}] [{date}] {r['text']}")

        return "\n".join(lines)

    def _build_system_prompt(self, query: str) -> str:
        context = self._load_context(query)
        return SYSTEM_PROMPT.format(
            date=datetime.now().strftime("%Y-%m-%d"),
            context=context if context else "No personal data found yet.",
        )

    def _extract_and_save_facts(self, user_message: str, agent_response: str):
        """
        Use Claude Haiku to extract personal facts from the exchange and
        save each one individually to Qdrant.
        """
        try:
            extraction = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                messages=[{
                    "role": "user",
                    "content": FACT_EXTRACTION_PROMPT.format(
                        user_message=user_message,
                        agent_response=agent_response,
                    ),
                }],
            )
            raw = extraction.content[0].text.strip()

            # Parse JSON — handle markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            facts = json.loads(raw)

            if not isinstance(facts, list):
                return

            today = datetime.now().strftime("%Y-%m-%d")
            for fact in facts:
                if fact and isinstance(fact, str):
                    self.memory.save(
                        text=fact,
                        metadata={
                            "agent": AGENT_NAME,
                            "date": today,
                            "type": "auto_fact",
                        },
                    )
            if facts:
                log.info(f"[AUTO-SAVE] Extracted and saved {len(facts)} personal facts")

        except Exception as e:
            log.warning(f"[AUTO-SAVE] Fact extraction failed (non-critical): {e}")

    def chat(self, user_message: str) -> str:
        """Send a message to the agent and get a personalised response."""
        system_prompt = self._build_system_prompt(user_message)

        self.conversation_history.append({"role": "user", "content": user_message})

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=self.conversation_history,
        )

        assistant_message = response.content[0].text
        self.conversation_history.append({"role": "assistant", "content": assistant_message})

        # Save full conversation exchange
        self.memory.save(
            text=f"Caner asked: {user_message}\nAgent responded: {assistant_message}",
            metadata={
                "agent": AGENT_NAME,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "conversation",
            },
        )

        # Auto-extract and save individual personal facts
        self._extract_and_save_facts(user_message, assistant_message)

        return assistant_message

    def remember(self, text: str, tags: Optional[list] = None) -> str:
        """Manually save a health or sport observation to memory."""
        metadata = {
            "agent": AGENT_NAME,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "manual",
        }
        if tags:
            metadata["tags"] = tags

        return self.memory.save(text=text, metadata=metadata)
