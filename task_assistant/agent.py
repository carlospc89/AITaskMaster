from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage, HumanMessage

from .tools import all_tools
from .logger_config import log

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

class Agent:
    def __init__(self, model, system=""):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_model)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges("llm", self.exists_action, {True: "action", False: END})
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile()
        self.tools = {t.name: t for t in all_tools}
        self.model = model.bind_tools(all_tools)
        log.info("Agent initialized successfully.")

    def exists_action(self, state: AgentState) -> bool:
        result = state["messages"][-1]
        action_exists = len(result.tool_calls) > 0
        log.info(f"Does an action exist? {action_exists}")
        return action_exists

    def call_model(self, state: AgentState):
        log.info("Calling the model...")
        messages = state["messages"]
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {"messages": [message]}

    def take_action(self, state: AgentState):
        tool_calls = state["messages"][-1].tool_calls
        results = []
        for t in tool_calls:
            log.info(f"Calling tool: {t['name']} with args: {t['args']}")
            result = self.tools[t["name"]].invoke(t["args"])
            results.append(ToolMessage(tool_call_id=t["id"], name=t["name"], content=str(result)))
        log.info("Returning to the model with tool results.")
        return {"messages": results}

    def get_prioritization(self, tasks_json: str, system_prompt: str) -> str:
        """Makes a one-off call to the model for a specific task like prioritization."""
        log.info("Requesting prioritization from the model...")
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=tasks_json)
        ]
        response = self.model.invoke(messages)
        return response.content