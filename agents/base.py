import json
import time
from abc import ABC, abstractmethod
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.callbacks import BaseCallbackHandler
from langchain_anthropic import ChatAnthropic
from realtime.ws import broadcast as ws_broadcast


class BaseAgent(ABC):
    """Lightweight ReAct agent base."""

    def __init__(self, name, description, llm=None, max_iterations=10, temperature=0.0):
        self.name = name
        self.description = description
        self.llm = llm or ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=temperature)
        self.max_iterations = max_iterations
        self.tools = self.setup_tools()

    @abstractmethod
    def setup_tools(self):
        """Return tools."""
        raise NotImplementedError

    def _build_prompt(self):
        """Compact ReAct prompt."""

        template = (
            "You are {agent_name}: {agent_description}.\n"
            "You are part of a multi-agent deployment pipeline.\n"
            "Current context (JSON):\n{context}\n\n"
            "Follow ReAct:\n"
            "- Think step-by-step about what to do next.\n"
            "- Use tools when they help.\n"
            "- When done, output ONLY a compact JSON object with fields to merge into the context.\n"
            "Do not repeat unchanged fields.\n\n"
            "User request: {input}"
        )
        return PromptTemplate(input_variables=["input", "context", "agent_name", "agent_description"], template=template)

    def build_agent(self):
        """Build executor."""
        prompt = self._build_prompt()
        agent = create_react_agent(self.llm, self.tools, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            max_iterations=self.max_iterations,
            handle_parsing_errors=True,
            verbose=False,
        )
        return executor

    def _invoke(self, executor, *, instruction, context):
        """Invoke and return raw text output."""
        context_json = json.dumps(context, ensure_ascii=False)
        deployment_id = context.get("deployment_id")
        callbacks = None
        if deployment_id:
            callbacks = [
                _WSCallbackHandler(
                    deployment_id=deployment_id,
                    agent_name=self.name,
                )
            ]
        result = executor.invoke(
            {
                "input": instruction,
                "context": context_json,
                "agent_name": self.name,
                "agent_description": self.description,
            },
            config={"callbacks": callbacks} if callbacks else None,
        )
        return str(result.get("output", ""))

    def _merge_delta_into_context(self, *, delta_json, context):
        """Merge JSON delta; fallback to `last_message`."""
        try:
            delta = json.loads(delta_json)
            if not isinstance(delta, dict):
                raise ValueError("Agent output JSON must be an object")
            new_context = {**context, **delta}
            deployment_id = context.get("deployment_id")
            if deployment_id:
                try:
                    ws_broadcast(
                        deployment_id,
                        {
                            "type": "trace",
                            "stage": self.name.lower(),
                            "subtype": "agent_delta",
                            "delta": delta,
                            "ts": int(time.time()),
                        },
                    )
                except Exception:
                    pass
            return new_context
        except Exception:
            new_context = dict(context)
            new_context["last_message"] = delta_json
            return new_context

    def run(self, context):
        """Run and return updated context."""
        instruction = (
            "Review the context and perform your role. Use tools if needed. "
            "Return only the minimal JSON fields to add or update."
        )
        executor = self.build_agent()
        raw = self._invoke(executor, instruction=instruction, context=context)
        return self._merge_delta_into_context(delta_json=raw, context=context)



def _redact(value: str) -> str:
    if not isinstance(value, str):
        return value
    to_mask = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "VERCEL_TOKEN",
        "GITHUB_TOKEN",
    ]
    for key in to_mask:
        secret = None
        try:
            import os

            secret = os.getenv(key)
        except Exception:
            secret = None
        if secret and secret in value:
            value = value.replace(secret, f"***{key}***")
    return value


class _WSCallbackHandler(BaseCallbackHandler):
    def __init__(self, deployment_id: str, agent_name: str):
        self.deployment_id = deployment_id
        self.agent_name = agent_name

    def _emit(self, payload: dict):
        try:
            payload.setdefault("type", "trace")
            payload.setdefault("stage", self.agent_name.lower())
            payload.setdefault("ts", int(time.time()))
            ws_broadcast(self.deployment_id, payload)
        except Exception:
            pass

    def on_llm_start(self, serialized, prompts, **kwargs):
        safe_prompts = [_redact(p) for p in (prompts or [])]
        model = None
        try:
            model = serialized.get("kwargs", {}).get("model")
        except Exception:
            model = None
        self._emit({
            "subtype": "llm_start",
            "model": model,
            "input": safe_prompts,
        })

    def on_llm_end(self, response, **kwargs):
        try:
            texts = []
            for gen in response.generations:
                for g in gen:
                    if hasattr(g, "text"):
                        texts.append(_redact(g.text))
            self._emit({
                "subtype": "llm_end",
                "output": texts,
            })
        except Exception:
            self._emit({"subtype": "llm_end"})

    def on_tool_start(self, serialized, input_str, **kwargs):
        name = None
        try:
            name = serialized.get("name")
        except Exception:
            name = None
        self._emit({
            "subtype": "tool_start",
            "tool": name,
            "input": _redact(input_str) if isinstance(input_str, str) else input_str,
        })

    def on_tool_end(self, output, **kwargs):
        self._emit({
            "subtype": "tool_end",
            "output": _redact(output) if isinstance(output, str) else output,
        })

