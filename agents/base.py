import json
from abc import ABC, abstractmethod
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic


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
        result = executor.invoke(
            {
                "input": instruction,
                "context": context_json,
                "agent_name": self.name,
                "agent_description": self.description,
            }
        )
        return str(result.get("output", ""))

    def _merge_delta_into_context(self, *, delta_json, context):
        """Merge JSON delta; fallback to `last_message`."""
        try:
            delta = json.loads(delta_json)
            if not isinstance(delta, dict):
                raise ValueError("Agent output JSON must be an object")
            new_context = {**context, **delta}
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


