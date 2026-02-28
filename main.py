import os
import logging

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
    "health": agent,
    "sport":  agent,
}

# ---------------------------------------------------------------------------
# Slack app
# ---------------------------------------------------------------------------
app = App(token=os.getenv("SLACK_BOT_TOKEN"))


def resolve_agent(channel_id: str, client) -> HealthSportAgent | None:
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
    if event.get("bot_id") or event.get("subtype"):
        return

    user_text = event.get("text", "").strip()
    channel_id = event.get("channel")

    if not user_text:
        return

    routed_agent = resolve_agent(channel_id, client)

    if routed_agent is None:
        log.info(f"No agent mapped for channel {channel_id} — ignoring.")
        return

    log.info(f"Message received: {user_text[:80]}")

    try:
        response = routed_agent.chat(user_text)
        say(response)
    except Exception as e:
        log.error(f"Agent error: {e}")
        say(f"Something went wrong: {e}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    log.info("Starting worldv2...")
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
