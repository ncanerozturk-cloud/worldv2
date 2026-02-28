import os
import re
import logging
from typing import Optional

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from memory.qdrant_client import QdrantMemory
from memory.file_ingestor import FileIngestor
from agents.health_agent import HealthSportAgent

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Channel routing — map Slack channel names to agents
# ---------------------------------------------------------------------------
CHANNEL_MAP: dict = {}

# ---------------------------------------------------------------------------
# Initialise core components
# ---------------------------------------------------------------------------
log.info("Initialising Qdrant memory...")
memory = QdrantMemory()
ingestor = FileIngestor(memory)

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


SLACK_MAX_LEN = 3900


def split_message(text: str) -> list:
    """Split a long message into chunks <= SLACK_MAX_LEN, breaking on newlines."""
    if len(text) <= SLACK_MAX_LEN:
        return [text]

    chunks = []
    while text:
        if len(text) <= SLACK_MAX_LEN:
            chunks.append(text)
            break
        # Find the last newline within the limit
        split_at = text.rfind("\n", 0, SLACK_MAX_LEN)
        if split_at == -1:
            # No newline found — split at last space
            split_at = text.rfind(" ", 0, SLACK_MAX_LEN)
        if split_at == -1:
            # No space either — hard cut
            split_at = SLACK_MAX_LEN
        chunks.append(text[:split_at].rstrip())
        text = text[split_at:].lstrip()

    return chunks


def resolve_agent(channel_id: str, client) -> Optional[HealthSportAgent]:
    """Return the agent assigned to this channel, or None if unrecognised."""
    try:
        info = client.conversations_info(channel=channel_id)
        channel_name = info["channel"]["name"]
        return CHANNEL_MAP.get(channel_name)
    except Exception as e:
        log.warning(f"Could not resolve channel name for {channel_id}: {e}")
        return None


# ---------------------------------------------------------------------------
# Message handler
# ---------------------------------------------------------------------------
@app.event("message")
def handle_message(event, say, client):
    """Route incoming Slack messages to the appropriate agent."""
    log.info(f"[EVENT] message received: {event}")

    bot_id = event.get("bot_id")
    subtype = event.get("subtype")
    if bot_id or subtype:
        log.info(f"[SKIP] Ignoring event — bot_id={bot_id}, subtype={subtype}")
        return

    raw_text = event.get("text", "")
    user_text = re.sub(r"<@[A-Z0-9]+>", "", raw_text).strip()
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
        for chunk in split_message(response):
            say(chunk)
    except Exception as e:
        log.error(f"[ERROR] Agent error: {e}", exc_info=True)
        say(f"Something went wrong: {e}")


@app.event("app_mention")
def handle_mention(event, say, client):
    """Catch direct @mentions."""
    log.info(f"[MENTION] event: {event}")
    handle_message(event, say, client)


# ---------------------------------------------------------------------------
# File ingestion handler
# ---------------------------------------------------------------------------
@app.event("file_shared")
def handle_file_shared(event, say, client):
    """Download and ingest files uploaded to Slack into Qdrant."""
    file_id = event.get("file_id")
    channel_id = event.get("channel_id")

    log.info(f"[FILE] Received file_shared event — file_id={file_id} channel={channel_id}")

    try:
        file_info_response = client.files_info(file=file_id)
        file_info = file_info_response["file"]
        file_name = file_info.get("name", "unknown")
        mimetype = file_info.get("mimetype", "")

        log.info(f"[FILE] Ingesting '{file_name}' ({mimetype})")

        bot_token = os.getenv("SLACK_BOT_TOKEN")
        count = ingestor.ingest_from_slack(file_info, bot_token)

        msg = f"✅ *{file_name}* ingested — {count} chunk(s) saved to memory."
        log.info(f"[FILE] {msg}")

        if channel_id:
            client.chat_postMessage(channel=channel_id, text=msg)

    except Exception as e:
        log.error(f"[FILE] Ingestion failed: {e}", exc_info=True)
        if channel_id:
            client.chat_postMessage(channel=channel_id, text=f"❌ File ingestion failed: {e}")


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------
@app.error
def handle_error(error, body):
    log.error(f"[BOLT ERROR] {error} | body: {body}", exc_info=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    log.info("Starting worldv2...")
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
