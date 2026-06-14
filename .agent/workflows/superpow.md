---
description: Turn on and activate the Superpowers skills and development methodology.
---

# Superpowers Command

This command activates the Superpowers development methodology by instructing the agent to utilize the skills located in the `.agent/SuperPow/skills` directory.

## What This Command Does

When you execute `/superpow`, the agent will:
1. Acknowledge that the Superpowers methodology is now active.
2. Begin incorporating the Superpowers skills (like `brainstorming`, `test-driven-development`, `writing-plans`, `subagent-driven-development`, etc.) into its workflow.
3. Consult the Superpowers central instruction file (`using-superpowers`) to understand the core rules and constraints.

## The Basic Workflow

Once activated, the agent will naturally follow these steps as described in the Superpowers documentation:
1. **brainstorming** - Activates before writing code. Refines rough ideas through questions, explores alternatives, presents design in sections for validation. Saves design document.
2. **writing-plans** - Activates with approved design. Breaks work into bite-sized tasks (2-5 minutes each). Every task has exact file paths, complete code, verification steps.
4. **subagent-driven-development** or **executing-plans** - Activates with plan. Dispatches fresh subagent per task with two-stage review (spec compliance, then code quality), or executes in batches with human checkpoints.
5. **test-driven-development** - Activates during implementation. Enforces RED-GREEN-REFACTOR.
6. **requesting-code-review** - Activates between tasks. Reviews against plan.
7. **finishing-a-development-task** - Activates when tasks complete.

## Agent Instructions

Upon running this command, the agent MUST immediately:
1. View the core constraints file by reading `c:\Users\extra\OneDrive\Documents\vscode projects\Massa_Mesh\MASSA_BMESH_CONSOLE-main\.agent\SuperPow\skills\using-superpowers\SKILL.md`.
2. Acknowledge to the user that the Superpowers methodology has been activated.
3. When performing tasks, you MUST use the `view_file` tool to read the `SKILL.md` inside any of the following directories when the respective workflow step is reached:
   - `c:\Users\extra\OneDrive\Documents\vscode projects\Massa_Mesh\MASSA_BMESH_CONSOLE-main\.agent\SuperPow\skills\brainstorming\SKILL.md`
   - `c:\Users\extra\OneDrive\Documents\vscode projects\Massa_Mesh\MASSA_BMESH_CONSOLE-main\.agent\SuperPow\skills\dispatching-parallel-agents\SKILL.md`
   - `c:\Users\extra\OneDrive\Documents\vscode projects\Massa_Mesh\MASSA_BMESH_CONSOLE-main\.agent\SuperPow\skills\executing-plans\SKILL.md`
   - `c:\Users\extra\OneDrive\Documents\vscode projects\Massa_Mesh\MASSA_BMESH_CONSOLE-main\.agent\SuperPow\skills\finishing-a-development-task\SKILL.md`
   - `c:\Users\extra\OneDrive\Documents\vscode projects\Massa_Mesh\MASSA_BMESH_CONSOLE-main\.agent\SuperPow\skills\receiving-code-review\SKILL.md`
   - `c:\Users\extra\OneDrive\Documents\vscode projects\Massa_Mesh\MASSA_BMESH_CONSOLE-main\.agent\SuperPow\skills\requesting-code-review\SKILL.md`
   - `c:\Users\extra\OneDrive\Documents\vscode projects\Massa_Mesh\MASSA_BMESH_CONSOLE-main\.agent\SuperPow\skills\subagent-driven-development\SKILL.md`
   - `c:\Users\extra\OneDrive\Documents\vscode projects\Massa_Mesh\MASSA_BMESH_CONSOLE-main\.agent\SuperPow\skills\systematic-debugging\SKILL.md`
   - `c:\Users\extra\OneDrive\Documents\vscode projects\Massa_Mesh\MASSA_BMESH_CONSOLE-main\.agent\SuperPow\skills\test-driven-development\SKILL.md`
   - `c:\Users\extra\OneDrive\Documents\vscode projects\Massa_Mesh\MASSA_BMESH_CONSOLE-main\.agent\SuperPow\skills\verification-before-completion\SKILL.md`
   - `c:\Users\extra\OneDrive\Documents\vscode projects\Massa_Mesh\MASSA_BMESH_CONSOLE-main\.agent\SuperPow\skills\writing-plans\SKILL.md`
   - `c:\Users\extra\OneDrive\Documents\vscode projects\Massa_Mesh\MASSA_BMESH_CONSOLE-main\.agent\SuperPow\skills\writing-skills\SKILL.md`
4. Ask the user what they would like to build or start the `brainstorming` process immediately if a task was already provided.
