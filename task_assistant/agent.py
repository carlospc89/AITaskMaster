# task_assistant/agent.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain.output_parsers import PydanticOutputParser
from .schemas import TaskList, Task
from .logger_config import log
from datetime import datetime
import json
import re  # Import the regular expression module


class Agent:
    def __init__(self, model):
        self.model = model
        self.parser = PydanticOutputParser(pydantic_object=TaskList)

    def get_structured_tasks(self, prompt_template: str, content: str) -> TaskList:
        """
        Processes content to extract structured tasks. This version is resilient
        to cases where the LLM returns conversational text alongside the JSON.
        """
        current_date_str = datetime.now().strftime("%A, %Y-%m-%d")

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_template),
            ("human", "{user_input}")
        ])

        chain = prompt | self.model

        log.info("Invoking LLM chain to get raw output...")
        try:
            raw_result = chain.invoke({
                "format_instructions": self.parser.get_format_instructions(),
                "current_date": current_date_str,
                "user_input": content
            })
            raw_response_text = raw_result.content

            # THIS IS THE FIX: Instead of assuming the whole response is JSON,
            # we search for the JSON block within the text.
            start_index = raw_response_text.find('[')
            end_index = raw_response_text.rfind(']')

            if start_index != -1 and end_index != -1:
                json_str = raw_response_text[start_index: end_index + 1].strip()
                log.info(f"Extracted JSON string: {json_str}")

                # Now that we have a clean JSON string, we can parse it
                data = json.loads(json_str)

                if isinstance(data, list):
                    data = {"tasks": data}

                parsed_object = TaskList.model_validate(data)
                return parsed_object
            else:
                log.warning(f"AI returned a response, but no JSON array was found in it: '{raw_response_text}'")
                return TaskList(tasks=[])

        except Exception as e:
            log.error(f"Failed to get structured tasks from LLM: {e}", exc_info=True)
            return TaskList(tasks=[])

    def get_prioritization(self, tasks_json: str, system_prompt: str) -> str:
        log.info("Requesting prioritization from the model...")
        messages = [
            {"role": "system", "content": system_prompt},
            HumanMessage(content=tasks_json)
        ]
        response = self.model.invoke(messages)
        return response.content
