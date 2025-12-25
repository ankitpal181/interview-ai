from ..core.storage import Storage
from ..core.schemas import InterviewState
from ..core.operators import (
    interview_perception_function, candidate_information_collection_function, question_generation_function,
    answer_collection_function, evaluation_function, tool_node, reporting_function, reporting_tool_node,
    phase_router_function
)
from ..core.utilities import custom_tools_condition
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition


# Graph
graph = StateGraph(InterviewState)

# Graph Nodes
graph.add_node("perception_node", interview_perception_function)
graph.add_node("candidate_information_collection_node", candidate_information_collection_function)
graph.add_node("question_generation_node", question_generation_function)
graph.add_node("answer_collection_node", answer_collection_function)
graph.add_node("evaluation_node", evaluation_function)
graph.add_node("execution_tools", tool_node)
graph.add_node("reporting_node", reporting_function)
graph.add_node("tools", reporting_tool_node)

# Graph Edges
graph.add_edge(START, "candidate_information_collection_node")
graph.add_conditional_edges("candidate_information_collection_node", phase_router_function)
# Segment 1
graph.add_edge("perception_node", "question_generation_node")
graph.add_conditional_edges("question_generation_node", custom_tools_condition)
graph.add_edge("execution_tools", "question_generation_node")
graph.add_conditional_edges("answer_collection_node", phase_router_function)
graph.add_edge("evaluation_node", END)
# Segment 2
graph.add_conditional_edges("reporting_node", tools_condition)
graph.add_edge("tools", "reporting_node")

# Compile Graph
interviewbot = graph.compile(Storage("database").storage)
