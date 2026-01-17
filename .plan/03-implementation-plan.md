# Implementation Plan

## Phase 1: Core Control Plane

### Task 1.1: Project Setup

- [ ] Initialize Go module with dependencies
- [ ] Set up build system (Makefile)
- [ ] Configure linting and formatting (golangci-lint)
- [ ] Set up basic testing framework
- [ ] Create project structure documentation

**Dependencies**: None
**Deliverables**: Working Go project with basic tooling

---

### Task 1.2: Task Data Structures

- [ ] Define `Task` struct with all fields (including claim TTL, heartbeat, lock paths)
- [ ] Define `TaskStatus` enum (queued, claimed, running, blocked, done, failed)
- [ ] Define `TaskType` enum
- [ ] Implement task serialization (JSON)
- [ ] Write unit tests for task operations

**Dependencies**: Task 1.1
**Deliverables**: Task package with types and serialization

---

### Task 1.3: Task Manager Core

- [ ] Implement state store (SQLite as default; file-based for prototype)
- [ ] Implement task creation
- [ ] Implement task claiming with claim/lease model (TTL + heartbeat)
- [ ] Implement task-level locking
- [ ] Implement path/module-level locking (glob-based acceptable)
- [ ] Implement task state transitions (queued → claimed → running → done/failed)
- [ ] Implement blocked state handling (dependency waiting)
- [ ] Implement task queue (priority-based)
- [ ] Implement DAG dependency resolution
- [ ] Write integration tests

**Dependencies**: Task 1.2
**Deliverables**: Functional task manager with queue and DAG support

---

### Task 1.4: Policy Engine Core

- [ ] Define policy YAML schema
- [ ] Implement policy loader from `.ai/policy.yaml`
- [ ] Implement policy validator
- [ ] Implement basic rule enforcement
- [ ] Implement Policy Decision Record (PDR) system: every enforced decision emits traceable record
- [ ] Write unit tests for policy operations

**Dependencies**: Task 1.1
**Deliverables**: Policy engine that loads and validates policies

---

### Task 1.5: Audit System Foundation

- [ ] Define event types
- [ ] Implement event logger
- [ ] Implement trace storage (file-based initially)
- [ ] Implement evidence collector interface
- [ ] Write unit tests

**Dependencies**: Task 1.1
**Deliverables**: Basic audit logging system

---

### Task 1.6: CLI Foundation

- [ ] Set up CLI framework (cobra)
- [ ] Implement basic command structure
- [ ] Implement `task create` command
- [ ] Implement `task list` command
- [ ] Implement `task claim` command
- [ ] Implement `policy validate` command
- [ ] Write CLI tests

**Dependencies**: Tasks 1.3, 1.4
**Deliverables**: Working CLI with basic task and policy commands

**Acceptance Criteria**: Can create tasks, list them, claim them, and validate policies via CLI

---

## Phase 2: AI Integration Layer

**MVP Scope**: Phase 2 is intentionally minimal and non-generalized. Initially targets ONE connector only.

### Task 2.1: AI Registry Foundation

- [ ] Define `AIInstance` struct
- [ ] Implement AI registration
- [ ] Implement AI listing
- [ ] Implement AI status tracking
- [ ] Write unit tests

**Dependencies**: Task 1.1
**Deliverables**: AI registry with basic CRUD operations

---

### Task 2.2: Connector Interface

- [ ] Define `Connector` interface
- [ ] Define `Capabilities` struct
- [ ] Define connector configuration format
- [ ] Document v1 (CLI-based) vs v2 (MCP-based, future) connector distinction
- [ ] Write interface documentation

**Dependencies**: Task 2.1
**Deliverables**: Connector interface specification

---

### Task 2.3: Claude Code Connector (v1 CLI-based)

- [ ] Implement process spawning for Claude Code CLI
- [ ] Implement stdout/stderr parsing
- [ ] Implement command translation
- [ ] Implement capability detection
- [ ] Implement evidence capture (diffs, test results)
- [ ] Write integration tests

**Dependencies**: Task 2.2
**Deliverables**: Working Claude Code connector

---

### Task 2.4: Router Implementation

- [ ] Implement capability matching
- [ ] Implement label-based routing
- [ ] Implement load balancing (minimal for MVP)
- [ ] Write unit tests

**Dependencies**: Tasks 2.1, 2.3
**Deliverables**: Router that selects appropriate AI for tasks

---

### Task 2.5: Task Executor

- [ ] Implement task execution via connector
- [ ] Implement execution monitoring
- [ ] Implement evidence collection
- [ ] Implement failure handling
- [ ] Implement retry logic
- [ ] Write integration tests

**Dependencies**: Tasks 2.4, 1.3
**Deliverables**: Executor that runs tasks on AIs and collects evidence

---

### Task 2.6: CLI AI Management Commands

- [ ] Implement `ai register` command
- [ ] Implement `ai list` command
- [ ] Implement `ai label` command
- [ ] Implement `task execute` command
- [ ] Write CLI tests

**Dependencies**: Tasks 2.5, 1.6
**Deliverables**: CLI commands for AI management and task execution

**Acceptance Criteria**: Can register AIs, label them, and execute tasks on them via CLI

---

## Phase 3: Policy & Rules System

### Task 3.1: Policy Override System

- [ ] Implement policy hierarchy (Global → Project → AI)
- [ ] Implement policy merging logic
- [ ] Implement Policy Decision Record (PDR) tracking for overrides
- [ ] Implement policy override commands
- [ ] Write unit tests

**Dependencies**: Task 1.4
**Deliverables**: Policy system with hierarchical overrides

---

### Task 3.2: Rule Engine Foundation

- [ ] Define rule DSL syntax
- [ ] Implement rule parser
- [ ] Implement rule evaluator
- [ ] Implement rule conflict detection
- [ ] Write unit tests

**Dependencies**: Task 3.1
**Deliverables**: Rule engine that evaluates workflow rules

---

### Task 3.3: Workflow Definition System

- [ ] Define workflow YAML schema
- [ ] Implement workflow loader
- [ ] Implement DAG workflow parsing
- [ ] Implement conditional branching
- [ ] Write unit tests

**Dependencies**: Task 3.2
**Deliverables**: Workflow definition system with DAG support

---

### Task 3.4: Workflow Execution Engine

- [ ] Implement workflow execution
- [ ] Implement step-by-step execution
- [ ] Implement conditional branching logic
- [ ] Implement retry loops
- [ ] Implement workflow state management
- [ ] Write integration tests

**Dependencies**: Tasks 3.3, 2.6
**Deliverables**: Workflow execution engine

---

### Task 3.5: CLI Workflow Commands

- [ ] Implement `workflow create` command
- [ ] Implement `workflow list` command
- [ ] Implement `workflow execute` command
- [ ] Implement `workflow suggest` command (stub)
- [ ] Write CLI tests

**Dependencies**: Task 3.4
**Deliverables**: CLI commands for workflow management

**Acceptance Criteria**: Can create workflows, execute them, and use policy overrides

---

## Phase 4: Skill System

### Task 4.1: Skill Definition System

- [ ] Define skill YAML schema
- [ ] Implement skill loader
- [ ] Implement skill metadata validation
- [ ] Implement dependency resolution
- [ ] Write unit tests

**Dependencies**: Task 1.1
**Deliverables**: Skill definition and loading system

---

### Task 4.2: Skill Registry

- [ ] Implement shared skill registry (`.ai/skills/`)
- [ ] Implement per-AI skill registry (`.ai/skills/<ai-id>/`)
- [ ] Implement skill discovery
- [ ] Implement skill versioning
- [ ] Write unit tests

**Dependencies**: Task 4.1
**Deliverables**: Skill registry with scoping (global vs AI-specific)

---

### Task 4.3: Skill Execution System

- [ ] Implement skill invocation interface
- [ ] Implement skill context passing
- [ ] Implement skill chaining
- [ ] Implement skill result aggregation
- [ ] Write integration tests

**Dependencies**: Tasks 4.2, 2.6
**Deliverables**: Skill execution system

---

### Task 4.4: Skill Injection for AIs

- [ ] Implement skill injection into AI context
- [ ] Implement connector-specific skill formatting
- [ ] Implement skill dependency injection
- [ ] Write integration tests

**Dependencies**: Tasks 4.3, 2.3, 2.4
**Deliverables**: Skills can be injected into AI execution context

---

### Task 4.5: CLI Skill Commands

- [ ] Implement `skill list` command
- [ ] Implement `skill add` command
- [ ] Implement `skill enable` command
- [ ] Implement `skill test` command
- [ ] Write CLI tests

**Dependencies**: Task 4.4
**Deliverables**: CLI commands for skill management

**Acceptance Criteria**: Can manage skills (shared and AI-specific) and they are injected into AI context

---

## Phase 5: Autonomous Execution

### Task 5.1: Scheduler Implementation

- [ ] Implement priority-based task queue
- [ ] Implement dependency resolution for scheduling
- [ ] Implement retry strategies
- [ ] Implement backoff mechanisms
- [ ] Write unit tests

**Dependencies**: Task 1.3
**Deliverables**: Task scheduler with priority and dependency support

---

### Task 5.2: Autonomous Agent

- [ ] Implement task queue monitoring
- [ ] Implement auto-claiming with approval mechanism
- [ ] Implement progress tracking
- [ ] Implement health checks
- [ ] Implement graceful shutdown
- [ ] Write integration tests

**Dependencies**: Tasks 5.1, 2.6
**Deliverables**: Autonomous agent that monitors and executes tasks

---

### Task 5.3: Notification System

- [ ] Define notification types
- [ ] Implement notification handlers
- [ ] Implement webhook support (stub)
- [ ] Implement console notifications
- [ ] Write unit tests

**Dependencies**: Task 1.5
**Deliverables**: Notification system for task events

---

### Task 5.4: Daemon Mode

- [ ] Implement daemon process management
- [ ] Implement daemon status reporting
- [ ] Implement daemon configuration
- [ ] Write integration tests

**Dependencies**: Tasks 5.2, 5.3
**Deliverables**: Daemon that runs continuously

---

### Task 5.5: CLI Daemon Commands

- [ ] Implement `daemon start` command
- [ ] Implement `daemon stop` command
- [ ] Implement `daemon status` command
- [ ] Implement `task watch` command
- [ ] Write CLI tests

**Dependencies**: Task 5.4
**Deliverables**: CLI commands for daemon management

**Acceptance Criteria**: Daemon runs continuously, auto-executes tasks with approval, and sends notifications

---

## Testing Strategy

### Unit Tests
- Each package should have >80% coverage
- Test edge cases and error conditions
- Mock external dependencies

### Integration Tests
- Test full workflows end-to-end
- Test with real AI CLI tools (if available)
- Test failure scenarios

### CLI Tests
- Test all commands with various inputs
- Test error handling
- Test help and documentation

### Performance Tests
- Task execution overhead should be < 100ms
- Concurrent task handling
- Memory usage under load

## Documentation Requirements

### Code Documentation
- All public APIs documented
- Architecture decisions documented
- Complex algorithms explained

### User Documentation
- Installation guide
- Quick start tutorial
- Command reference
- Workflow examples
- Troubleshooting guide

### Developer Documentation
- Contribution guidelines
- Architecture overview
- Extension points
- Testing guide

## Risk Mitigation

### Technical Risks
1. **AI CLI Changes**: Abstract connector interface to isolate changes
2. **Performance Issues**: Profile early, optimize bottlenecks
3. **Complexity**: Keep components focused, avoid over-engineering

### Integration Risks
1. **AI Tool Compatibility**: Version-specific connectors, feature detection
2. **Policy Conflicts**: Clear resolution rules, user warnings
3. **Skill Dependencies**: Dependency validation, clear error messages

### Operational Risks
1. **Data Loss**: Regular backups of audit logs and state
2. **Security Issues**: Security review, input validation, sandboxing
3. **Maintenance**: Clear architecture, good documentation, test coverage
