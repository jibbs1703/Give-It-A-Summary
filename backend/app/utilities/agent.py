"""Give-It-A-Summary agent utilities module."""

from langgraph.graph import Graph

from .extract import extract_text_tool
from .summarize import summarize_text_tool

TOOLS = {
    "extract_text": extract_text_tool,
    "summarize_text": summarize_text_tool,
}

graph = Graph()

graph.add_node("extract", TOOLS["extract_text"])
graph.add_node("summarize", TOOLS["summarize_text"])

graph.add_edge("extract", "summarize")
