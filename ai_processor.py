import json
import os
import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

class AIProcessor:
    def __init__(self, backend="perplexity", settings=None):
        """
        Initialize AI Processor with configurable backend.
        
        Args:
            backend (str): AI backend to use - "perplexity", "ollama", or "openai"
            settings (dict): Configuration settings for AI processing
        """
        self.backend = backend
        self.api_available = False
        self.settings = settings or {}
        
        # Configure performance settings
        self.extraction_temperature = self.settings.get('extraction_temperature', 0.1)
        self.max_tokens = self.settings.get('max_tokens', 1000)
        
        if backend == "perplexity":
            self.model = "llama-3.1-sonar-small-128k-online"
            self.api_key = os.getenv("PERPLEXITY_API_KEY")
            self.base_url = "https://api.perplexity.ai/chat/completions"
            self.api_available = bool(self.api_key)
            
        elif backend == "ollama":
            self.model = self.settings.get('ollama_model') or os.getenv("OLLAMA_MODEL", "mistral:latest")
            self.base_url = self.settings.get('ollama_base_url') or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.api_key = None  # Ollama doesn't require API keys
            self._check_ollama_availability()
            
        elif backend == "openai":
            self.model = "gpt-4o"
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = "https://api.openai.com/v1/chat/completions"
            self.api_available = bool(self.api_key)
    
    def _check_ollama_availability(self):
        """Check if Ollama is running and the model is available."""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                # Check if the specified model is available
                if any(self.model in model_name for model_name in model_names):
                    self.api_available = True
                else:
                    print(f"Ollama model '{self.model}' not found. Available models: {model_names}")
                    self.api_available = False
            else:
                self.api_available = False
        except Exception as e:
            print(f"Ollama not available: {e}")
            self.api_available = False
    
    def _make_api_request(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.2) -> Dict:
        """Make a request to the configured AI backend."""
        if self.backend == "ollama":
            return self._make_ollama_request(messages, max_tokens, temperature)
        elif self.backend == "perplexity":
            return self._make_perplexity_request(messages, max_tokens, temperature)
        elif self.backend == "openai":
            return self._make_openai_request(messages, max_tokens, temperature)
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")
    
    def _make_perplexity_request(self, messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> Dict:
        """Make a request to Perplexity API."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': 0.9,
            'stream': False,
            'presence_penalty': 0,
            'frequency_penalty': 1
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def _make_ollama_request(self, messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> Dict:
        """Make a request to Ollama API."""
        headers = {'Content-Type': 'application/json'}
        
        # Convert messages to Ollama format
        prompt = self._convert_messages_to_prompt(messages)
        
        payload = {
            'model': self.model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': temperature,
                'num_predict': max_tokens,
            }
        }
        
        response = requests.post(f"{self.base_url}/api/generate", headers=headers, json=payload)
        response.raise_for_status()
        
        # Convert Ollama response to OpenAI-like format for compatibility
        ollama_response = response.json()
        return {
            'choices': [{
                'message': {
                    'content': ollama_response.get('response', '')
                }
            }]
        }
    
    def _make_openai_request(self, messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> Dict:
        """Make a request to OpenAI API."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': 0.9,
            'stream': False,
            'presence_penalty': 0,
            'frequency_penalty': 0
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to a single prompt for Ollama."""
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts) + "\n\nAssistant:"
    
    def extract_action_items(self, text: str, auto_categorize: bool = True, auto_delegate: bool = True) -> List[Dict[str, Any]]:
        """Extract action items from meeting notes or text using AI, optimized for Mistral models."""
        if not self.api_available:
            return self._fallback_extraction(text)
        
        try:
            # Use different prompting strategy based on backend
            if self.backend == "ollama" and "mistral" in self.model.lower():
                return self._extract_with_mistral_optimization(text, auto_categorize, auto_delegate)
            else:
                return self._extract_with_standard_prompt(text, auto_categorize, auto_delegate)
            
        except Exception as e:
            print(f"AI processing error: {e}")
            return self._fallback_extraction(text)
    
    def _extract_with_mistral_optimization(self, text: str, auto_categorize: bool, auto_delegate: bool) -> List[Dict[str, Any]]:
        """Optimized extraction for Mistral models with step-by-step approach."""
        
        # Step 1: Extract raw action items
        system_prompt = """You are a task extraction expert. Your job is to find action items in text.

RULES:
1. Look for tasks that need to be done
2. Look for assignments or responsibilities 
3. Look for deadlines or timeframes
4. Ignore general discussion or information
5. AVOID DUPLICATES - each action item should be unique and distinct
6. Combine similar tasks into one clear action item

TASK: Read the text and list each UNIQUE action item you find. Be specific and actionable.

FORMAT: Return only a JSON array like this:
["Action item 1", "Action item 2", "Action item 3"]

IMPORTANT: 
- Each item must be different from the others
- If multiple people need to do the same thing, combine into one task
- Focus on distinct outcomes, not repeated activities
- Keep it simple - just the unique action items as strings in a JSON array."""

        user_prompt = f"""Extract action items from this text:

{text}

Return only the JSON array of action items."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self._make_api_request(messages, max_tokens=self.max_tokens, temperature=self.extraction_temperature)
            content = response['choices'][0]['message']['content'].strip()
            
            # Clean and parse the response
            content = self._extract_json_from_content(content)
            raw_items = json.loads(content)
            
            if not isinstance(raw_items, list):
                return self._fallback_extraction(text)
                
        except Exception as e:
            print(f"Step 1 failed: {e}")
            return self._fallback_extraction(text)
        
        # Step 2: Enhance each item with metadata
        enhanced_items = []
        for i, item in enumerate(raw_items[:8]):  # Limit to 8 items for processing
            try:
                enhanced_item = self._enhance_action_item(item, i + 1, auto_categorize, auto_delegate)
                if enhanced_item:
                    enhanced_items.append(enhanced_item)
            except Exception as e:
                print(f"Enhancement failed for item {i}: {e}")
                # Add basic item if enhancement fails
                enhanced_items.append({
                    'title': f"Task {i + 1}",
                    'description': str(item)[:200],
                    'priority': 'Medium',
                    'category': 'Other',
                    'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                    'estimated_hours': 2.0,
                    'suggested_delegate': None
                })
        
        # Step 3: Remove duplicates and similar items
        deduplicated_items = self._remove_duplicate_items(enhanced_items)
        
        return deduplicated_items
    
    def _remove_duplicate_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate and very similar action items."""
        if len(items) <= 1:
            return items
        
        unique_items = []
        seen_titles = set()
        
        for item in items:
            title_lower = item.get('title', '').lower().strip()
            desc_lower = item.get('description', '').lower().strip()
            
            # Check for exact title matches
            if title_lower in seen_titles:
                continue
            
            # Check for similar items (high similarity in title or description)
            is_duplicate = False
            for existing_item in unique_items:
                existing_title = existing_item.get('title', '').lower().strip()
                existing_desc = existing_item.get('description', '').lower().strip()
                
                # Simple similarity check
                if (self._similarity_score(title_lower, existing_title) > 0.8 or 
                    self._similarity_score(desc_lower, existing_desc) > 0.8):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_items.append(item)
                seen_titles.add(title_lower)
        
        return unique_items
    
    def _similarity_score(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings (0.0 to 1.0)."""
        if not str1 or not str2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _enhance_action_item(self, raw_item: str, item_number: int, auto_categorize: bool, auto_delegate: bool) -> Dict[str, Any]:
        """Enhance a raw action item with metadata using focused prompts."""
        
        # Get available categories and delegates from settings
        categories = self.settings.get('categories', ['Strategic', 'Technical', 'Meeting', 'Review', 'Administrative', 'Other'])
        delegates = self.settings.get('delegates', ['Developer', 'Designer', 'QA Engineer', 'Marketing Team', 'Technical Writer', 'Project Manager'])
        
        categories_str = "/".join(categories)
        
        system_prompt = f"""You are a task analyst. Analyze the given action item and return structured data.

ANALYZE THE TASK FOR:
1. Priority (Critical/High/Medium/Low)
2. Category ({categories_str})  
3. Time estimate in hours (0.5 to 40.0)
4. Due date (YYYY-MM-DD format, estimate if not specified)

RETURN ONLY THIS JSON:
{{
  "title": "Short clear title (max 50 chars)",
  "description": "What needs to be done",
  "priority": "Medium", 
  "category": "Other",
  "estimated_hours": 2.0,
  "due_date": "2025-01-30"
}}"""

        user_prompt = f"""Analyze this action item:

{raw_item}

Estimate a due date about 1 week from now unless urgency suggests otherwise.
Return only the JSON object."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self._make_api_request(messages, max_tokens=min(500, self.max_tokens), temperature=self.extraction_temperature)
            content = response['choices'][0]['message']['content'].strip()
            
            # Extract and parse JSON
            content = self._extract_json_from_content(content)
            enhanced_item = json.loads(content)
            
            # Validate required fields
            required_fields = ['title', 'description', 'priority', 'category', 'estimated_hours', 'due_date']
            for field in required_fields:
                if field not in enhanced_item:
                    enhanced_item[field] = self._get_default_value(field)
            
            # Add delegation suggestion if enabled
            enhanced_item['suggested_delegate'] = None
            if auto_delegate:
                enhanced_item['suggested_delegate'] = self._suggest_delegate(raw_item, delegates)
            
            return enhanced_item
            
        except Exception as e:
            print(f"Enhancement error: {e}")
            return None
    
    def _extract_with_standard_prompt(self, text: str, auto_categorize: bool, auto_delegate: bool) -> List[Dict[str, Any]]:
        """Standard extraction for non-Mistral models."""
        system_prompt = """You are an expert project manager specialized in extracting action items from text. 

Extract actionable tasks and return a JSON object with an "action_items" array. Each item needs:
- title: Clear, concise title 
- description: What needs to be done
- priority: Critical/High/Medium/Low
- category: Strategic/Technical/Meeting/Review/Administrative/Other
- due_date: YYYY-MM-DD format
- estimated_hours: 0.5 to 40.0
- suggested_delegate: null or name if mentioned

Return only the JSON object."""

        user_prompt = f"""Extract action items from:

{text}

Return JSON with action_items array."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._make_api_request(messages, max_tokens=2000)
        content = response['choices'][0]['message']['content']
        
        # Extract and parse JSON
        content = self._extract_json_from_content(content)
        result = json.loads(content)
        return result.get('action_items', [])
    
    def _extract_json_from_content(self, content: str) -> str:
        """Extract JSON from AI response content, handling common formatting issues."""
        content = content.strip()
        
        # Remove code block markers
        content = re.sub(r'^```(?:json)?\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
        
        # Find JSON-like content
        json_match = re.search(r'(\[.*\]|\{.*\})', content, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        return content
    
    def _get_default_value(self, field: str):
        """Get default value for missing fields."""
        defaults = {
            'title': 'Action Item',
            'description': 'Task needs completion',
            'priority': 'Medium',
            'category': 'Other',
            'estimated_hours': 2.0,
            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        }
        return defaults.get(field, '')
    
    def _suggest_delegate(self, text: str, available_delegates: List[str]) -> str:
        """Simple delegation suggestion based on text content and available delegates."""
        text_lower = text.lower()
        
        # Create mapping of keywords to delegate types
        delegate_keywords = {
            'Developer': ['develop', 'code', 'implement', 'build', 'program', 'software'],
            'Designer': ['design', 'ui', 'ux', 'mockup', 'visual', 'interface'],
            'QA Engineer': ['test', 'qa', 'verify', 'validate', 'quality', 'bug'],
            'Marketing Team': ['market', 'customer', 'user research', 'promotion', 'campaign'],
            'Technical Writer': ['document', 'write', 'spec', 'documentation', 'manual'],
            'Project Manager': ['coordinate', 'manage', 'schedule', 'plan', 'organize']
        }
        
        # Look for role indicators and match with available delegates
        for delegate in available_delegates:
            keywords = delegate_keywords.get(delegate, [])
            if any(keyword in text_lower for keyword in keywords):
                return delegate
        
        return None
    
    def _fallback_extraction(self, text: str) -> List[Dict[str, Any]]:
        """Fallback extraction using simple text analysis when AI is not available."""
        action_items = []
        
        # Simple pattern matching for action items
        action_patterns = [
            r'(?:action|todo|task|follow[- ]?up|need to|should|must|will)[\s:]+([^\n\r.!?]*)',
            r'(?:assign|delegate)[\s:]+([^\n\r.!?]*)',
            r'(?:deadline|due)[\s:]+([^\n\r.!?]*)',
        ]
        
        lines = text.split('\n')
        item_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for action patterns
            for pattern in action_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    if len(match.strip()) > 10:  # Ensure meaningful content
                        item_count += 1
                        action_items.append({
                            'title': f"Action Item {item_count}",
                            'description': match.strip(),
                            'priority': 'Medium',
                            'category': 'Other',
                            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                            'estimated_hours': 2.0,
                            'suggested_delegate': None
                        })
        
        # If no patterns found, try bullet points or numbered lists
        if not action_items:
            for line in lines:
                line = line.strip()
                if re.match(r'^[\-\*\+\d\.]+\s+', line):
                    content = re.sub(r'^[\-\*\+\d\.]+\s+', '', line).strip()
                    if len(content) > 10:
                        item_count += 1
                        action_items.append({
                            'title': f"Task {item_count}",
                            'description': content,
                            'priority': 'Medium',
                            'category': 'Other',
                            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                            'estimated_hours': 1.5,
                            'suggested_delegate': None
                        })
        
        return action_items[:10]  # Limit to 10 items for fallback
    
    def prioritize_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use AI to re-prioritize tasks based on context and dependencies."""
        if not self.api_available or not tasks:
            return self._fallback_prioritization(tasks)
        
        try:
            system_prompt = """You are an expert in task prioritization for tech leadership. 
Analyze the provided tasks and assign appropriate priorities based on:
- Business impact and strategic importance
- Urgency and deadlines
- Dependencies between tasks
- Resource requirements
- Risk factors

Return a JSON object with the same tasks but with updated priorities (Critical, High, Medium, Low) and brief reasoning.
Format: {"tasks": [{"id": ..., "priority": "High", "priority_reasoning": "...", ...}]}"""

            user_prompt = f"""Please analyze and prioritize these tasks:

{json.dumps(tasks, indent=2)}

Return the same tasks with updated priorities and add a 'priority_reasoning' field explaining the priority assignment."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self._make_api_request(messages, max_tokens=2000)
            
            content = response['choices'][0]['message']['content']
            result = json.loads(content)
            return result.get('tasks', tasks)
            
        except Exception as e:
            print(f"AI prioritization error: {e}")
            return self._fallback_prioritization(tasks)
    
    def _fallback_prioritization(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback prioritization using simple heuristics."""
        for task in tasks:
            # Simple scoring based on due date and keywords
            score = 0
            
            # Due date urgency
            if task.get('due_date'):
                try:
                    due_date = datetime.strptime(task['due_date'], '%Y-%m-%d')
                    days_until_due = (due_date - datetime.now()).days
                    if days_until_due <= 1:
                        score += 30
                    elif days_until_due <= 3:
                        score += 20
                    elif days_until_due <= 7:
                        score += 10
                except:
                    pass
            
            # Keyword analysis
            text = f"{task.get('title', '')} {task.get('description', '')}".lower()
            urgent_keywords = ['urgent', 'asap', 'critical', 'emergency', 'deadline', 'milestone']
            high_keywords = ['important', 'priority', 'strategic', 'key', 'major']
            
            for keyword in urgent_keywords:
                if keyword in text:
                    score += 25
            
            for keyword in high_keywords:
                if keyword in text:
                    score += 15
            
            # Assign priority based on score
            if score >= 40:
                task['priority'] = 'Critical'
            elif score >= 25:
                task['priority'] = 'High'
            elif score >= 10:
                task['priority'] = 'Medium'
            else:
                task['priority'] = 'Low'
        
        return tasks
    
    def generate_insights(self, tasks: List[Dict[str, Any]], delegations: List[Dict[str, Any]]) -> List[str]:
        """Generate AI insights about workload and productivity."""
        if not self.api_available or not (tasks or delegations):
            return self._fallback_insights(tasks, delegations)
        
        try:
            system_prompt = """You are an executive assistant AI specialized in workload analysis and productivity insights for tech leadership. 
Analyze the provided tasks and delegations to generate actionable insights about:
- Workload distribution and balance
- Bottlenecks and risks
- Delegation effectiveness
- Priority alignment
- Time management opportunities
- Strategic focus areas

Return a JSON object with an "insights" array containing 3-5 concise, actionable insights.
Format: {"insights": ["Insight 1", "Insight 2", ...]}"""

            user_prompt = f"""Please analyze this workload data and provide insights:

TASKS:
{json.dumps(tasks[-20:], indent=2) if tasks else "No tasks"}

DELEGATIONS:
{json.dumps(delegations[-10:], indent=2) if delegations else "No delegations"}

Generate actionable insights for better productivity and workload management."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self._make_api_request(messages, max_tokens=1500)
            
            content = response['choices'][0]['message']['content']
            result = json.loads(content)
            return result.get('insights', [])
            
        except Exception as e:
            print(f"AI insights error: {e}")
            return self._fallback_insights(tasks, delegations)
    
    def _fallback_insights(self, tasks: List[Dict[str, Any]], delegations: List[Dict[str, Any]]) -> List[str]:
        """Generate basic insights using simple analytics."""
        insights = []
        
        if tasks:
            # Task analysis
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.get('status') == 'Completed'])
            critical_tasks = len([t for t in tasks if t.get('priority') == 'Critical'])
            overdue_tasks = len([t for t in tasks if t.get('due_date') and 
                               datetime.strptime(t['due_date'], '%Y-%m-%d') < datetime.now() and 
                               t.get('status') != 'Completed'])
            
            if overdue_tasks > 0:
                insights.append(f"⚠️ You have {overdue_tasks} overdue tasks that need immediate attention.")
            
            if critical_tasks > 3:
                insights.append(f"🔥 High workload alert: {critical_tasks} critical tasks detected. Consider delegation.")
            
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            if completion_rate < 50:
                insights.append(f"📈 Current completion rate is {completion_rate:.1f}%. Focus on completing existing tasks.")
            
            # Category analysis
            categories = {}
            for task in tasks:
                cat = task.get('category', 'Other')
                categories[cat] = categories.get(cat, 0) + 1
            
            if categories:
                top_category = max(categories, key=categories.get)
                insights.append(f"📊 Most tasks are in {top_category} category ({categories[top_category]} tasks).")
        
        if delegations:
            pending_delegations = len([d for d in delegations if d.get('status') in ['Assigned', 'In Progress']])
            if pending_delegations > 5:
                insights.append(f"👥 You have {pending_delegations} active delegations. Follow up for status updates.")
        
        if not insights:
            insights.append("✅ Your workload looks manageable. Keep up the good work!")
        
        return insights[:5]  # Limit to 5 insights
    
    def suggest_calendar_blocking(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest optimal calendar time blocks for tasks."""
        if not self.api_available:
            return self._fallback_calendar_blocking(tasks)
        
        try:
            system_prompt = """You are a time management expert. Analyze the provided tasks and suggest optimal calendar time blocks considering:
- Task priorities and deadlines
- Estimated durations
- Optimal work periods for different task types
- Buffer time for interruptions
- Energy levels throughout the day

Return a JSON object with suggested calendar blocks.
Format: {"calendar_blocks": [{"task_id": ..., "suggested_start_time": "09:00", "duration_hours": 2.0, "day_preference": "weekday", "rationale": "..."}]}"""

            # Filter tasks that need scheduling
            pending_tasks = [t for t in tasks if t.get('status') not in ['Completed'] and t.get('due_date')]
            
            user_prompt = f"""Please suggest calendar time blocks for these tasks:

{json.dumps(pending_tasks, indent=2)}

Return suggestions with: task_id, suggested_start_time, duration_hours, day_preference, and rationale."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self._make_api_request(messages, max_tokens=1500)
            
            content = response['choices'][0]['message']['content']
            result = json.loads(content)
            return result.get('calendar_blocks', [])
            
        except Exception as e:
            print(f"AI calendar blocking error: {e}")
            return self._fallback_calendar_blocking(tasks)
    
    def _fallback_calendar_blocking(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simple calendar blocking suggestions."""
        suggestions = []
        
        # Sort tasks by priority and due date
        sorted_tasks = sorted(tasks, key=lambda x: (
            ['Critical', 'High', 'Medium', 'Low'].index(x.get('priority', 'Medium')),
            x.get('due_date', '9999-12-31')
        ))
        
        current_time = 9  # Start at 9 AM
        
        for task in sorted_tasks[:5]:  # Limit to top 5 tasks
            if task.get('status') == 'Completed':
                continue
                
            duration = float(task.get('estimated_hours', 1.0))
            
            # Suggest time based on task type
            if task.get('category') == 'Strategic':
                preferred_time = "Morning (9-11 AM) - best for strategic thinking"
                start_time = "09:00"
            elif task.get('category') == 'Technical':
                preferred_time = "Mid-morning (10 AM-12 PM) - peak focus time"
                start_time = "10:00"
            elif task.get('category') == 'Meeting':
                preferred_time = "Afternoon (1-4 PM) - collaborative time"
                start_time = "14:00"
            else:
                preferred_time = f"Flexible timing"
                start_time = f"{current_time:02d}:00"
                current_time += int(duration) + 1
            
            suggestions.append({
                'task_id': task.get('id'),
                'task_title': task.get('title'),
                'suggested_start_time': start_time,
                'duration_hours': duration,
                'day_preference': preferred_time,
                'rationale': f"Scheduled based on {task.get('priority', 'Medium')} priority and {task.get('category', 'general')} category"
            })
        
        return suggestions
