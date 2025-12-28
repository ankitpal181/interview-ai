import json
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import List
from ..core.settings import settings
from ..core.cache import cache
from ..core.utilities import load_interview_rules, load_cache
from ..servers import interviewbot
from langgraph.types import Command
from langchain_core.messages import HumanMessage


class InterviewClient:
    """
    InterviewClient is a class that provides a simple interface to interact with the interviewbot.
    """
    def __init__(self, interview_format: str = "coding") -> None:
        """
        Initialize the InterviewClient with the given interview format.

        Args:
            interview_format (str): The interview format to be used.

        Returns:
            None
        """
        self.interview_rules = load_interview_rules(interview_format)
        self.max_questions = self.interview_rules.get(
            "no_of_questions", 10
        ) + settings.max_intro_questions

    def _check_answer_expiry(self, user_message: str, last_updated: str) -> str:
        """
        Check if the answer is expired.

        Args:
            user_message (str): The user message to be checked.
            last_updated (str): The last updated time of the user message.

        Returns:
            str: The user message if it is not expired, otherwise an empty string.
        """
        if datetime.fromisoformat(last_updated) < datetime.now(timezone.utc) - timedelta(
            minutes=float(self.interview_rules.get("time_frame", 0)), seconds=float(5)
        ):
            return ""
        return user_message

    def start(self) -> dict:
        """
        Start the interview.

        Returns:
            dict: The interview configuration and initial interrupt message.
        """
        interview_id = str(uuid4())
        interview_config = {"configurable": {"thread_id": interview_id}}
        response = interviewbot.invoke({
            "messages": [HumanMessage(content="Start Interview")],
            "phase": "introduction",
            "rules": self.interview_rules
        }, interview_config)
        
        interrupt_message = response['__interrupt__'][0].value
        cached_data = {
            "last_message": {
                "text": response['__interrupt__'][0].value,
                "type": "interrupt"
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "count": 0
        }

        cache.set(interview_id, cached_data)
        return {
            "interview_config": interview_config,
            "message": interrupt_message
        }

    def next(self, interview_config: dict, user_message: str = "") -> dict:
        """
        Next step in the interview workflow. This function is the contact point to move/control
        the interview flow and submit user messages, with a timer + 5 seconds buffer,
        based on the interview rules.

        Args:
            interview_config (dict): The interview configuration.
            user_message (str): The user message to be processed.

        Returns:
            dict: The next message or "__end__" if the interview is over.
        """
        if not interview_config: raise ValueError("Interview config is required")

        cached_data = load_cache(interview_config['configurable']['thread_id'], interviewbot)

        if cached_data["count"] >= self.max_questions: return "__end__"

        if cached_data["last_message"]["type"] == "interrupt":
            user_message = self._check_answer_expiry(user_message, cached_data["last_updated"])
            response = interviewbot.invoke(
                Command(resume=user_message), interview_config
            )
        else:
            response = interviewbot.invoke({
                "messages": [HumanMessage(content=user_message)],
                "phase": "evaluation",
                "rules": self.interview_rules
            }, interview_config)
        
        if response and "__interrupt__" in response:
            cached_data["last_message"] = {
                "text": response['__interrupt__'][0].value,
                "type": "interrupt"
            }
        else:
            cached_data["last_message"] = {
                "text": response["messages"][-1].content,
                "type": "text"
            }
        
        cached_data["count"] += 1
        cached_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        cache.set(interview_config['configurable']['thread_id'], cached_data)

        return "__end__" if (
            cached_data["count"] >= self.max_questions
        ) else {"message": cached_data['last_message']['text']}

    def end(self, interview_config: dict, operations_map: List[dict] = []) -> dict:
        """
        End the interview and generate the response map containg evaluation dict and
        operations results. Each operation details are processed using LLMs and data will be
        generated. Keep in mind that actual emails or whatsapp messages will not be sent.

        Args:
            interview_config (dict): The interview configuration.
            operations_map (List[dict]): The operations to be performed, supported: email, whatsapp, api.
                                         Operation templates[can send multiple same type operations with different data]:
                                         {
                                            "type": "email",
                                            "receiver_name": "Jhon Doe",
                                            "receiver_relation_to_interview": "Candidate/Hiring Manager/HR",
                                            "template"[optional]: "html/json_string"
                                         }
                                         {
                                            "type": "whatsapp",
                                            "receiver_name": "Jhon Doe",
                                            "receiver_relation_to_interview": "Candidate/Hiring Manager/HR",
                                            "template"[optional]: "html/json_string"
                                         }
                                         {
                                            "type": "api",
                                            "endpoint": "https://example.com/api",
                                            "headers"[optional]: {
                                                "Content-Type": "application/json"
                                            },
                                            "body"[Keys depends upon your api]: {
                                                "name": "Jhon Doe",
                                                "evaluation": "evaluation string or dict",
                                                "good_fit_for_position"[
                                                    use #Description# to let AI fill the actual values based on description
                                                ]: "#Description# Name all the positions for which this candidate is good fit #Description#"
                                            },
                                            "attachment"[optional]: "path_to_file or use #Evaluation PDF# to attach evaluation PDF"
                                            "method"[optional]: "default POST"
                                         }

        Returns:
            dict: The response map containg evaluation dict and operations results.
        """
        if not interview_config: raise ValueError("Interview config is required")

        cached_data = load_cache(interview_config['configurable']['thread_id'], interviewbot)
        response_map = {"evaluation": cached_data['last_message']['text']}
        
        if not operations_map: return response_map
        user_message = {}

        for operation in operations_map:
            if operation.get("type") == "email":
                if "email" not in user_message:
                    user_message["email"] = []
                user_message["email"].append({
                    "receiver_name": operation.get("receiver_name"),
                    "receiver_relation_to_interview": operation.get("receiver_relation_to_interview"),
                    "template": operation.get("template")
                })
                user_message["attachment"] = "Generate Evaluation PDF"
            elif operation.get("type") == "whatsapp":
                if "whatsapp" not in user_message:
                    user_message["whatsapp"] = []
                user_message["whatsapp"].append({
                    "receiver_name": operation.get("receiver_name"),
                    "receiver_relation_to_interview": operation.get("receiver_relation_to_interview"),
                    "template": operation.get("template")
                })
                user_message["attachment"] = "Generate Evaluation PDF"
            elif operation.get("type") == "api":
                required_values = {"endpoint": operation.get("endpoint")}

                for key, value in operation.get("body", {}).items():
                    value = value.strip()

                    if value.startswith("#Description#") and value.endswith("#Description#"):
                        required_values[key] = value
                
                if "description_value" not in user_message:
                    user_message["description_value"] = []
                user_message["description_value"].append(required_values)

                if operation.get("attachment", "") == "#Evaluation PDF#":
                    user_message["attachment"] = "Generate Evaluation PDF"
        
        # Call llm for information
        response = interviewbot.invoke({
            "messages": [HumanMessage(content=json.dumps(user_message))],
            "phase": "reporting"
        }, interview_config)
        response_data = json.loads(response["messages"][-1].content)

        for operation in operations_map:
            if operation.get("type") == "api":
                message_to_call_api_tool = {
                    "endpoint": operation.get("endpoint"),
                    "headers": operation.get("headers", {}),
                    "body": operation.get("body", {}),
                    "attachment": response_data["pdf"]["file_path"] if (
                        operation.get("attachment", "") == "#Evaluation PDF#"
                    ) else operation.get("attachment"),
                    "method": operation.get("method", "POST")
                }

                for value in response_data["description_value"]:
                    if value["endpoint"] == operation.get("endpoint"):
                        message_to_call_api_tool["body"].update({
                            value["key"]: value["value"]
                        })

                api_response = interviewbot.invoke({
                    "messages": [HumanMessage(content=json.dumps(message_to_call_api_tool))],
                    "phase": "reporting"
                }, interview_config)
                api_response_data = json.loads(api_response["messages"][-1].content)

                if api_response_data["error_report"]:
                    response_map["api_errors"] = response_map.get("api_errors", [])
                    response_map["api_errors"].append(api_response_data["error_report"])
        
        response_map["operations_results"] = response_data
        return response_map

__all__ = [
    "InterviewClient"
]
