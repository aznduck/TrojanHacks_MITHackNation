import asyncio
import os
import time
import json
import urllib.request

_mongo = None
try:
    from pymongo import MongoClient  # type: ignore

    uri = os.getenv("MONGODB_URI")
    if uri:
        _mongo = MongoClient(uri)[os.getenv("MONGODB_DB", "agentops")]
except Exception:
    _mongo = None


class ConnectionManager:
    def __init__(self):
        self._events = {}
        self._callbacks = {}

    def register_callback(self, deployment_id: str, callback_url: str):
        urls = self._callbacks.setdefault(deployment_id, set())
        urls.add(callback_url)

    async def broadcast(self, deployment_id, message):
        buf = self._events.setdefault(deployment_id, [])
        buf.append(message)
        if len(buf) > 500:
            self._events[deployment_id] = buf[-500:]
        # persist to Mongo if available
        if _mongo:
            try:
                doc = dict(message)
                doc.setdefault("deployment_id", deployment_id)
                doc.setdefault("ts", int(time.time()))
                _mongo.events.insert_one(doc)
            except Exception:
                pass
        # post to registered webhook callbacks
        for url in list(self._callbacks.get(deployment_id, set())):
            try:
                asyncio.get_running_loop().create_task(_post_json(url, message))
            except RuntimeError:
                # no loop; send synchronously
                try:
                    _post_json_sync(url, message)
                except Exception:
                    pass

    def get_events(self, deployment_id):
        return list(self._events.get(deployment_id, []))


async def _post_json(url: str, payload: dict):
    await asyncio.to_thread(_post_json_sync, url, payload)


def _post_json_sync(url: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        method="POST",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as _:
            pass
    except Exception:
        pass


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

