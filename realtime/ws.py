import asyncio


class ConnectionManager:
    def __init__(self):
        self._rooms = {}
        self._events = {}

    async def connect(self, deployment_id, websocket):
        await websocket.accept()
        self._rooms.setdefault(deployment_id, set()).add(websocket)

    def disconnect(self, deployment_id, websocket):
        room = self._rooms.get(deployment_id)
        if not room:
            return
        room.discard(websocket)
        if not room:
            self._rooms.pop(deployment_id, None)

    async def broadcast(self, deployment_id, message):
        buf = self._events.setdefault(deployment_id, [])
        buf.append(message)
        if len(buf) > 500:
            self._events[deployment_id] = buf[-500:]
        room = self._rooms.get(deployment_id, set())
        dead = []
        for ws in list(room):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            room.discard(ws)
        if not room and deployment_id in self._rooms:
            self._rooms.pop(deployment_id, None)

    def get_events(self, deployment_id):
        return list(self._events.get(deployment_id, []))


manager = ConnectionManager()


def broadcast(deployment_id, message):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast(deployment_id, message))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(manager.broadcast(deployment_id, message))
        finally:
            loop.close()


