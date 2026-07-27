from __future__ import annotations

import asyncio
from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class ChatHub:
    def __init__(self) -> None:
        self._rooms: dict[UUID, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, thread_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._rooms[thread_id].add(websocket)

    def disconnect(self, thread_id: UUID, websocket: WebSocket) -> None:
        room = self._rooms.get(thread_id)
        if not room:
            return
        room.discard(websocket)
        if not room:
            self._rooms.pop(thread_id, None)

    async def broadcast(self, thread_id: UUID, payload: dict) -> None:
        room = list(self._rooms.get(thread_id, set()))
        dead: list[WebSocket] = []
        for ws in room:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(thread_id, ws)


chat_hub = ChatHub()
