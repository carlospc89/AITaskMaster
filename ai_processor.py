import json
import os
import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

class AIProcessor:
    def __init__(self):
        # Using Perplexity Pro API with llama-3.1-sonar-small-128k-online model
        self.model = "llama-3.1-sonar-small-128k-online"
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        
        if self.api_key:
            self.api_available = True
        else:
            self.api_available = False
    
    def _make_api_request(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.2) -> Dict:
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
    
    def extract_action_items(self, text: str, auto_categorize: bool = True, auto_delegate: bool = True) -> List[Dict[str, Any]]:
        """Extract action items from meeting notes or text using AI."""
        if not self.api_available:
            return self._fallback_extraction(text)
        
        try:
            system_prompt = """You are an expert project manager and AI assistant specialized in extracting action items from meeting notes and text. 

Your task is to analyze the provided text and extract actionable items. Respond with a JSON object containing an "action_items" array. Each action item should have:
- title: A clear, concise title for the action item
- description: A brief description of what needs to be done
- priority: One of [Critical, High, Medium, Low] based on urgency and importance
- category: One of [Strategic, Technical, Meeting, Review, Administrative, Other]
- due_date: Estimated due date in YYYY-MM-DD format (if mentioned or can be inferred)
- estimated_hours: Estimated time to complete in hours (0.5 to 40.0)
- suggested_delegate: If the task should be delegated, suggest who (if mentioned in text)

Guidelines:
- Only extract clear, actionable items (not general discussions)
- Prioritize based on urgency indicators (ASAP, urgent, deadline, etc.)
- Estimate realistic timeframes
- Identify delegation opportunities for tasks that don't require direct leadership involvement
- If no specific date is mentioned, estimate based on priority and context

Example response format:
{"action_items": [{"title": "...", "description": "...", "priority": "High", "category": "Technical", "due_date": "2025-01-25", "estimated_hours": 2.0, "suggested_delegate": null}]}"""

            user_prompt = f"""Please analyze the following text and extract all action items:

{text}

Additional instructions:
- Auto-categorize tasks: {auto_categorize}
- Suggest delegations: {auto_delegate}

Return the results as a JSON object with an "action_items" array."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self._make_api_request(messages, max_tokens=2000)
            
            content = response['choices'][0]['message']['content']
            result = json.loads(content)
            return result.get('action_items', [])
            
        except Exception as e:
            print(f"AI processing error: {e}")
            return self._fallback_extraction(text)
    
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
