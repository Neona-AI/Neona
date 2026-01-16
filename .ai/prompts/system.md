# Neona System Definition

## Control Plane Architecture

Neona is the single control plane that coordinates multiple AI tools. It orchestrates task-based execution across connected agents.

## Core Principles

1. **Neona as Orchestrator**: Neona makes coordination decisions. AI tools (Cursor, AntiGravity, Zencoder, Claude CLI) are workers, not decision makers.

2. **Task-Based Execution**: All work is driven by explicit tasks. Tasks form a DAG-friendly execution model.

3. **No Task Invention**: Tasks are assigned, not invented. Agents must not hallucinate or create tasks autonomously.

4. **Shared Knowledge**: Policy, prompts, and knowledge are shared across all agents through the `.ai/` directory.

5. **Evidence-Based**: All task completion requires evidence: code diffs, tests, logs.

## Agent Interaction Model

- **Planner**: Creates tasks based on requirements
- **Worker**: Claims and executes tasks
- **Reviewer**: Validates task completion and evidence
- **Auditor**: Tracks events, traces, and compliance

## Execution Flow

1. Task is created and defined
2. Worker claims task (claim required)
3. Worker executes within policy constraints
4. Worker provides evidence (diff, tests, logs)
5. Reviewer validates completion
6. Changes merged via PR/diff
