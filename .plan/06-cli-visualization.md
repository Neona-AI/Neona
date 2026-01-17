# CLI Visualization Strategy

## Problem Statement

Neona runs as a CLI tool, not a visual GUI. Users need ways to:
- View tasks and their relationships (DAG structure)
- Understand policy hierarchy (Global → Project → AI)
- Explore workflows and dependencies
- Review rule configurations
- Navigate complex task graphs

**Challenge**: Make complex hierarchical data accessible in terminal without visual tools.

## Solution Architecture

### Multi-Layered Approach

1. **Interactive TUI Mode** - Rich terminal interface for exploration
2. **Tree/ASCII Visualization** - Hierarchical text-based displays
3. **Export Formats** - Export to human-readable or tool-processable formats
4. **Interactive Commands** - Navigable command-line interfaces

---

## Solution 1: Interactive TUI Mode

**Pattern**: Inspired by Letta-Code and OpenCode TUI implementations.

### Implementation

```go
// TUI Mode for task/rule exploration
neona tui                    # Interactive TUI
neona tui tasks              # TUI focused on tasks
neona tui policies           # TUI focused on policies
neona tui workflows          # TUI focused on workflows
```

### TUI Features

#### Task Tree View

```
┌────────────────────────────────────────────────────────┐
│  Neona TUI - Tasks                                      │
├────────────────────────────────────────────────────────┤
│  [Q] Queue  [C] Claimed  [R] Running  [D] Done  [F] Failed │
│                                                         │
│  Queue (3)                                              │
│  ├─ task-001: Review PR #123 [code-review, urgent]     │
│  │   └─> Depends on: task-002, task-003                │
│  ├─ task-002: Run tests [testing, required]            │
│  └─ task-003: Update docs [documentation]              │
│      └─> Depends on: task-002                          │
│                                                         │
│  Claimed (1)                                            │
│  └─ task-004: Fix bug in auth [bug-fix]                │
│      └─> Claimed by: claude-001 (12m ago)              │
│                                                         │
│  [↑↓] Navigate  [Enter] Details  [C] Claim  [Q] Quit   │
└────────────────────────────────────────────────────────┘
```

#### Policy Tree View

```
┌────────────────────────────────────────────────────────┐
│  Neona TUI - Policies                                   │
├────────────────────────────────────────────────────────┤
│  Policy Hierarchy                                       │
│  ├─ Global (.ai/policy.yaml)                           │
│  │   ├─ task_execution:                                │
│  │   │   ├─ claim_required: true                       │
│  │   │   └─ direct_main_write: false                   │
│  │   └─ safety:                                        │
│  │       └─ secrets_access: false                      │
│  ├─ Project (./.ai/policy.yaml)                        │
│  │   └─ task_execution:                                │
│  │       └─ direct_main_write: true  [OVERRIDE]        │
│  └─ AI (claude-001) (.ai/policy/claude-001.yaml)       │
│      └─ task_execution:                                │
│          └─ autonomous_task_creation: true [OVERRIDE]  │
│                                                         │
│  [↑↓] Navigate  [Enter] Edit  [P] Show PDR  [Q] Quit   │
└────────────────────────────────────────────────────────┘
```

#### Workflow Graph View (ASCII)

```
┌────────────────────────────────────────────────────────┐
│  Workflow: code-review                                  │
├────────────────────────────────────────────────────────┤
│                                                         │
│       [task-1: Analyze]                                │
│            │                                            │
│            ├─> [task-2: Test]                          │
│            │                                            │
│            └─> [task-3: Lint]                          │
│                 │                                       │
│                 └─> [task-4: Review]                   │
│                      │                                  │
│                      └─> [task-5: Approve]             │
│                                                         │
│  Status: task-1 (running)                              │
│          task-2 (blocked)                              │
│          task-3 (blocked)                              │
│                                                         │
│  [←→] Pan  [Zoom +/-]  [E] Execute  [Q] Quit           │
└────────────────────────────────────────────────────────┘
```

### TUI Components (Go)

```go
// Inspired by Letta-Code's TUI
type TUI struct {
    renderer *Renderer
    buffers  *Buffers
    events   chan TUIEvent
}

func (tui *TUI) RenderTaskTree(tasks []Task) {
    // Tree rendering with expand/collapse
    // Navigation with arrow keys
    // Details on Enter
}

func (tui *TUI) RenderPolicyHierarchy(policies PolicyHierarchy) {
    // Hierarchical policy display
    // Show override markers
    // Expandable sections
}
```

---

## Solution 2: Tree/ASCII Visualization Commands

**Pattern**: Tree structures for hierarchical data (like `tree` command).

### Task Tree Command

```bash
# Show task DAG as tree
neona task tree [task-id]

# Output example:
Tasks:
├─ task-001: Review PR #123 [queued]
│  ├─ Depends on: task-002, task-003
│  └─ Claims: claude-001 (code-review label)
│
├─ task-002: Run tests [running]
│  ├─ Claimed by: opencode-001 (5m ago)
│  └─ Dependencies: [none]
│
└─ task-003: Update docs [blocked]
   ├─ Depends on: task-002
   └─ Status: Waiting for task-002
```

### Policy Tree Command

```bash
# Show policy hierarchy as tree
neona policy tree [--ai <id>] [--project <path>]

# Output example:
Policy Hierarchy:
.
├─ Global (.ai/policy.yaml)
│  ├─ task_execution
│  │  ├─ claim_required: true
│  │  └─ direct_main_write: false
│  └─ safety
│     └─ secrets_access: false
│
├─ Project (./.ai/policy.yaml) [OVERRIDE]
│  └─ task_execution
│     └─ direct_main_write: true  ⚠️
│
└─ AI: claude-001 (.ai/policy/claude-001.yaml) [OVERRIDE]
   └─ task_execution
      └─ autonomous_task_creation: true  ⚠️

Legend: ⚠️ = Override, → = Inherited
```

### Workflow DAG Command

```bash
# Show workflow as ASCII graph
neona workflow tree <workflow-name>

# Output example:
Workflow: code-review
│
├─ Step 1: Analyze
│  └─> AI: claude-001
│  └─> [status: completed]
│
├─ Step 2: Test
│  ├─> Depends on: Step 1
│  ├─> AI: opencode-001
│  └─> [status: running]
│
└─ Step 3: Review
   ├─> Depends on: Step 2
   ├─> AI: claude-001
   └─> [status: pending]
```

---

## Solution 3: Export Formats

**Pattern**: Export to formats that external tools can visualize.

### Markdown Export

```bash
# Export tasks to markdown (human-readable)
neona task export [task-id] --format markdown > tasks.md

# Output: tasks.md
# Tasks

## Queue

- **task-001**: Review PR #123
  - Status: `queued`
  - Dependencies: task-002, task-003
  - Labels: code-review, urgent
  - Assigned to: claude-001

## Running

- **task-002**: Run tests
  - Status: `running`
  - Claimed by: opencode-001 (5m ago)
  - Progress: 60%
```

### Graphviz DOT Export

```bash
# Export workflow to Graphviz DOT format
neona workflow export <name> --format dot > workflow.dot

# User can visualize with:
# dot -Tpng workflow.dot -o workflow.png
# Or use online tools like GraphvizOnline

# Output: workflow.dot
digraph workflow_code_review {
    "task-001" [label="Analyze\n[completed]"]
    "task-002" [label="Test\n[running]"]
    "task-003" [label="Review\n[pending]"]
    
    "task-001" -> "task-002"
    "task-001" -> "task-003"
    "task-002" -> "task-003"
}
```

### JSON Export (Machine-Readable)

```bash
# Export for external tools
neona task export --format json | jq .
neona policy export --format json | jq .

# JSON structure includes all metadata
# External tools can render visualizations
```

### Mermaid Diagram Export

```bash
# Export to Mermaid format (GitHub/GitLab renderable)
neona workflow export <name> --format mermaid > workflow.mmd

# Output can be embedded in markdown files
# Renders automatically on GitHub/GitLab

# Example: workflow.mmd
graph TD
    A[Analyze] --> B[Test]
    A --> C[Lint]
    B --> D[Review]
    C --> D
    D --> E[Approve]
```

---

## Solution 4: Interactive Commands

**Pattern**: Navigable command-line interfaces with pagination and filtering.

### Task List Command (Interactive)

```bash
# Interactive task listing
neona task list --interactive

# Output:
Tasks (Page 1/3) - [N]ext [P]rev [F]ilter [S]ort [Q]uit

ID        Description           Status    AI        Created
───────────────────────────────────────────────────────────
task-001  Review PR #123        queued    -         2h ago
task-002  Run tests             running   opencode  1h ago
task-003  Update docs           blocked   -         30m ago

[N]ext page  [P]rev page  [F]ilter  [S]ort  [Enter] Details  [Q]uit
```

### Policy Show Command (Interactive)

```bash
# Interactive policy exploration
neona policy show --interactive

# Output:
Policy Explorer - [↑↓] Navigate [Enter] Expand [Q]uit

Global Policy (.ai/policy.yaml)
├─ task_execution
│  ├─ claim_required: true
│  ├─ direct_main_write: false
│  └─ autonomous_task_creation: false
│
└─ safety
   ├─ secrets_access: false
   └─ speculative_changes: false

[↑↓] Navigate  [Enter] Expand/Collapse  [E] Edit  [Q] Quit
```

---

## Solution 5: File-Based Formats (Import/Export)

**Pattern**: Human-readable text formats that can be edited and imported.

### Task Definition Format

```yaml
# tasks.yaml - Human-readable task definition
tasks:
  - id: task-001
    description: Review PR #123
    type: single
    dependencies: [task-002, task-003]
    priority: high
    labels: [code-review, urgent]
    policy:
      ai: claude-001
      allow_direct_main_write: false
    
  - id: task-002
    description: Run tests
    type: single
    dependencies: []
    priority: required
    labels: [testing]
```

### Policy Definition Format (Existing)

```yaml
# .ai/policy.yaml - Already human-readable
# Users can edit directly or import

global:
  task_execution:
    claim_required: true
    
per_ai:
  "claude-001":
    task_execution:
      autonomous_task_creation: true
```

### Import/Export Commands

```bash
# Export current state to files
neona task export --file tasks.yaml
neona policy export --file policies.yaml
neona workflow export --file workflows.yaml

# Import from files
neona task import tasks.yaml
neona policy import policies.yaml
neona workflow import workflows.yaml
```

---

## Solution 6: Status Dashboard (Single Command)

**Pattern**: Quick overview command showing everything at once.

```bash
# Show status dashboard
neona status

# Output:
┌─────────────────────────────────────────────────────────┐
│  Neona Status Dashboard                                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Tasks:                                                   │
│    Queue: 3  │  Claimed: 1  │  Running: 2  │  Done: 12   │
│                                                          │
│  AIs:                                                      │
│    claude-001: online (code-review, urgent)              │
│    opencode-001: online (testing)                        │
│    letta-001: offline                                    │
│                                                          │
│  Policies:                                                │
│    Global: 1  │  Project: 1  │  AI: 2                     │
│                                                          │
│  Recent Activity:                                         │
│    • task-002 claimed by opencode-001 (5m ago)           │
│    • task-001 created (10m ago)                          │
│    • claude-001 policy updated (1h ago)                  │
│                                                          │
│  [R] Refresh  [T] Tasks  [P] Policies  [A] AIs  [Q] Quit │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1 (MVP)
1. ✅ Tree visualization commands (`neona task tree`, `neona policy tree`)
2. ✅ Markdown export (`neona task export --format markdown`)
3. ✅ Status dashboard (`neona status`)
4. ✅ File-based import/export (YAML format)

### Phase 2 (Enhanced)
1. Interactive TUI mode (`neona tui`)
2. Graphviz DOT export (for external visualization)
3. Mermaid diagram export (for GitHub/GitLab)
4. Interactive commands with pagination

### Phase 3 (Advanced)
1. Real-time TUI updates
2. Workflow visualization with pan/zoom
3. Policy diff visualization
4. Task timeline view

---

## Example Workflows

### Viewing Task DAG

```bash
# Quick tree view
neona task tree

# Detailed view
neona task show task-001 --tree

# Export for external tool
neona task tree --format dot | dot -Tpng -o tasks.png
```

### Understanding Policy Hierarchy

```bash
# See full policy tree
neona policy tree

# See policy for specific AI
neona policy tree --ai claude-001

# Export to markdown
neona policy export --format markdown > policies.md
```

### Exploring Workflows

```bash
# View workflow as tree
neona workflow tree code-review

# Export to Mermaid (GitHub-compatible)
neona workflow export code-review --format mermaid > review.mmd

# Edit in external tool, then import
vim review.mmd
neona workflow import review.mmd
```

---

## Technical Implementation

### Tree Rendering Library

For Go, use:
- `github.com/disiqueira/gotree` - Tree structure rendering
- `github.com/muesli/termenv` - Terminal styling
- Custom ASCII tree generator for DAG visualization

### TUI Framework

For Go TUI:
- `github.com/charmbracelet/bubbletea` - TUI framework (inspired by Letta-Code's React-based TUI)
- `github.com/gdamore/tcell/v2` - Terminal UI library
- `github.com/rivo/tview` - Terminal UI components

### Export Format Libraries

- `gopkg.in/yaml.v3` - YAML export/import
- `encoding/json` - JSON export
- Custom generators for DOT, Mermaid formats

---

## Benefits

1. **Terminal-Native**: Works entirely in CLI
2. **Human-Readable**: Markdown/YAML files can be edited manually
3. **Tool-Compatible**: Export to formats external tools understand
4. **Interactive**: TUI mode for exploration
5. **Scriptable**: All commands can be automated
6. **Portable**: Text files can be shared, versioned, reviewed

---

## Summary

**Solution**: Multi-layered approach combining:
- **Tree commands** for quick hierarchical views
- **TUI mode** for interactive exploration
- **Export formats** for external visualization tools
- **File-based formats** for manual editing and import

Users get:
- ✅ Visual representation in terminal (tree/ASCII)
- ✅ Interactive exploration (TUI)
- ✅ Export to external tools (DOT, Mermaid)
- ✅ Human-readable files (YAML, Markdown)
- ✅ No requirement for external tools (everything works in CLI)
