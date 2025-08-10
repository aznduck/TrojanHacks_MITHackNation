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
        self._agent_outputs = {}  # Store agent outputs by deployment_id
        self._callbacks = {}
        self._agent_outputs = {}

    def register_callback(self, deployment_id: str, callback_url: str):
        urls = self._callbacks.setdefault(deployment_id, set())
        urls.add(callback_url)
    
    def store_agent_outputs(self, deployment_id: str, agent_outputs: dict):
        """Store agent outputs for a deployment"""
        self._agent_outputs[deployment_id] = agent_outputs
        
        # Also persist to MongoDB if available
        try:
            _mongo.agent_outputs.replace_one(
                {"deployment_id": deployment_id},
                {
                    "deployment_id": deployment_id,
                    "agent_outputs": agent_outputs,
                    "timestamp": int(time.time())
                },
                upsert=True
            )
        except Exception:
            pass  # MongoDB not available, use in-memory only
    
    def get_agent_outputs(self, deployment_id: str) -> dict:
        """Get agent outputs for a deployment"""
        # Try MongoDB first
        try:
            doc = _mongo.agent_outputs.find_one({"deployment_id": deployment_id})
            if doc:
                return doc.get("agent_outputs", {})
        except Exception:
            pass
        
        # Fall back to in-memory
        return self._agent_outputs.get(deployment_id, {})

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
                # Ensure message has deployment_id for frontend
                callback_message = dict(message)
                callback_message.setdefault("deployment_id", deployment_id)
                callback_message.setdefault("ts", int(time.time()))
                
                asyncio.get_running_loop().create_task(_post_json(url, callback_message))
            except RuntimeError:
                # no loop; send synchronously
                try:
                    callback_message = dict(message)
                    callback_message.setdefault("deployment_id", deployment_id)
                    callback_message.setdefault("ts", int(time.time()))
                    _post_json_sync(url, callback_message)
                except Exception:
                    pass

    def get_events(self, deployment_id):
        return list(self._events.get(deployment_id, []))
    
    def store_agent_outputs(self, deployment_id, agent_outputs):
        """Store agent outputs for a deployment"""
        self._agent_outputs[deployment_id] = agent_outputs
        # Also persist to MongoDB if available
        if _mongo:
            try:
                doc = {
                    "deployment_id": deployment_id,
                    "agent_outputs": agent_outputs,
                    "stored_at": int(time.time())
                }
                _mongo.agent_outputs.replace_one(
                    {"deployment_id": deployment_id}, 
                    doc, 
                    upsert=True
                )
            except Exception:
                pass
    
    def get_agent_outputs(self, deployment_id):
        """Get agent outputs for a deployment"""
        # Try MongoDB first if available
        if _mongo:
            try:
                doc = _mongo.agent_outputs.find_one({"deployment_id": deployment_id})
                if doc:
                    return doc.get("agent_outputs", {})
            except Exception:
                pass
        # Fallback to in-memory storage
        return self._agent_outputs.get(deployment_id, {})


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

