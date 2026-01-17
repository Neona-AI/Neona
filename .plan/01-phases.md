# Development Phases

**Note**: Neona is NOT time-boxed. Execution speed is unconstrained. Phases are ordered but not time-coupled.

## Phase 0: Foundation (Current)
**Status**: ✅ In Progress

### Goals
- [x] Repository structure setup
- [x] Configuration system (`.ai/` directory)
- [x] Policy framework definition
- [ ] Go module initialization

### Deliverables
- [x] Directory structure (cmd/, internal/, .ai/)
- [x] Policy YAML schema
- [x] System and role prompts
- [ ] Basic CLI scaffold

---

## Phase 1: Core Control Plane

**MVP Requirement**: Phase 1 must be complete before meaningful execution exists.

### Goals
- Task management system (create, claim, execute, track)
- Policy engine (load, validate, enforce)
- Basic audit logging
- CLI command structure

### Components

#### 1.1 Task Manager (`internal/controlplane/task/`)
- Task data structures (DAG support)
- State store (SQLite as default; file-based allowed for prototype)
- Task lifecycle states: queued, claimed, running, blocked, done, failed
- Claim/lease model with TTL + heartbeat
- Task queue and prioritization
- Locking at minimum:
  - Task-level locks
  - Path/module-level locks (glob-based acceptable)

#### 1.2 Policy Engine (`internal/controlplane/policy/`)
- Policy loader from `.ai/policy.yaml`
- Policy validator
- Rule enforcement hooks
- Policy override system (per-AI)
- Policy Decision Record (PDR): Every enforced decision must emit a traceable record

#### 1.3 Audit System (`internal/audit/`)
- Event logger (structured logging)
- Trace storage (request/response)
- Evidence collector (diffs, tests, logs)

#### 1.4 CLI Foundation (`cmd/neona/`)
- Command structure (cobra/spf13)
- TUI mode (primary interface, like OpenCode/Letta-Code)
- Basic commands (available in both TUI and CLI):
  - `neona task create <description>` or `/task create`
  - `neona task list` or `/task list`
  - `neona task claim <id>` or `/task claim <id>`
  - `neona policy validate` or `/policy validate`
- AI provider routing system (custom API support)

### Acceptance Criteria
- Can create tasks via CLI
- Tasks can be claimed by worker (manual)
- Policy violations are logged
- Audit trail captures all operations

---

## Phase 2: AI Integration Layer

**MVP Scope**: Phase 2 is intentionally minimal and non-generalized. Initially targets ONE connector only.

### Goals
- Connect to one AI CLI tool (initially)
- AI registry and discovery
- Capability detection and routing
- Basic task execution

### Components

#### 2.1 AI Registry (`internal/registry/ai/`)
- AI instance registration
- Capability detection (tools, models, skills)
- Health checking
- Label system (user-defined tags)

#### 2.2 Connector Framework (`internal/controlplane/connector/`)
- Interface for AI CLI integration
- v1: CLI-based connectors
  - Process spawning
  - stdout/stderr parsing
  - Evidence capture
- v2: MCP-based gateways (future extension, not required for MVP)
- Command translation layer

#### 2.3 Router (`internal/controlplane/router/`)
- Task-to-AI matching based on:
  - Capabilities (required tools/skills)
  - Labels (user preferences)
  - Load balancing
  - Policy constraints
- Fallback mechanisms

#### 2.4 Task Executor (`internal/controlplane/executor/`)
- Execute tasks via connected AIs
- Monitor execution status
- Collect evidence (output, diffs)
- Handle failures and retries

### CLI Commands
- `neona ai register <name> <type> <config>`
- `neona ai list`
- `neona ai label <id> <tags...>`
- `neona task execute <id> --ai <id>`

### Acceptance Criteria
- Can register at least one AI type (initially)
- Tasks can be routed to the registered AI
- Evidence collection works for executed tasks
- Labels can be applied and used for routing

---

## Phase 3: Policy & Rules System

### Goals
- Per-AI policy overrides
- Workflow rules and patterns
- Policy validation and compliance checking
- Smart rule creation/modification

### Components

#### 3.1 Policy Override System (`internal/registry/policy/`)
- Hierarchical policy structure:
  - Global (`.ai/policy.yaml`)
  - Per-AI (`.ai/policy/<ai-id>.yaml`)
  - Per-project (`<project>/.ai/policy.yaml`)
- Policy inheritance and merging
- Policy Decision Record (PDR): Every enforced decision emits a traceable record

#### 3.2 Rule Engine (`internal/controlplane/rules/`)
- Rule DSL for workflow patterns
- Rule evaluation engine
- Rule suggestions (AI-assisted)
- Rule conflict resolution

#### 3.3 Workflow Definition (`internal/registry/workflow/`)
- Workflow YAML format
- DAG workflow support
- Conditional branching
- Loop and retry patterns

### CLI Commands
- `neona policy show [--ai <id>]`
- `neona policy override <ai-id> <rule> <value>`
- `neona workflow create <name> <file>`
- `neona workflow suggest <description>` (AI-assisted)

### Acceptance Criteria
- Policies can be overridden per-AI
- Workflows can be defined and executed
- Rule engine evaluates policies correctly
- Smart suggestions help users create workflows

---

## Phase 4: Skill System

### Goals
- Shared skill registry
- Per-AI skill management
- Skill discovery and loading
- Skill composition and chaining

### Components

#### 4.1 Skill Registry (`internal/registry/skill/`)
- Skill definition format (YAML + code)
- Skill metadata (capabilities, requirements)
- Skill versioning
- Skill dependencies

#### 4.2 Skill Loader (`internal/registry/skill/loader/`)
- Load skills from `.ai/skills/`
- Load AI-specific skills from `.ai/skills/<ai-id>/`
- Dynamic skill injection
- Skill validation

#### 4.3 Skill Execution (`internal/controlplane/skill/`)
- Skill invocation interface
- Skill chaining/composition
- Skill context passing
- Skill result aggregation

### CLI Commands
- `neona skill list [--ai <id>]`
- `neona skill add <path> [--ai <id>]`
- `neona skill enable <id> [--ai <id>]`
- `neona skill test <id>`

### Acceptance Criteria
- Shared skills available to all AIs
- AI-specific skills override shared ones
- Skills can be composed and chained
- Skill execution produces evidence

---

## Phase 5: Autonomous Execution

### Goals
- Continuous task monitoring
- Autonomous task creation (user-approved)
- Smart task routing and delegation
- Background execution with notifications

### Components

#### 5.1 Scheduler (`internal/controlplane/scheduler/`)
- Task queue management
- Priority-based scheduling
- Dependency resolution (DAG)
- Retry and backoff strategies

#### 5.2 Autonomous Agent (`internal/controlplane/autonomous/`)
- Monitor task queue
- Detect task dependencies
- Auto-claim tasks (with approval)
- Progress reporting

#### 5.3 Notification System (`internal/audit/notify/`)
- Task completion notifications
- Error alerts
- Progress updates
- Integration hooks (webhook, email, etc.)

### CLI Commands
- `neona daemon start`
- `neona daemon stop`
- `neona daemon status`
- `neona task watch [--filter <criteria>]`

### Acceptance Criteria
- Tasks can execute autonomously with approval
- DAG dependencies are resolved correctly
- Notifications work for task completion
- Daemon runs continuously without issues

---

## Phase 6: Advanced Features

### Goals
- Workflow visualization
- AI capability learning
- Performance analytics
- Multi-project orchestration

### Components

#### 6.1 Analytics (`internal/audit/analytics/`)
- Task execution metrics
- AI performance tracking
- Skill usage statistics
- Workflow success rates

#### 6.2 Learning System (`internal/controlplane/learning/`)
- Track AI capabilities over time
- Learn optimal task-to-AI mappings
- Suggest workflow improvements
- Predict task requirements

#### 6.3 UI Enhancements (`cmd/neona/ui/`)
- TUI improvements (inspired by Letta-Code)
- Workflow visualization
- Real-time task monitoring
- Interactive policy editor

### CLI Commands
- `neona analytics show [--ai <id>]`
- `neona workflow visualize <name>`
- `neona learn optimize`
- `neona project add <path>`

### Acceptance Criteria
- Analytics provide actionable insights
- Workflows can be visualized
- Learning system improves routing over time
- Multi-project orchestration works

---

## Phase 7: Production Readiness

### Goals
- Performance optimization
- Security hardening
- Documentation completion
- Integration testing

### Components

#### 7.1 Performance
- Task execution optimization
- Connection pooling for AIs
- Caching strategies
- Resource limits

#### 7.2 Security
- Secrets management
- Access control
- Audit log integrity
- Policy enforcement hardening

#### 7.3 Documentation
- User guides
- API documentation
- Workflow examples
- Troubleshooting guides

### Acceptance Criteria
- Performance meets requirements (< 100ms overhead)
- Security audit passes
- Documentation is complete
- Integration tests pass

---

## Phase 8: External Integrations (Future)

### Goals
- GitHub integration for repository and PR management
- Marketplace for skills, agents, and smart routes
- Workflow orchestration patterns inspired by n8n
- Additional external service integrations

### Components

#### 8.1 GitHub Integration (`internal/integrations/github/`)
- Authentication: Token or HTTPS (OAuth)
- Repository access: Read code, metadata, structure
- PR management: Check status, create PRs, comments, reviews
- Issue management: Read, create, update issues
- Diff analysis: Parse and analyze code changes
- Integration with task system for PR-based workflows

#### 8.2 Marketplace (`internal/marketplace/`)
- Skill Marketplace: Discover and download community skills
- Agent Marketplace: Pre-configured agents with capabilities
- Smart Routes Marketplace: Community-contributed routing patterns
- Curation system: Verification and categorization
- Versioning and updates for marketplace items
- Dependency resolution for marketplace packages
- Extensibility mechanisms for custom integrations (inspired by n8n's node system)

#### 8.3 Workflow Orchestration Patterns (Inspired by n8n)
- Node-based workflow composition concepts
- Conditional branching and error handling patterns
- Execution order management and connection patterns
- Integration architecture: Credential management, OAuth flows, API abstractions
- Webhook support for event-driven task triggers

### CLI Commands
- `neona github connect [--token <token>] [--oauth]`
- `neona github pr check <owner>/<repo> <pr-number>`
- `neona github repo list`
- `neona marketplace browse [skills|agents|routes]`
- `neona marketplace install <type> <id>`
- `neona marketplace publish <type> <path>`

### Acceptance Criteria
- GitHub connection works via token or OAuth
- Can check PRs and repository metadata
- Marketplace can browse and install skills/agents/routes
- Marketplace items integrate with Neona's registry system
