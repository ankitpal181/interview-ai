import os, uuid, json, torch, re
from typing import Any, Optional, List, Sequence
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer
from langchain_openai.chat_models import ChatOpenAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig, Runnable
from langchain_core.messages import AIMessage, BaseMessage, ToolCall
from langchain_core.language_models import LanguageModelInput
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_core.tools import BaseTool


class LocalModel(BaseChatModel):
    client: Any = Field(default=None, exclude=True)
    tokenizer: Any = Field(default=None, exclude=True)
    fine_tune: bool = Field(default=False)
    DEVICE: torch.device = Field(default="cpu", exclude=True)

    def __init__(self, model: str, fine_tune: bool = False) -> None:
        super().__init__()
        self.fine_tune = fine_tune

        if torch.backends.mps.is_available():
            self.DEVICE = torch.device("mps")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True)
            self.client = AutoModelForCausalLM.from_pretrained(model, local_files_only=True).to(self.DEVICE)
        except:
            self.tokenizer = AutoTokenizer.from_pretrained(model)
            self.client = AutoModelForCausalLM.from_pretrained(model).to(self.DEVICE)
    
    @property
    def _llm_type(self) -> str:
        return "local"

    def invoke(
        self, input: LanguageModelInput, config: Optional[RunnableConfig] = None,
        *, stop: Optional[list[str]] = None, **kwargs: Any,
    ) -> AIMessage:
        return super().invoke(input, config, stop=stop, **kwargs)
    
    def _generate(
        self,
        messages: List[BaseMessage],
        **kwargs: Any,
    ) -> ChatResult:
        conversation_context = ""
        generated_texts_list = []
        tools_block = {
            "available_tools": [convert_to_openai_tool(tool) for tool in kwargs.get("tools", [])],
            "tool_config": kwargs.get("tool_config")
        }

        for message in messages:
            if message.type == "human":
                conversation_context += f"User: {message.content}\n"
            elif message.type == "ai":
                conversation_context += f"Assistant: {message.content}\n"
            elif message.type == "system":
                conversation_context += f"System: {message.content}\n"
                tools_json = json.dumps(tools_block, indent=2)
                conversation_context += f"\n# Available Tools\nYou have access to the following tools. To call a tool, respond with a JSON object inside a ```json code block using this format:\n{{\n\"tool\": \"tool_name\",\n\"parameters\": {{ \"param1\": \"value1\" }}\n}}\n\n## Tool Definitions:\n{tools_json}\n"

        tokenized_input = self.tokenizer(conversation_context, return_tensors="pt").to(self.DEVICE)

        if self.fine_tune:
            llm_response = self.client.generate(
                tokenized_input["input_ids"], max_new_tokens=256, num_return_sequences=1
            )
        else:
            with torch.no_grad():
                llm_response = self.client.generate(
                    tokenized_input["input_ids"], max_new_tokens=256, num_return_sequences=1
                )
        
        input_length = tokenized_input["input_ids"].shape[1]
        message = self.tokenizer.decode(llm_response[0][input_length:], skip_special_tokens=True)
        json_match = re.search(r"```json\s*(.*?)\s*```", message, re.DOTALL)

        if json_match:
            try:
                data = json.loads(json_match.group(1))
                tool_call = ToolCall(
                    name=data["tool"],
                    args=data["parameters"],
                    id=str(uuid.uuid4())
                )
                generated_texts_list.append(ChatGeneration(
                    message=AIMessage(content=message, tool_calls=[tool_call]), generation_info={}
                ))
            except Exception as e:
                generated_texts_list.append(
                    ChatGeneration(message=AIMessage(content=message), generation_info={"error": str(e)})
                )
        else:
            generated_texts_list.append(
                ChatGeneration(message=AIMessage(content=message, generation_info={}))
            )
        
        return ChatResult(generations=generated_texts_list)
    
    def bind_tools(
        self, tools: Sequence[dict[str, Any] | BaseTool], **kwargs: Any
    ) -> Runnable[LanguageModelInput, AIMessage]:
        formatted_tools = [convert_to_openai_tool(tool) for tool in tools]
        return self.bind(tools=formatted_tools, **kwargs)


class Model:
    def __init__(self, tools: Sequence[dict[str, Any] | BaseTool] = [], output_schema: BaseModel = None) -> None:
        self.tools = tools
        self.tools_by_name = {tool.name: tool for tool in self.tools}

        if os.environ.get("OPENAI_API_KEY"):
            self.model = self._set_openai_model(output_schema)
        elif os.environ.get("GOOGLE_API_KEY"):
            self.model = self._set_gemini_model(output_schema)
        else:
            self.model = self._set_local_model(output_schema)
    
    def _set_openai_model(self, output_schema: BaseModel) -> ChatOpenAI:
        model = ChatOpenAI(model = os.environ.get("LLM_MODEL_NAME", ""))
        model = model.bind_tools(self.tools)

        if output_schema: model = model.with_structured_output(output_schema)
        return model
    
    def _set_gemini_model(self, output_schema: BaseModel) -> ChatGoogleGenerativeAI:
        model = ChatGoogleGenerativeAI(model = os.environ.get("LLM_MODEL_NAME", ""))
        model = model.bind_tools(self.tools)

        if output_schema: model = model.with_structured_output(output_schema)
        return model
    
    def _set_local_model(self, output_schema: BaseModel) -> LocalModel:
        model = LocalModel(model = os.environ.get("LLM_MODEL_NAME", ""))
        model = model.bind_tools(self.tools)

        if output_schema: model = model.with_structured_output(output_schema)
        return model
