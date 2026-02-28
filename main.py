import os
import logging
from typing import Optional

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from memory.qdrant_client import QdrantMemory
from agents.health_agent import HealthSportAgent

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Channel routing — map Slack channel names to agents
# ---------------------------------------------------------------------------
CHANNEL_MAP: dict[str, HealthSportAgent] = {}

# ---------------------------------------------------------------------------
# Initialise core components
# ---------------------------------------------------------------------------
log.info("Initialising Qdrant memory...")
memory = QdrantMemory()

log.info("Initialising Health & Sport Agent...")
agent = HealthSportAgent()

CHANNEL_MAP = {
    "md_health_agent":    agent,
    "coach_sport_agent":  agent,
}

# ---------------------------------------------------------------------------
# Slack app
# ---------------------------------------------------------------------------
app = App(token=os.getenv("SLACK_BOT_TOKEN"))


def resolve_agent(channel_id: str, client) -> Optional[HealthSportAgent]:
    """Return the agent assigned to this channel, or None if unrecognised."""
    try:
        info = client.conversations_info(channel=channel_id)
        channel_name = info["channel"]["name"]
        return CHANNEL_MAP.get(channel_name)
    except Exception as e:
        log.warning(f"Could not resolve channel name for {channel_id}: {e}")
        return None


@app.event("message")
def handle_message(event, say, client):
    """Route incoming Slack messages to the appropriate agent."""
    log.info(f"[EVENT] message received: {event}")

    bot_id = event.get("bot_id")
    subtype = event.get("subtype")
    if bot_id or subtype:
        log.info(f"[SKIP] Ignoring event — bot_id={bot_id}, subtype={subtype}")
        return

    user_text = event.get("text", "").strip()
    channel_id = event.get("channel")
    user_id = event.get("user")

    log.info(f"[MSG] user={user_id} channel={channel_id} text={user_text[:120]!r}")

    if not user_text:
        log.info("[SKIP] Empty message text.")
        return

    routed_agent = resolve_agent(channel_id, client)

    if routed_agent is None:
        log.warning(f"[ROUTE] No agent mapped for channel {channel_id} — ignoring.")
        return

    log.info(f"[ROUTE] Dispatching to {routed_agent.__class__.__name__}")

    try:
        response = routed_agent.chat(user_text)
        log.info(f"[REPLY] {response[:120]!r}")
        say(response)
    except Exception as e:
        log.error(f"[ERROR] Agent error: {e}", exc_info=True)
        say(f"Something went wrong: {e}")


@app.event("app_mention")
def handle_mention(event, say, client):
    """Catch direct @mentions — useful for debugging event delivery."""
    log.info(f"[MENTION] event: {event}")
    handle_message(event, say, client)


@app.error
def handle_error(error, body):
    """Log any unhandled Slack Bolt errors."""
    log.error(f"[BOLT ERROR] {error} | body: {body}", exc_info=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    log.info("Starting worldv2...")
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
