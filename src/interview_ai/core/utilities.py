import os, json, importlib
from typing import Any
from .schemas import InterviewState
from .cache import cache


# Graph Node Utilities(Planning Modules)
def custom_tools_condition(state: InterviewState, messages_key: str = "messages") -> str:
    """
    Custom tools condition function to check if execution tools are required.

    Args:
        state (InterviewState): State object.
        messages_key (str): Key to access messages in the state.
    
    Returns:
        str: "execution_tools" if the message contains tool calls, otherwise "answer_collection_node".
    """
    ai_message = None

    if isinstance(state, list):
        ai_message = state[-1]
    elif isinstance(state, dict) and (messages := state.get(messages_key, [])) or (
        messages := getattr(state, messages_key, [])
    ):
        ai_message = messages[-1]
    else:
        msg = f"No messages found in input state to tool_edge: {state}"
        raise ValueError(msg)

    if (hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0):
        return "execution_tools"
    
    return "answer_collection_node"

def load_interview_rules(format: str = "coding") -> dict:
    """
    Load interview rules from the interview_rules.json file.

    Args:
        format (str): Format of the interview rules to be loaded.
    
    Returns:
        dict: Interview rules.
    """
    root_dir = os.getcwd()
    json_path = os.path.join(root_dir, "interview_ai", "interview_rules.json")

    with open(json_path, "r") as file:
        interview_rules = json.load(file)
    
    return interview_rules.get(format, {})

def load_cache(thread_id: str, interviewbot: Any) -> dict:
    """
    Load cached data from the cache module for given thread, if not found
    fetch the latest graph state and use it to populate the cache.

    Args:
        thread_id (str): Thread ID of the interview, used for cache lookup.
        interviewbot (Any): InterviewBot instance, used to fetch the latest graph state.
    
    Returns:
        dict: Cached data.
    """
    cached_data = cache.get(thread_id)

    if cached_data is None:
        config = {"configurable": {"thread_id": thread_id}}
        latest_graph_state = interviewbot.get_state(config)
        cached_data = {
            "last_message": {},
            "last_updated": latest_graph_state.created_at,
            "count": len(latest_graph_state.values.get("candidate_information", {})) + len(
                latest_graph_state.values.get("answers", [])
            )
        }

        if "__interrupt__" in latest_graph_state.values:
            cached_data["last_message"]["type"] = "interrupt"
            cached_data["last_message"]["text"] = latest_graph_state.values['__interrupt__'][0].value
        else:
            cached_data["last_message"]["type"] = "text"
            cached_data["last_message"]["text"] = latest_graph_state.values["messages"][-1].content
        
        cache.set(thread_id, cached_data)

    return cached_data

def fetch_user_tools() -> list:
    """
    Fetch user defined custom tools from the tools.py file.

    Returns:
        list: List of user tools.
    """
    root_dir = os.getcwd()
    tools_path = os.path.join(root_dir, "interview_ai", "tools.py")

    if not os.path.exists(tools_path): return []

    try:
        spec = importlib.util.spec_from_file_location("user_tools", tools_path)
        if spec is None or spec.loader is None: return []
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, 'user_tools', [])
    except Exception:
        return []
