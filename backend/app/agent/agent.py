"""Give-It-A-Summary agent utilities module."""

from langgraph.graph import Graph

from ..tools.extract import extract_text_tool
from ..tools.summarize import summarize_text_tool

graph = Graph()

graph.add_node("extract", extract_text_tool)
graph.add_node("summarize", summarize_text_tool)

graph.add_edge("extract", "summarize")
