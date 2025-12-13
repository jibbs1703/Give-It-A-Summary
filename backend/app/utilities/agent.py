"""Give-It-A-Summary agent utilities module."""

from langgraph.graph import Graph

from .extract import extract_text_tool
from .summarize import summarize_text_tool

graph = Graph()

graph.add_node("extract", extract_text_tool)
graph.add_node("summarize", summarize_text_tool)

graph.add_edge("extract", "summarize")
