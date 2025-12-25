import json
from .llms import Model
from .schemas import InterviewState, QuestionsSchema, EvaluationSchema
from .prompts import INTERVIEWBOT_PROMPT
from .tools import search_internet, generate_csv_tool, generate_pdf_tool, user_tools
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt


# InterviewBot AI instances
questioner_model = Model(tools = [search_internet, *user_tools], output_schema = QuestionsSchema)
evaluator_model = Model(tools = user_tools, output_schema = EvaluationSchema)
reporting_model = Model(tools = [generate_csv_tool, generate_pdf_tool, *user_tools])


# Graph Node Operators/Functions
tool_node = ToolNode(reporting_model.tools)
reporting_tool_node = ToolNode(reporting_model.tools)


# InterviewBot Functions
def candidate_information_collection_function(state: InterviewState) -> dict:
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
    messages = state["messages"]
    questions = questioner_model.model.invoke(messages)
    questions_json = questions.model_dump_json(indent = 2)

    return {"messages": [AIMessage(questions_json)], "questions": questions.questions}

def answer_collection_function(state: InterviewState) -> dict:
    questions = state["questions"]
    answers = state.get("answers", [])
    question = questions[len(answers)]
    answer = {"question": question.question, "answer": interrupt(question)}

    if len(answers) + 1 < len(questions):
        return {"answers": answers + [answer], "phase": "q&a"}
    else:
        return {
            "messages": [HumanMessage(json.dumps(answers))],
            "answers": answers + [answer],
            "phase": "evaluation"
        }

def evaluation_function(state: InterviewState) -> dict:
    messages = state["messages"]
    evaluation = evaluator_model.model.invoke(messages)
    evaluation_json = evaluation.model_dump_json(indent = 2)

    return {"messages": [AIMessage(evaluation_json)]}

def interview_perception_function(state: InterviewState) -> dict:
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
    if state.get("phase") == "reporting": return "reporting_node"
    elif state.get("phase") == "introduction": return "candidate_information_collection_node"
    elif state.get("phase") == "q&a": return "answer_collection_node"
    elif state.get("phase") == "evaluation": return "evaluation_node"
    else: return "perception_node"

def reporting_function(state: InterviewState) -> dict:
    messages = state["messages"]
    response = reporting_model.model.invoke(messages)
    return {"messages": [response]}
