# Architecture Design

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Neona CLI                                │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Interactive │  │  Headless    │  │   Commands   │      │
│  │    TUI      │  │    Mode      │  │              │      │
│  │  (Primary)  │  │              │  │              │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  AI Provider Router (Custom API Support)            │   │
│  │  Format Translation | Request Routing | Fallback    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Control Plane Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Task    │  │  Policy  │  │  Router  │  │Scheduler │   │
│  │ Manager  │  │  Engine  │  │          │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │Executor  │  │  Rules   │  │Autonomous│                 │
│  │          │  │  Engine  │  │  Agent   │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Registry Layer                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │    AI    │  │  Skill   │  │  Policy  │  │ Workflow │   │
│  │ Registry │  │ Registry │  │ Registry │  │ Registry │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Connector Layer                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Claude  │  │  Letta   │  │ OpenCode │  │  9Router │   │
│  │   Code   │  │   Code   │  │          │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐                                │
│  │  Custom  │  │  Plugin  │                                │
│  │   AI     │  │  System  │                                │
│  └──────────┘  └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Audit Layer                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Event   │  │  Trace   │  │Evidence  │  │Analytics │   │
│  │  Logger  │  │ Storage  │  │Collector │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Task Execution Flow

```
User Request
    │
    ▼
CLI Command Parser
    │
    ▼
Task Manager (Create Task)
    │
    ▼
Policy Engine (Validate)
    │
    ▼
Router (Select AI)
    │
    ▼
Connector (Translate Command)
    │
    ▼
AI CLI Execution
    │
    ▼
Executor (Monitor & Collect)
    │
    ▼
Audit Layer (Log & Store)
    │
    ▼
Task Manager (Update Status)
    │
    ▼
User Notification
```

### Policy Resolution Flow

```
Task Request
    │
    ▼
Load Global Policy (.ai/policy.yaml)
    │
    ▼
Load Per-AI Policy (.ai/policy/<ai-id>.yaml) [if exists]
    │
    ▼
Load Per-Project Policy (<project>/.ai/policy.yaml) [if exists]
    │
    ▼
Merge Policies (AI > Project > Global)
    │
    ▼
Validate Against Task
    │
    ▼
Enforce Rules
```

### Skill Resolution Flow

```
Task Requires Skill
    │
    ▼
Check AI-Specific Skills (.ai/skills/<ai-id>/)
    │
    ▼
Check Shared Skills (.ai/skills/)
    │
    ▼
Load Skill Definition
    │
    ▼
Validate Dependencies
    │
    ▼
Inject into AI Context
    │
    ▼
Execute Task with Skill
```

## Component Responsibilities

### Control Plane

**Task Manager**
- Task lifecycle (create, claim, execute, complete, fail)
- State store (SQLite as default; file-based for prototype)
- Task lifecycle states: queued, claimed, running, blocked, done, failed
- Claim/lease model with TTL + heartbeat
- DAG dependency resolution
- Task state management
- Task queue and prioritization
- Locking: task-level, path/module-level (glob-based acceptable)

**Policy Engine**
- Policy loading and validation
- Rule enforcement
- Policy merging (hierarchical: Global → Project → AI)
- Policy Decision Record (PDR): Every enforced decision emits a traceable record

**Router**
- AI capability matching
- Load balancing
- Label-based routing
- Fallback selection

**Scheduler**
- Task queuing
- Priority-based execution
- Dependency resolution
- Retry strategies

**Executor**
- AI command translation
- Execution monitoring
- Evidence collection
- Failure handling

**Rules Engine**
- Rule DSL parsing
- Rule evaluation
- Rule conflict resolution
- Rule suggestions

**Autonomous Agent**
- Task queue monitoring
- Auto-claiming (with approval)
- Progress tracking
- Continuous operation

### Registry

**AI Registry**
- AI instance registration
- Capability tracking
- Health monitoring
- Label management

**Skill Registry**
- Skill definitions
- Skill dependencies
- Version management
- Load/unload operations

**Policy Registry**
- Policy storage
- Policy versioning
- Policy inheritance
- Policy validation

**Workflow Registry**
- Workflow definitions
- Workflow templates
- Workflow execution state
- Workflow versioning

**External Integration Registry** (Future)
- GitHub integration (token/HTTPS auth)
  - PR access and creation
  - Repository metadata
  - Issue management
  - Code reading and diff analysis
- Other external service integrations

**Marketplace** (Future)
- Skill marketplace
- Agent marketplace
- Smart routes marketplace

### Connector

**AI Connectors**
- v1: CLI-based connectors (process spawning, stdout/stderr parsing, evidence capture)
- v2: MCP-based gateways (future extension, not required for MVP)
- Format translation
- Response parsing

**Plugin System**
- Custom AI adapter interface
- Dynamic loading
- Configuration management
- Capability reporting

### Audit

**Event Logger**
- Structured event logging
- Event correlation
- Event filtering
- Event export

**Trace Storage**
- Request/response storage
- Trace correlation
- Trace querying
- Trace export

**Evidence Collector**
- Code diff collection
- Test result storage
- Log aggregation
- Evidence verification

**Analytics**
- Performance metrics
- Success rate tracking
- AI capability learning
- Workflow optimization

## Data Structures

### Task

```go
type Task struct {
    ID          string
    Description string
    Type        TaskType // single, workflow, dag
    Status      TaskStatus // queued, claimed, running, blocked, done, failed
    Priority    int
    Dependencies []string // Task IDs
    ClaimedBy   string   // AI ID
    ClaimedAt   time.Time
    ClaimTTL    time.Duration
    LastHeartbeat time.Time
    LockPaths   []string // Glob patterns for path-level locks
    CreatedAt   time.Time
    StartedAt   time.Time
    CompletedAt time.Time
    Evidence    Evidence
    Policy      PolicyRef
    Metadata    map[string]interface{}
}
```

### AI Instance

```go
type AIInstance struct {
    ID          string
    Type        string // claude-code, letta, opencode, custom
    Name        string
    Labels      []string
    Capabilities Capabilities
    Status      AIStatus // online, offline, error
    Config      map[string]interface{}
    Policy      PolicyRef
    Skills      []string
    LastSeen    time.Time
}
```

### Policy

```go
type Policy struct {
    Version     string
    Global      GlobalRules
    PerAI       map[string]AIRules
    Workflows   []WorkflowRule
    Constraints []Constraint
}
```

### Skill

```go
type Skill struct {
    ID          string
    Name        string
    Description string
    Version     string
    Capabilities []string
    Dependencies []string
    Code        string
    Config      map[string]interface{}
    Scope       SkillScope // global, ai-specific
}
```

## Configuration Schema

### `.ai/policy.yaml`

```yaml
version: "1.0"
global:
  task_execution:
    claim_required: true
    direct_main_write: false
    autonomous_task_creation: false
  safety:
    secrets_access: false
    speculative_changes: false
  completion:
    evidence_required: true
per_ai:
  "ai-claude-001":
    task_execution:
      autonomous_task_creation: true
workflows:
  - name: "code-review"
    steps:
      - type: "analyze"
        ai: "ai-claude-001"
      - type: "test"
        ai: "ai-opencode-001"
```

### `.ai/skills/<skill-id>.yaml`

```yaml
id: "skill-code-review"
name: "Code Review"
description: "Review code for bugs and improvements"
version: "1.0.0"
capabilities:
  - "code-analysis"
  - "bug-detection"
dependencies:
  - "skill-read-files"
code: |
  function review(files) {
    // skill implementation
  }
```

## Integration Points

### AI CLI Integration

**Claude Code**
- CLI invocation: `claude-code <command>`
- Response parsing: stdout/stderr capture
- Evidence: file diffs, test results

**Letta Code**
- CLI invocation: `letta -p "<prompt>"`
- API integration (if available)
- Evidence: agent messages, code changes

**OpenCode**
- CLI invocation: `opencode <command>`
- Task delegation: subagent system
- Evidence: task results, logs

**9Router**
- API proxy for routing
- Format translation
- Account management

**n8n**
- **Workflow Patterns**: Node-based execution, conditional branching, error handling, retry mechanisms
- **Node Concepts**: Input/output ports, data transformation, execution order, connection patterns
- **Integration Architecture**: Credential management, OAuth flows, API abstractions, webhook handling
- **Extensibility Mechanisms**: Custom node development, plugin system, community marketplace patterns

## External Integrations (Future)

### GitHub Integration
- Authentication: Token or HTTPS (OAuth)
- Capabilities:
  - Read repository metadata, code, diffs
  - Check PR status and details
  - Create PRs, comments, reviews
  - Access issues and labels
  - Repository structure inspection
- Integration with task system for PR-based workflows
- Use cases:
  - PR analysis tasks
  - Code review automation
  - Repository metadata queries
  - Issue tracking integration

### Marketplace (Future)
- **Skill Marketplace**: Discover and download community skills
- **Agent Marketplace**: Pre-configured agents with specific capabilities
- **Smart Routes Marketplace**: Community-contributed routing patterns
- **Curation**: Verification and categorization system
- **Versioning**: Marketplace item versioning and updates
- **Dependency Resolution**: Marketplace package dependencies

### Integration Patterns (Inspired by n8n)
- **Credential Management**: Secure token storage, OAuth flows, scope management
- **API Abstractions**: Unified interface for external services
- **Webhook Support**: Event-driven task triggers
- **Extensibility**: Plugin system for custom integrations

## Security Considerations

1. **Secrets Management**: Never store API keys in policy files
   - GitHub tokens stored securely (OS keychain or encrypted config)
2. **Access Control**: Task claiming requires authentication
3. **Policy Enforcement**: Cannot bypass policy constraints
4. **Audit Integrity**: All operations logged, cannot be tampered
5. **Sandboxing**: AI executions isolated from system
6. **External API Security**: Token rotation, scope limits, rate limiting

## Performance Considerations

1. **Connection Pooling**: Reuse AI connections where possible
2. **Caching**: Cache policy and skill definitions
3. **Async Execution**: Non-blocking task execution
4. **Resource Limits**: CPU/memory limits per AI
5. **Batch Operations**: Group related tasks
