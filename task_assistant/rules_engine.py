import yaml
from .logger_config import log


class RulesEngine:
    def __init__(self, config_path="config.yaml"):
        try:
            with open(config_path, 'r') as f:
                self.rules = yaml.safe_load(f)
            log.info(f"Rules loaded successfully from {config_path}")
        except FileNotFoundError:
            log.warning(f"Configuration file not found at {config_path}. No rules will be applied.")
            self.rules = {}
        except Exception as e:
            log.error(f"Error loading configuration file: {e}")
            self.rules = {}

    def apply_priority(self, tasks: list[dict]) -> list[dict]:
        """
        Applies priority to tasks based on keywords in the task description.

        Args:
            tasks: A list of task dictionaries.

        Returns:
            The list of tasks with an added 'priority' key.
        """
        if "priority_rules" not in self.rules:
            return tasks

        priority_rules = self.rules["priority_rules"]

        for task in tasks:
            task['priority'] = "⚪ Normal"  # Default priority
            task_description = task.get("task", "").lower()

            for rule in priority_rules:
                if any(keyword in task_description for keyword in rule["keywords"]):
                    task['priority'] = rule["priority"]
                    break  # Stop at the first rule that matches

        return tasks