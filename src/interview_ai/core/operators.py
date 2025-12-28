import json
from .llms import Model
from .schemas import InterviewState, QuestionsSchema, EvaluationSchema, ReportingSchema
from .prompts import INTERVIEWBOT_PROMPT, REPORTING_PROMPT, REPORTING_PROMPT_MAP
from .tools import search_internet, generate_csv_tool, generate_pdf_tool, call_api_tool, user_tools
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt


# InterviewBot AI instances
questioner_model = Model(tools = [], output_schema = QuestionsSchema)
evaluator_model = Model(tools = [], output_schema = EvaluationSchema)
reporting_model = Model(tools = [], output_schema = ReportingSchema)
questioner_tools_operator = Model(tools = [search_internet, *user_tools])
evaluator_tools_operator = Model(tools = user_tools)
reporting_tools_operator = Model(tools = [generate_csv_tool, generate_pdf_tool, call_api_tool, *user_tools])


# Graph Node Operators/Functions
execution_tool_node = ToolNode([search_internet, *user_tools])
reporting_tool_node = ToolNode([generate_csv_tool, generate_pdf_tool, call_api_tool, *user_tools])


# InterviewBot Functions
def candidate_information_collection_function(state: InterviewState) -> dict:
    """
    Candidate information collection to feed into system level prompt and
    provide the LLM with the required context.
    
    Args:
        state (InterviewState): Current state of the interview.
    
    Returns:
        dict: Updated state of the interview.
    """
    if state.get("phase") == "reporting": return state

    user_information = state.get("candidate_information", {})
    phase = "introduction"

    if "name" not in user_information:
        user_information["name"] = interrupt("Please enter your full name")
    elif "role" not in user_information:
        user_information["role"] = interrupt("Job role you want to interview for")
    elif "companies" not in user_information:
        user_information["companies"] = interrupt(
            "Please enter comma separated names of companies you prefer"
        )
        phase = "execution"

    return {
        "messages": [HumanMessage(json.dumps(user_information))],
        "candidate_information": user_information,
        "phase": phase
    }

def question_generation_function(state: InterviewState) -> dict:
    """
    Generate questions based on the information provided by the candidate.
    
    Args:
        state (InterviewState): Current state of the interview.
    
    Returns:
        dict: Updated state of the interview.
    """
    messages = state["messages"]
    questions_data = questioner_tools_operator.model.invoke(messages)

    if hasattr(questions_data, "tool_calls") and len(questions_data.tool_calls) > 0:
        return {"messages": [questions_data]}
    else:
        messages.append(questions_data)

    questions = questioner_model.model.invoke(messages)
    questions_json = questions.model_dump_json(indent = 2)

    return {"messages": [AIMessage(questions_json)], "questions": questions.questions}

def answer_collection_function(state: InterviewState) -> dict:
    """
    Collect answers from the candidate, one question at a time.
    
    Args:
        state (InterviewState): Current state of the interview.
    
    Returns:
        dict: Updated state of the interview.
    """
    questions = state["questions"]
    answers = state.get("answers", [])
    question = questions[len(answers)]
    answer = {"question": question.question, "answer": interrupt(question)}

    if len(answers) + 1 < len(questions):
        return {"answers": answers + [answer], "phase": "q&a"}
    else:
        return {
            "messages": [HumanMessage(json.dumps(answers + [answer]))],
            "answers": answers + [answer],
            "phase": "evaluation"
        }

def evaluation_function(state: InterviewState) -> dict:
    """
    Evaluate the candidate's answers and provide detailed feedback.
    
    Args:
        state (InterviewState): Current state of the interview.
    
    Returns:
        dict: Updated state of the interview.
    """
    messages = state["messages"]
    evaluation = evaluator_model.model.invoke(messages)
    evaluation_json = evaluation.model_dump_json(indent = 2)

    return {"messages": [AIMessage(evaluation_json)]}

def interview_perception_function(state: InterviewState) -> dict:
    """
    Collect all the information required for the Agent, from multiple sources and
    inject system level context to shape the LLM responses.
    
    Args:
        state (InterviewState): Current state of the interview.
    
    Returns:
        dict: Updated state of the interview.
    """
    rules = state["rules"]
    user_information = state["candidate_information"]
    system_prompt = SystemMessage(INTERVIEWBOT_PROMPT.format(
        role=user_information["role"],
        companies=user_information["companies"],
        time_frame=rules.get("time_frame"),
        no_of_questions=rules.get("no_of_questions"),
        questions_type=rules.get("questions_type")
    ))

    if system_prompt: state["messages"].insert(0, system_prompt)

    return state

def phase_router_function(state: InterviewState) -> str:
    """
    Route the agent's workflow to the appropriate phase based node,
    using the current state.
    
    Args:
        state (InterviewState): Current state of the interview.
    
    Returns:
        str: Name of the node to be executed.
    """
    if state.get("phase") == "reporting": return "reporting_perception_node"
    elif state.get("phase") == "introduction": return "candidate_information_collection_node"
    elif state.get("phase") == "q&a": return "answer_collection_node"
    elif state.get("phase") == "evaluation": return "evaluation_node"
    else: return "perception_node"

def reporting_function(state: InterviewState) -> dict:
    """
    Generate reports like evaluation PDFs, email content, message content using feedback data.
    
    Args:
        state (InterviewState): Current state of the interview.
    
    Returns:
        dict: Updated state of the interview.
    """
    messages = state["messages"]
    response_data = reporting_tools_operator.model.invoke(messages)

    if hasattr(response_data, "tool_calls") and len(response_data.tool_calls) > 0:
        return {"messages": [response_data]}
    else:
        messages.append(response_data)

    response = reporting_model.model.invoke(messages)
    response_json = response.model_dump_json(indent = 2)

    return {"messages": [AIMessage(response_json)]}

def reporting_perception_function(state: InterviewState) -> dict:
    """
    Collect all the information required by the Agent for reporting, from multiple sources and
    inject system level context to shape the LLM responses.
    
    Args:
        state (InterviewState): Current state of the interview.
    
    Returns:
        dict: Updated state of the interview.
    """
    messages = state["messages"]
    reporting_data = json.loads(messages[-1].content)
    system_prompt = SystemMessage(REPORTING_PROMPT.format(
        pdf=REPORTING_PROMPT_MAP.get("pdf") if "attachment" in reporting_data else "",
        email=REPORTING_PROMPT_MAP.get("email") if "email" in reporting_data else "",
        whatsapp=REPORTING_PROMPT_MAP.get("whatsapp") if "whatsapp" in reporting_data else "",
        description_value=REPORTING_PROMPT_MAP.get("description_value") if "description_value" in reporting_data else ""
    ))

    if system_prompt: state["messages"].insert(-1, system_prompt)

    return state
