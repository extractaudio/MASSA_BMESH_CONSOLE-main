
import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Path Setup
mcp_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if mcp_root not in sys.path:
    sys.path.append(mcp_root)

# Mock config and server
sys.modules["config"] = MagicMock()
sys.modules["config.settings"] = MagicMock()
sys.modules["config.settings"].AGENT_WORKFLOWS_DIR = "/mock/workflows"

# We strictly mock core.server, but allow core (package) to be resolved naturally
sys.modules["core.server"] = MagicMock()
# Make @mcp.tool() a pass-through decorator so functions aren't replaced by Mocks
sys.modules["core.server"].mcp.tool.return_value = lambda func: func

from core.workflow import WorkflowEngine
from skills import workflow_runner

class TestWorkflowEngine(unittest.TestCase):
    
    def test_markdown_parsing(self):
        engine = WorkflowEngine()
        
        # Dummy Content
        content = """Overview text.

## Step 1: Init
Do X.

## Step 2: Run
```python
print('hi')
```
// turbo
"""
        with patch("builtins.open", unittest.mock.mock_open(read_data=content)):
            with patch("os.path.exists", return_value=True):
                view = engine.load_workflow("Test", "/mock/path.md")
                
        self.assertEqual(len(engine.steps), 3) # Overview, Step 1, Step 2
        self.assertEqual(engine.steps[0].title, "Overview")
        self.assertEqual(engine.steps[1].title, "Step 1: Init")
        self.assertEqual(engine.steps[2].title, "Step 2: Run")

    def test_navigation(self):
        engine = WorkflowEngine()
        # Manually inject steps
        engine._add_step(0, "S1", "C1")
        engine._add_step(1, "S2", "C2")
        
        self.assertEqual(engine.current_step_index, 0)
        
        view = engine.next_step()
        self.assertIn("Step 2", view)
        self.assertEqual(engine.current_step_index, 1)
        
        view = engine.next_step()
        self.assertIn("End of Workflow", view)
        
        view = engine.previous_step()
        self.assertEqual(engine.current_step_index, 0)

    @patch("glob.glob")
    @patch("os.path.exists")
    def test_runner_start(self, mock_exists, mock_glob):
        mock_exists.return_value = True 
        
        with patch("core.workflow.WorkflowEngine.load_workflow") as mock_load:
             mock_load.return_value = "Step 1 View"
             
             res = workflow_runner.start_workflow("exact.md")
             print(f"DEBUG: start_workflow result: {res}")
             
             # Verify it called load_workflow with the exact path
             self.assertTrue(mock_load.called, f"load_workflow was not called! Result: {res}")
             args, _ = mock_load.call_args
             self.assertEqual(args[0], "exact.md")
             self.assertIn("exact.md", args[1])

    @patch("glob.glob")
    @patch("os.path.exists")
    def test_runner_fuzzy(self, mock_exists, mock_glob):
        # Case 2: Fuzzy Logic
        def exists_side_effect(path):
            print(f"DEBUG: Checking exists for fuzzy: {path}")
            return "long_name" in str(path) # Returns true only for the fuzzy result later
        
        mock_exists.side_effect = exists_side_effect
        
        target = os.path.join("/mock", "workflows", "long_name_repair.md")
        mock_glob.return_value = [target]
        
        with patch.object(workflow_runner._ENGINE, 'load_workflow') as mock_load:
            mock_load.return_value = "Step 1 View"
            
            res = workflow_runner.start_workflow("repair")
            print(f"DEBUG: start_workflow fuzzy result: {res}")
            
            # Verify call
            self.assertTrue(mock_load.called, f"load_workflow was not called! Result: {res}")
            args, _ = mock_load.call_args
            self.assertEqual(args[0], "long_name_repair.md")
            self.assertEqual(os.path.normpath(args[1]), os.path.normpath(target))

if __name__ == '__main__':
    unittest.main()
