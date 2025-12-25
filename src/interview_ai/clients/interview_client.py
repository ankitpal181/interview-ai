from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import List
from ..core.settings import settings
from ..core.cache import cache
from ..core.utilities import load_interview_rules, load_cache
from ..servers import interviewbot
from langgraph.types import Command


class InterviewClient:
    def __init__(self, interview_format: str = "coding") -> None:
        self.interview_rules = load_interview_rules(interview_format)
        self.max_questions = self.interview_rules.get(
            "no_of_questions", 10
        ) + settings.max_intro_questions

    def _check_answer_expiry(self, user_message: str, last_updated: str) -> str:
        if datetime.fromisoformat(last_updated) < datetime.now(timezone.utc) - timedelta(
            minutes=float(self.interview_rules.get("time_frame", 0)), seconds=float(5)
        ):
            return ""
        return user_message

    def start(self) -> dict:
        interview_id = str(uuid4())
        interview_config = {"configurable": {"thread_id": interview_id}}
        response = interviewbot.invoke({
            "messages": [{"role": "user", "content": "Start Interview"}],
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
                "messages": [{"role": "user", "content": user_message}],
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
        if not interview_config: raise ValueError("Interview config is required")

        cached_data = load_cache(interview_config['configurable']['thread_id'], interviewbot)
        response_map = {"evaluation": cached_data['last_message']['text']}

        for operation in operations_map:
            if operation.get("type") == "email":
                # check for name to whom email should be sent
                # check for the reciver's relation to this interview
                # check for email template [optional]
                pass
            elif operation.get("type") == "whatsapp":
                # check for name to whom whatsapp should be sent
                # check for the reciver's relation to this interview
                # check for whatsapp template [optional]
                pass
            elif operation.get("type") == "api":
                # check for api endpoint
                # check for api headers
                # check for api body template [
                # should have values to the keys and if value to be filled by ai,
                # then value should be a string starting with and ending with #Description#,
                # holding the detailed description of the value to be filled by ai]
                # check if a file needs to be uploaded [given or evaluation pdf]
                # check for api method
                pass
        
        return response_map

__all__ = [
    "InterviewClient"
]
