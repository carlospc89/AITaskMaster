# task_assistant/agent.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain.output_parsers import PydanticOutputParser
from .schemas import TaskList, Task  # Import both schemas
from .logger_config import log
from datetime import datetime
import json


class Agent:
    def __init__(self, model):
        self.model = model
        self.parser = PydanticOutputParser(pydantic_object=TaskList)

    def get_structured_tasks(self, prompt_template: str, content: str) -> TaskList:
        """
        Processes content to extract structured tasks using a Pydantic parser.
        This version is robust to the AI returning either a dict or a list.
        """
        current_date_str = datetime.now().strftime("%A, %Y-%m-%d")

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_template),
            ("human", "{user_input}")
        ])

        # We get the raw string output from the model first
        chain = prompt | self.model

        log.info("Invoking LLM chain to get raw output...")
        try:
            raw_result = chain.invoke({
                "format_instructions": self.parser.get_format_instructions(),
                "current_date": current_date_str,
                "user_input": content
            })
            # Clean the raw output from the AI
            raw_json_str = raw_result.content.strip().replace("```json", "").replace("```", "").strip()

            # Now, we manually parse and validate
            data = json.loads(raw_json_str)

            # If the AI returns a list, wrap it in the expected dictionary
            if isinstance(data, list):
                data = {"tasks": data}

            # Now, validate with the Pydantic model
            parsed_object = TaskList.model_validate(data)
            return parsed_object

        except Exception as e:
            log.error(f"Failed to parse LLM output: {e}", exc_info=True)
            return TaskList(tasks=[])

    def get_prioritization(self, tasks_json: str, system_prompt: str) -> str:
        """
        Makes a one-off call to the model for a specific task like prioritization.
        """
        log.info("Requesting prioritization from the model...")
        messages = [
            {"role": "system", "content": system_prompt},
            HumanMessage(content=tasks_json)
        ]
        response = self.model.invoke(messages)
        return response.content
