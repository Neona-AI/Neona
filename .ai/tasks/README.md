# Tasks Directory

This directory contains task definitions and execution history for Neona.

## Task Lifecycle

1. Tasks are created by Planner agents
2. Tasks are stored here or in the task system
3. Workers claim tasks from this registry
4. Execution evidence is stored with task records

## Format

Tasks should include:
- Task ID and description
- Dependencies
- Acceptance criteria
- Claimed by (agent)
- Status and evidence
