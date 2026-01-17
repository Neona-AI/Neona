# AI Connection & Coordination Architecture

## Overview

Neona acts as the **central orchestrator** that connects multiple AI CLI tools. AIs do not connect directly to each other; they connect through Neona, which coordinates all interactions, enforces policies, and manages continuous task execution.

## Connection Model

```
┌─────────────────────────────────────────────────────────────┐
│                      Neona Control Plane                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Task Manager    │  Policy Engine  │  Router        │   │
│  │  State Store     │  PDR System     │  Scheduler     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         │                │                │                │
         ▼                ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Claude Code │  │ Letta Code  │  │ OpenCode    │  │ 9Router     │
│  (via CLI)  │  │  (via CLI)  │  │  (via CLI)  │  │  (API/CLI)  │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

**Key Principle**: AIs are **workers**, not coordinators. Neona makes all decisions.

## Connection Mechanisms

### Phase 2: CLI-Based Connectors (v1)

Each AI connects via its CLI interface:

#### Connection Flow

```
1. User registers AI:
   neona ai register claude-001 claude-code --path /usr/local/bin/claude-code

2. Neona stores connection config:
   - Type: "claude-code"
   - Executable path
   - Environment variables
   - Capabilities (detected)

3. Neona validates connection:
   - Executes: claude-code --version
   - Parses stdout for version/capability info
   - Stores in AI Registry (state store)
```

#### Command Execution

```go
type Connector interface {
    Execute(ctx context.Context, cmd Command) (*ExecutionResult, error)
    GetCapabilities() Capabilities
    HealthCheck() error
}

// CLI Connector Implementation
type CLIConnector struct {
    executable string
    env        map[string]string
    config     ConnectorConfig
}

func (c *CLIConnector) Execute(ctx context.Context, cmd Command) (*ExecutionResult, error) {
    // 1. Translate Neona command to AI CLI format
    cliCmd := c.translate(cmd)
    
    // 2. Spawn process with context
    proc := exec.CommandContext(ctx, c.executable, cliCmd.Args...)
    proc.Env = mergeEnv(c.env, cliCmd.Env)
    
    // 3. Capture stdout/stderr
    var stdout, stderr bytes.Buffer
    proc.Stdout = &stdout
    proc.Stderr = &stderr
    
    // 4. Execute with timeout
    err := proc.Run()
    
    // 5. Parse output for evidence
    evidence := c.collectEvidence(stdout.Bytes(), stderr.Bytes(), cmd)
    
    return &ExecutionResult{
        ExitCode: proc.ProcessState.ExitCode(),
        Stdout:   stdout.String(),
        Stderr:   stderr.String(),
        Evidence: evidence,
    }, err
}
```

#### Evidence Collection

Each connector must capture:
- **File diffs**: Track modified files (git diff before/after)
- **Test results**: Parse test output
- **Logs**: Capture stdout/stderr
- **Metadata**: Execution time, resource usage

## Policy Enforcement Architecture

### Policy Resolution Hierarchy

```
Task Execution Request
    │
    ▼
1. Load Global Policy (.ai/policy.yaml)
    │
    ▼
2. Load Per-AI Policy (.ai/policy/<ai-id>.yaml) [if exists]
    │
    ▼
3. Load Per-Project Policy (<project>/.ai/policy.yaml) [if exists]
    │
    ▼
4. Merge Policies (AI > Project > Global)
    │
    ▼
5. Validate Task Against Policy
    │
    ▼
6. Emit Policy Decision Record (PDR)
    │
    ▼
7. Enforce Rules Before/During/After Execution
```

### Policy Enforcement Points

#### Pre-Execution Validation

```go
func (tm *TaskManager) ClaimTask(taskID string, aiID string) error {
    // 1. Load merged policy for this AI
    policy := tm.policyEngine.GetMergedPolicy(aiID, task.Project)
    
    // 2. Validate task against policy
    if policy.TaskExecution.ClaimRequired && !task.ClaimedBy == "" {
        return ErrClaimRequired
    }
    
    // 3. Check secrets access policy
    if policy.Safety.SecretsAccess == false && task.RequiresSecrets() {
        return ErrSecretsAccessDenied
    }
    
    // 4. Emit PDR
    pdr := PolicyDecisionRecord{
        TaskID:    taskID,
        AIID:      aiID,
        Decision:  "ALLOW",
        Policy:    policy,
        Timestamp: time.Now(),
        Reason:    "All policy checks passed",
    }
    tm.audit.RecordPDR(pdr)
    
    // 5. Claim task with lock
    return tm.claimTaskWithLock(taskID, aiID)
}
```

#### During Execution Monitoring

```go
func (exec *Executor) ExecuteTask(ctx context.Context, task Task, connector Connector) error {
    // 1. Monitor for policy violations
    ctx, cancel := context.WithCancel(ctx)
    defer cancel()
    
    go exec.monitorPolicy(ctx, task, connector)
    
    // 2. Execute via connector
    result, err := connector.Execute(ctx, task.Command)
    
    // 3. Validate evidence against policy
    if task.Policy.Completion.EvidenceRequired {
        if !exec.validateEvidence(result.Evidence) {
            exec.audit.RecordPDR(PolicyDecisionRecord{
                Decision: "BLOCK",
                Reason:   "Insufficient evidence",
            })
            return ErrEvidenceRequired
        }
    }
    
    return nil
}

func (exec *Executor) monitorPolicy(ctx context.Context, task Task, connector Connector) {
    ticker := time.NewTicker(5 * time.Second)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            // Check for forbidden operations (e.g., direct main branch writes)
            if exec.detectPolicyViolation(task) {
                exec.audit.RecordPDR(PolicyDecisionRecord{
                    Decision: "BLOCK",
                    Reason:   "Policy violation detected during execution",
                })
                // Cancel execution
                return
            }
        }
    }
}
```

#### Post-Execution Validation

```go
func (tm *TaskManager) CompleteTask(taskID string, evidence Evidence) error {
    task := tm.getTask(taskID)
    policy := tm.policyEngine.GetMergedPolicy(task.ClaimedBy, task.Project)
    
    // 1. Validate evidence
    if !tm.validateEvidence(evidence, policy) {
        tm.audit.RecordPDR(PolicyDecisionRecord{
            Decision: "REJECT",
            Reason:   "Evidence validation failed",
        })
        return ErrEvidenceInvalid
    }
    
    // 2. Check for direct main writes (policy violation)
    if policy.TaskExecution.DirectMainWrite == false {
        if evidence.HasMainBranchChanges() {
            tm.audit.RecordPDR(PolicyDecisionRecord{
                Decision: "BLOCK",
                Reason:   "Direct main branch write detected",
            })
            return ErrDirectMainWrite
        }
    }
    
    // 3. Record completion with PDR
    tm.audit.RecordPDR(PolicyDecisionRecord{
        Decision: "APPROVE",
        Reason:   "Task completed within policy constraints",
    })
    
    return tm.markTaskComplete(taskID, evidence)
}
```

## State Management & Coordination

### State Store Architecture

**Default**: SQLite database (`~/.neona/state.db`)

```sql
-- Tasks table
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    status TEXT NOT NULL,  -- queued, claimed, running, blocked, done, failed
    claimed_by TEXT,       -- AI ID
    claimed_at TIMESTAMP,
    claim_ttl INTEGER,     -- seconds
    last_heartbeat TIMESTAMP,
    lock_paths TEXT,       -- JSON array of glob patterns
    dependencies TEXT,     -- JSON array of task IDs
    priority INTEGER,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    policy_ref TEXT,       -- Reference to policy used
    metadata TEXT          -- JSON
);

-- Policy Decision Records (PDR)
CREATE TABLE policy_decisions (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    ai_id TEXT NOT NULL,
    decision TEXT NOT NULL,  -- ALLOW, BLOCK, REJECT, APPROVE
    policy_snapshot TEXT,    -- JSON of policy state
    reason TEXT,
    timestamp TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- AI Registry
CREATE TABLE ai_instances (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,      -- claude-code, letta, opencode
    status TEXT NOT NULL,    -- online, offline, error
    labels TEXT,             -- JSON array
    capabilities TEXT,       -- JSON
    config TEXT,             -- JSON
    policy_override TEXT,    -- JSON (per-AI policy)
    last_seen TIMESTAMP
);

-- Task Locks
CREATE TABLE task_locks (
    task_id TEXT PRIMARY KEY,
    ai_id TEXT NOT NULL,
    locked_at TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Path Locks (module-level)
CREATE TABLE path_locks (
    id TEXT PRIMARY KEY,
    path_pattern TEXT NOT NULL,  -- glob pattern
    task_id TEXT NOT NULL,
    ai_id TEXT NOT NULL,
    locked_at TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

### Task Claiming & Locking

```go
// Claim with TTL and heartbeat
func (tm *TaskManager) ClaimTask(taskID string, aiID string, ttl time.Duration) error {
    tx, err := tm.db.Begin()
    if err != nil {
        return err
    }
    defer tx.Rollback()
    
    // 1. Check if task is claimable
    task := tm.getTaskLocked(tx, taskID)
    if task.Status != "queued" {
        return ErrTaskNotClaimable
    }
    
    // 2. Acquire task-level lock
    lock := TaskLock{
        TaskID:    taskID,
        AIID:      aiID,
        LockedAt:  time.Now(),
        ExpiresAt: time.Now().Add(ttl),
    }
    if err := tm.acquireTaskLock(tx, lock); err != nil {
        return err  // Lock already held
    }
    
    // 3. Acquire path-level locks (from task.lockPaths)
    for _, pattern := range task.LockPaths {
        if err := tm.acquirePathLock(tx, pattern, taskID, aiID, ttl); err != nil {
            // Release task lock and fail
            tm.releaseTaskLock(tx, taskID)
            return err
        }
    }
    
    // 4. Update task status
    task.Status = "claimed"
    task.ClaimedBy = aiID
    task.ClaimedAt = time.Now()
    task.ClaimTTL = ttl
    task.LastHeartbeat = time.Now()
    tm.updateTask(tx, task)
    
    return tx.Commit()
}

// Heartbeat to extend lease
func (tm *TaskManager) Heartbeat(taskID string, aiID string) error {
    // Update last_heartbeat and extend expires_at
    // If heartbeat missed > TTL, task becomes available again
}
```

## Continuous Task Execution

### Autonomous Agent Architecture

```go
type AutonomousAgent struct {
    taskManager *TaskManager
    scheduler   *Scheduler
    executor    *Executor
    router      *Router
    config      AgentConfig
}

func (agent *AutonomousAgent) Start(ctx context.Context) error {
    // Main loop: monitor queue and execute tasks
    for {
        select {
        case <-ctx.Done():
            return nil
        default:
            // 1. Get next claimable task (DAG-aware)
            task := agent.scheduler.GetNextTask()
            if task == nil {
                time.Sleep(1 * time.Second)
                continue
            }
            
            // 2. Route to appropriate AI
            aiID := agent.router.SelectAI(task)
            if aiID == "" {
                // No suitable AI available
                continue
            }
            
            // 3. Claim task (with approval mechanism)
            if !agent.config.AutoClaim {
                // Require user approval
                if !agent.waitForApproval(task, aiID) {
                    continue
                }
            }
            
            // 4. Execute task
            go agent.executeTaskAsync(ctx, task, aiID)
        }
    }
}

func (agent *AutonomousAgent) executeTaskAsync(ctx context.Context, task Task, aiID string) {
    // 1. Claim task
    if err := agent.taskManager.ClaimTask(task.ID, aiID, 30*time.Minute); err != nil {
        agent.logError(err)
        return
    }
    
    // 2. Get connector
    connector := agent.connectors.Get(aiID)
    
    // 3. Execute with monitoring
    evidence, err := agent.executor.ExecuteTask(ctx, task, connector)
    
    // 4. Update task status
    if err != nil {
        agent.taskManager.MarkTaskFailed(task.ID, err)
    } else {
        agent.taskManager.CompleteTask(task.ID, evidence)
    }
    
    // 5. Process dependent tasks (DAG)
    agent.scheduler.OnTaskComplete(task.ID)
}
```

### DAG Execution Flow

```
Task A (queued)
    │
    ├─> Task B (blocked, depends on A)
    │
    └─> Task C (blocked, depends on A)
        │
        └─> Task D (blocked, depends on C)

Execution Order:
1. Claim and execute Task A
2. On A completion, unblock B and C
3. Claim and execute B and C (parallel if possible)
4. On C completion, unblock D
5. Claim and execute D
```

```go
func (s *Scheduler) GetNextTask() *Task {
    // 1. Query tasks with status="queued" AND all dependencies completed
    query := `
        SELECT t.* FROM tasks t
        WHERE t.status = 'queued'
        AND NOT EXISTS (
            SELECT 1 FROM tasks d
            WHERE d.id = json_each.value
            AND json_each.value IN (SELECT json_each.value FROM json_each(t.dependencies))
            AND d.status != 'done'
        )
        ORDER BY t.priority DESC, t.created_at ASC
        LIMIT 1
    `
    
    // 2. Return highest priority, earliest created task
}
```

## Rules Application

### Global Rules

All AIs inherit from `.ai/policy.yaml`:

```yaml
global:
  task_execution:
    claim_required: true
    direct_main_write: false
  safety:
    secrets_access: false
```

### Per-AI Rules

Override for specific AI in `.ai/policy/<ai-id>.yaml`:

```yaml
# Allow this AI to auto-claim tasks
task_execution:
  claim_required: false
  autonomous_task_creation: true
```

### Per-Project Rules

Override for specific project in `<project>/.ai/policy.yaml`:

```yaml
# This project allows direct main writes (with caution)
task_execution:
  direct_main_write: true  # Overrides global
```

### Rule Enforcement in Code

```go
func (pe *PolicyEngine) GetMergedPolicy(aiID string, projectPath string) Policy {
    // 1. Load global
    global := pe.LoadGlobalPolicy()
    
    // 2. Load per-AI (if exists)
    aiPolicy := pe.LoadAIPolicy(aiID)
    
    // 3. Load per-project (if exists)
    projectPolicy := pe.LoadProjectPolicy(projectPath)
    
    // 4. Merge: AI > Project > Global
    merged := Policy{
        Global: global.Global,
    }
    merged = mergePolicy(merged, projectPolicy)  // Project overrides global
    merged = mergePolicy(merged, aiPolicy)       // AI overrides project
    
    return merged
}
```

## Continuous Operation

### Daemon Mode

```bash
# Start autonomous daemon
neona daemon start

# Daemon:
# 1. Loads all registered AIs
# 2. Monitors task queue continuously
# 3. Routes tasks to appropriate AIs
# 4. Executes tasks with policy enforcement
# 5. Handles failures and retries
# 6. Sends notifications
```

### Heartbeat & Lease Renewal

```go
// Each claimed task must send heartbeat
func (connector *CLIConnector) sendHeartbeat(taskID string) {
    ticker := time.NewTicker(30 * time.Second)
    for {
        select {
        case <-ticker.C:
            taskManager.Heartbeat(taskID, connector.AIID)
        }
    }
}

// If heartbeat missed > TTL, task becomes available again
func (tm *TaskManager) checkExpiredClaims() {
    // Query tasks where expires_at < NOW()
    // Set status back to "queued"
    // Release locks
}
```

## Summary

**How AIs Connect**:
- Via CLI connectors (v1) - process spawning, stdout/stderr parsing
- Neona stores connection configs in state store
- AIs do not connect to each other directly

**How Rules/Policies Apply**:
- Hierarchical policy resolution (Global → Project → AI)
- Pre-execution validation (PDR system)
- During-execution monitoring
- Post-execution evidence validation
- All decisions traceable via PDR

**How Continuous Tasks Work**:
- Autonomous agent monitors task queue
- DAG-aware scheduling (dependency resolution)
- Task claiming with TTL/heartbeat
- Locking prevents conflicts (task-level + path-level)
- Parallel execution when possible
- Policy enforcement at every stage
