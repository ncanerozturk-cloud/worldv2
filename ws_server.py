import asyncio
import json
import logging
import threading
from typing import Optional

import websockets

log = logging.getLogger(__name__)

_ws_loop: Optional[asyncio.AbstractEventLoop] = None
_clients: set = set()


async def _handler(websocket):
    _clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        _clients.discard(websocket)


async def _broadcast(data: dict):
    if _clients:
        msg = json.dumps(data)
        await asyncio.gather(*[c.send(msg) for c in list(_clients)], return_exceptions=True)


def send_event(data: dict):
    """Thread-safe broadcast to all connected dashboard clients."""
    if _ws_loop and not _ws_loop.is_closed():
        asyncio.run_coroutine_threadsafe(_broadcast(data), _ws_loop)


def start(host: str = "localhost", port: int = 8765):
    """Start the WebSocket server in a background daemon thread."""
    global _ws_loop

    def _run():
        global _ws_loop
        _ws_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_ws_loop)

        async def _serve():
            async with websockets.serve(_handler, host, port):
                log.info(f"[WS] Dashboard server running on ws://{host}:{port}")
                await asyncio.Future()  # run forever

        _ws_loop.run_until_complete(_serve())

    threading.Thread(target=_run, daemon=True).start()
