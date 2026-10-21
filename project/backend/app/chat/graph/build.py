"""The text-to-SQL chat graph (spec 7.1). One run per question; no checkpointer, because
``chat_turn`` is the only history.

    load_context -> generate -> route -+-> clarify -----------------------------> finalize
                      ^                +-> guard -> execute -> analyze -> finalize
                      |                     |          |
                      +------ repair <------+----------+  (failed attempt, generations left)

A reply that is not a valid draft also goes to repair; provider errors and the last failed
attempt go straight to finalize as errors.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.chat.graph.nodes import ChatNodes, after_execute, after_guard, route
from app.chat.graph.state import ChatDeps, ChatState


def build_chat_graph(deps: ChatDeps) -> CompiledStateGraph:
    nodes = ChatNodes(deps)
    graph = StateGraph(ChatState)
    graph.add_node("load_context", nodes.load_context)
    graph.add_node("generate", nodes.generate)
    graph.add_node("clarify", nodes.clarify)
    graph.add_node("guard", nodes.guard)
    graph.add_node("execute", nodes.execute)
    graph.add_node("repair", nodes.repair)
    graph.add_node("analyze", nodes.analyze)
    graph.add_node("finalize", nodes.finalize)

    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "generate")
    graph.add_conditional_edges("generate", route)
    graph.add_conditional_edges("guard", after_guard)
    graph.add_conditional_edges("execute", after_execute)
    graph.add_edge("repair", "generate")
    graph.add_edge("clarify", "finalize")
    graph.add_edge("analyze", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()
