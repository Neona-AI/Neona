# Neona

A CLI-centric AI Control Plane that coordinates multiple AI tools (Cursor, AntiGravity, Zencoder, Claude CLI) to execute multi-step tasks under shared rules, knowledge, and policy.

## What Neona Is

Neona is an orchestration system that:
- Coordinates task-based execution across AI agents
- Enforces shared policy and knowledge
- Provides audit trails and evidence collection
- Connects IDE AIs as external workers

## What Neona Is NOT

- Not a standalone application
- Not a business logic execution engine
- Not a secret management system
- Not an autonomous task creator

## Interface

**CLI is the primary interface.** All coordination happens through the `neona` command-line tool.

## Agent Integration

IDE AIs (Cursor, AntiGravity, Zencoder, Claude CLI) connect as external agents through the CLI. They claim tasks, execute under shared policy, and provide evidence for completion.

## Configuration

Policy, prompts, and knowledge are stored in `.ai/` directory and serve as the single source of truth for all agents.
