# Repository Structure Map

## Directory Purpose

```
/neona
 ├─ cmd/
 │   └─ neona/            # CLI entry point (scaffold)
 │
 ├─ internal/
 │   ├─ controlplane/     # Task coordination, policy routing
 │   ├─ registry/         # Prompts, knowledge, skills registry
 │   └─ audit/            # Events, traces, evidence storage
 │
 └─ .ai/                  # Shared AI configuration
     ├─ policy.yaml       # Single source of truth for policy
     ├─ prompts/          # System and role prompts
     ├─ knowledge/        # Shared knowledge base
     └─ tasks/            # Task definitions and history
```

## Module Boundaries

- **controlplane/**: Task lifecycle, policy enforcement, routing
- **registry/**: Prompt templates, knowledge base, skill definitions
- **audit/**: Event logging, trace storage, evidence collection
- **cmd/neona/**: CLI interface and command routing

## File Conventions

- Policy: `.ai/policy.yaml`
- System prompts: `.ai/prompts/system.md`
- Role prompts: `.ai/prompts/roles/*.md`
- Knowledge: `.ai/knowledge/*.md`
- Tasks: `.ai/tasks/*.md` or task system
