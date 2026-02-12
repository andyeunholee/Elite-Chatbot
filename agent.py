import os
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# 1. Define State
class State(TypedDict):
    messages: Annotated[list, add_messages]

# 2. Define Tools
# Tavily Search Tool (Search Web)
tool = TavilySearchResults(max_results=5)
tools = [tool]

# 3. Define LLM (Gemini)
# Using gemini-2.0-flash for speed and performance.
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
llm_with_tools = llm.bind_tools(tools)

# 4. Define Nodes
def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# 5. Build Graph
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge("chatbot", END)

# Compile the graph
agent = graph_builder.compile()

if __name__ == "__main__":
    # Simple test
    print("Test run...")
    events = agent.stream(
        {"messages": [("user", "What is the current stock price of NVDA?")]},
        stream_mode="values",
    )
    for event in events:
        event["messages"][-1].pretty_print()
