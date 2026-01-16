# Neona Overview

## What Neona Is

Neona is a CLI-centric AI Control Plane that orchestrates multiple AI tools (Cursor, AntiGravity, Zencoder, Claude CLI) to coordinate, claim, and execute multi-step tasks under shared rules, knowledge, and policy.

## Architecture

Neona operates as an orchestration system, not an application. It provides:

- **Task Management**: Task creation, claiming, and execution tracking
- **Policy Enforcement**: Centralized policy through `.ai/policy.yaml`
- **Knowledge Sharing**: Shared prompts and knowledge via `.ai/` directory
- **Event Tracking**: Audit logs, traces, and evidence storage

## Key Components

- `internal/controlplane/`: Task, policy, routing coordination
- `internal/registry/`: Prompts, knowledge, skills registry
- `internal/audit/`: Events, traces, evidence storage
- `cmd/neona/`: CLI entry point

## Integration Model

IDE AIs connect as external agents. They interact with Neona through the CLI interface to claim and execute tasks under shared policy and knowledge.
