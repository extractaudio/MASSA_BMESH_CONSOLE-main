---
name: finishing-a-development-task
description: Use when implementation is complete and all tests pass to finalize the work on the main branch.
---

# Finishing a Development Task

## Overview

Guide completion of development work by ensuring tests pass and changes are safely committed.
Since we are working directly on the main branch, we do NOT use worktrees or separate branches.

**Announce at start:** "I'm using the finishing-a-development-task skill to complete this work."

## The Process

### Step 1: Verify Tests

**Before finalizing, verify tests pass:**

```bash
# Run project's test suite
npm test / cargo test / pytest / go test ./...
```

**If tests fail:**
```
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed until tests pass.
```

Stop. Don't proceed to Step 2.

### Step 2: Review Changes

Review the local uncommitted changes:
```bash
git status
git diff
```

### Step 3: Present Options

**Present exactly these options:**

```
Implementation complete. What would you like to do?

1. Commit changes locally
2. Commit and push changes
3. Keep the changes uncommitted (I'll handle it later)
4. Discard this work (git reset --hard)

Which option?
```

### Step 4: Execute Choice

#### Option 1: Commit Locally

```bash
git add .
git commit -m "feat: <summary of work>"
```

#### Option 2: Commit and Push

```bash
git add .
git commit -m "feat: <summary of work>"
git push
```

#### Option 3: Keep As-Is

Report: "Keeping changes uncommitted."

#### Option 4: Discard

**Confirm first:**
```
This will permanently delete all uncommitted changes.
Type 'discard' to confirm.
```

If confirmed:
```bash
git reset --hard
```

## Quick Reference

| Option | Commit | Push | Discard |
|--------|-------|------|----------------|
| 1. Commit locally | yes | - | - |
| 2. Commit & Push | yes | yes | - |
| 3. Keep uncommitted | - | - | - |
| 4. Discard | - | - | yes |

## Red Flags

**Never:**
- Proceed with failing tests
- Discard work without confirmation
- Create new branches or worktrees

**Always:**
- Verify tests before offering options
- Present exactly 4 options
- Get typed confirmation for Option 4
