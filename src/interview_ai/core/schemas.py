from typing import Annotated, TypedDict, List
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


# Graph state and output schemas
class InterviewState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    questions: list
    answers: list
    candidate_information: dict
    rules: dict
    phase: str

class QuestionsItemSchema(BaseModel):
    question: str = Field(
        description = "The question for which the candidate have to give answer"
    )
    type: str = Field(
        description = "Practical(a coding question or a maths/calculation problem) or Theory(a concept or process\
             explaination)"
    )
    companies: str = Field(
        description = "String of comma seperated names of companies which usually asks this type of questions"
    )

class PerformanceMetricsItemsSchema(BaseModel):
    Confidence: str = Field(
        description = "Assess the level of certainty and clarity in the presentation"
    )
    answering_patterns: str = Field(
        description = "Note any recurring positive or negative habits (e.g., rambling, jumping to conclusions,\
             excellent structuring)"
    )
    clarity_and_completeness_within_time: str = Field(
        description = "Judge whether the candidate was able to clearly and completely explain the solution/concept\
             within the strict 10-minute timeframe"
    )

class EvaluationSchema(BaseModel):
    rating: str = Field(
        description = "Assign a rating to each individual answer: Good, Average, or Bad"
    )
    feedback: str = Field(
        description = "For every answer, provide detailed, actionable feedback. Explain in detail what went wrong\
             (technical inaccuracy, lack of depth, poor structure) and how the answer could have been improved\
                 (specific concepts to mention, better approach, clearer explanation)"
    )
    performance_metrics: List[PerformanceMetricsItemsSchema] = Field(description = "Judge the candidate's performance\
         across the entire interview")
    final_verdict: str = Field(
        description = "Conclude the entire interaction with a clear, unambiguous verdict on the candidate's capability\
             for the desired role. If the verdict is negative ('Not Capable'), you must provide a concise, prioritized\
                 list of key reasons why (e.g., 'Lacks deep knowledge in Distributed Transactions', 'System design\
                     lacked metrics and failure analysis')"
    )

class QuestionsSchema(BaseModel):
    questions: List[QuestionsItemSchema] = Field(description = "List of questions")

class PDFSchema(BaseModel):
    label: str = Field(description = "Use the value for label from the tool response")
    file_path: str = Field(description = "Use the value for file_path from the tool response")
    file_name: str = Field(description = "Use the value for file_name from the tool response")
    mime: str = Field(description = "Use the value for mime from the tool response")

class EmailSchema(BaseModel):
    subject: str = Field(description = "Subject of the email")
    body: str = Field(description = "Content of the email")
    attachment: PDFSchema = Field(description = "PDF details of the interview")

class WhatsappSchema(BaseModel):
    message: str = Field(description = "Content of the message")
    attachment: PDFSchema = Field(description = "PDF details of the interview")

class DescriptionValueItemsSchema(BaseModel):
    key: str = Field(description = "Key for which the description value is to be generated")
    value: str = Field(description = "Value generated using key specific description")

class DescriptionValueSchema(BaseModel):
    endpoint: str = Field(description = "Endpoint to which this value is generated, given in user message")
    values: List[DescriptionValueItemsSchema] = Field(description = "List of description values of the interview")

class ReportingSchema(BaseModel):
    pdf: PDFSchema = Field(description = "PDF details of the interview, if asked to be generated")
    email: List[EmailSchema] = Field(description = "List of email details of the interview, if asked to be generated")
    whatsapp: List[WhatsappSchema] = Field(
        description = "List of whatsapp details of the interview, if asked to be generated"
    )
    description_value: DescriptionValueSchema = Field(
        description = "Dictionary of description values of the interview, if asked to be generated"
    )
