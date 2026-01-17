# Neona Roadmap Overview

## Vision

Neona is a CLI-centric multi-AI orchestration system that unifies local AI tools (Claude Code, Letta Code, OpenCode, 9Router, etc.) under a single control plane. It enables users to manage rules, policies, skills, and workflows across all connected AIs, while supporting both shared configurations and individual AI-specific settings.

## Core Principles

1. **Unified Control Plane**: Single CLI interface to manage all local AI tools
2. **Multi-AI Orchestration**: Coordinate tasks across multiple AI agents
3. **Policy-Driven**: Centralized rules and policies with per-AI overrides
4. **Task-Based Execution**: DAG-friendly task management with autonomous execution
5. **Skill Registry**: Shared and AI-specific skills that can be dynamically loaded
6. **Workflow Management**: User-defined workflows with smart routing and delegation
7. **Continuous Operation**: Autonomous task execution with monitoring and auditing

## Key Insights from Reference Repositories

### 9Router (API Routing & Proxy)
- **Pattern**: Format translation, provider abstraction, account management
- **Takeaways**: Multi-provider support, request/response transformation, fallback mechanisms
- **Application**: Neona can route tasks to appropriate AI providers based on capabilities

### Claude-Mem (Memory & Context)
- **Pattern**: Persistent memory, context injection, folder-level knowledge
- **Takeaways**: SQLite storage, session management, context compression
- **Application**: Neona can maintain shared knowledge base and AI-specific memory

### Letta-Code (Agent Management)
- **Pattern**: Persistent agents, subagents, skills, approval workflows
- **Takeaways**: Agent lifecycle, skill system, TUI interface, permission management
- **Application**: Neona can manage multiple AI instances with individual configurations

### OpenCode (Multi-Agent Tasks)
- **Pattern**: Task delegation, agent orchestration, tool management
- **Takeaways**: Subagent system, tool descriptions, concurrent execution
- **Application**: Neona can delegate complex tasks across specialized AI agents

### n8n (Workflow Orchestration)
- **Pattern**: Node-based workflows, execution order, connection patterns, extensibility
- **Takeaways**: Visual workflow composition, node execution engine, integration marketplace, conditional branching, error handling
- **Application**: Neona can adopt workflow patterns, node concepts for task composition, and extensibility mechanisms for connectors and integrations

### n8n (Workflow Automation)
- **Pattern**: Visual workflow editor, 400+ integrations, AI-native capabilities
- **Takeaways**: Node-based workflow design, integration marketplace, extensible architecture
- **Application**: Neona can leverage workflow patterns and integration concepts for task orchestration

## Architecture Components

```
Neona CLI
├── Control Plane (internal/controlplane/)
│   ├── Task Manager: DAG task creation, claiming, execution tracking
│   ├── Policy Engine: Rule enforcement, validation, compliance
│   ├── Router: AI selection, load balancing, capability matching
│   └── Scheduler: Task queuing, prioritization, autonomous execution
├── Registry (internal/registry/)
│   ├── AI Registry: Connected AI instances, capabilities, labels
│   ├── Skill Registry: Shared and AI-specific skills
│   ├── Policy Registry: Global and per-AI policies
│   └── Workflow Registry: User-defined workflows and patterns
├── Audit (internal/audit/)
│   ├── Event Logger: Task execution events
│   ├── Trace Storage: Request/response traces
│   └── Evidence Collection: Code diffs, test results, logs
└── CLI (cmd/neona/)
    ├── Interactive Mode: TUI for task management
    ├── Headless Mode: API for external tools
    └── Command Interface: Task creation, AI management, workflow control
```

## Future Features (Post-MVP)

### External Integrations
- **GitHub Integration**: Connect via token or HTTPS authentication
  - Check PRs, repositories, issues
  - Read code, diff analysis
  - Create PRs, comments, reviews
  - Repository metadata access

### Marketplace
- **Skill Marketplace**: Download and share skills
- **Agent Marketplace**: Discover and deploy pre-configured agents
- **Smart Routes Marketplace**: Community-contributed routing patterns
- Access to curated collections of workflows, skills, and agents

## Success Metrics

- Can connect to at least 3 different AI CLI tools
- Supports per-AI policy overrides
- Enables autonomous task execution with monitoring
- Provides workflow management with smart routing
- Maintains audit trail for all operations
- Supports both shared and AI-specific skills
