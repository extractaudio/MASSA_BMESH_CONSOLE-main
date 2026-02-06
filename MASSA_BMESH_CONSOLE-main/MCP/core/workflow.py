import re
import os
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class WorkflowStep:
    index: int
    title: str
    content: str
    code_blocks: List[str] = field(default_factory=list)
    automation_hint: bool = False

class WorkflowEngine:
    def __init__(self):
        self.steps: List[WorkflowStep] = []
        self.current_step_index: int = 0
        self.workflow_name: str = ""
        self.raw_content: str = ""

    def load_workflow(self, name: str, file_path: str) -> str:
        """
        Loads and parses a markdown workflow file.
        Returns the content of the first step.
        """
        self.workflow_name = name
        self.current_step_index = 0
        self.steps = []
        
        if not os.path.exists(file_path):
            return f"Error: Workflow file not found at {file_path}"
            
        with open(file_path, 'r', encoding='utf-8') as f:
            self.raw_content = f.read()
            
        self._parse_markdown(self.raw_content)
        
        return self.get_current_view()

    def _parse_markdown(self, content: str):
        """
        Splits markdown into steps based on headers.
        """
        lines = content.split('\n')
        current_title = "Overview"
        current_content = []
        step_index = 0
        
        # Regex for headers (H1 or H2)
        # We treat any ## Header as a new step start
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        
        for line in lines:
            match = header_pattern.match(line)
            if match:
                # If we have content accumulating, save the previous step
                if current_content or step_index == 0:
                    self._add_step(step_index, current_title, "\n".join(current_content))
                    step_index += 1
                    current_content = []
                
                # Set new title
                current_title = match.group(2).strip()
                current_content.append(line) 
            else:
                current_content.append(line)
                
        # Add the final step
        if current_content:
            self._add_step(step_index, current_title, "\n".join(current_content))

    def _add_step(self, index: int, title: str, content: str):
        # Extract code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        
        # Check for automation hints
        automation = "// turbo" in content
        
        step = WorkflowStep(
            index=index,
            title=title,
            content=content,
            code_blocks=code_blocks,
            automation_hint=automation
        )
        self.steps.append(step)

    def next_step(self) -> str:
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            return self.get_current_view()
        return "End of Workflow reached."

    def previous_step(self) -> str:
        if self.current_step_index > 0:
            self.current_step_index -= 1
            return self.get_current_view()
        return "Already at the start."

    def get_current_view(self) -> str:
        if not self.steps:
            return "No workflow loaded."
            
        step = self.steps[self.current_step_index]
        total = len(self.steps)
        
        view = f"""
--- WORKFLOW: {self.workflow_name} ---
Step {step.index + 1} of {total}: {step.title}
----------------------------------------
{step.content}
----------------------------------------
"""
        if step.automation_hint:
             view += "\n[!] AUTOMATION HINT DETECTED: This step may be auto-runnable."
             
        return view

    def get_status(self) -> str:
        if not self.steps:
            return "No active workflow."
        return f"Active: {self.workflow_name} | Step {self.current_step_index + 1}/{len(self.steps)}"
