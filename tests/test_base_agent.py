import os
import pytest

from agents.base import BaseAgent

class Tool:
    def __init__(self, name, description, func):
        self.name = name
        self.description = description
        self.func = func


class EchoAgent(BaseAgent):
    def setup_tools(self):
        def echo_tool(text: str) -> str:
            return f"echo:{text}"

        return [
            Tool(
                name="echo",
                description="Echo back the given text",
                func=echo_tool,
            )
        ]

    def run(self, context):
        return {**context, "echo": True}


def test_base_agent_instantiation():
    agent = EchoAgent(name="echo", description="simple")
    assert agent.name == "echo"
    assert len(agent.tools) == 1


@pytest.mark.skip(reason="LLM invocation requires API key; smoke only")
def test_base_agent_invoke_without_key():
    os.environ.pop("OPENAI_API_KEY", None)
    agent = EchoAgent(name="echo", description="simple")
    context = {"a": 1}
    result = agent.run(context)
    assert result.get("echo") is True


