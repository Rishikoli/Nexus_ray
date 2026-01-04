# Agent Flow Visualization Designs

## Overview
Visual representation of agent execution flow for both TUI (Textual) and Web (Next.js) dashboards.

---

## TUI Dashboard - Agent Flow Panel

### Layout Design (ASCII Art Mockup)

```
┌─ Nexus Ray Command Center ──────────────────────────────────────────────────┐
│ Workflow: wf-abc123 | Type: Protein-Drug Discovery | Status: RUNNING         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  AGENT EXECUTION FLOW (7 agents)                               [Pause][Stop]│
│                                                                              │
│  ┌──────────────────┐                                                       │
│  │ Input Validator  │ ✓ Completed (230ms)                                   │
│  └────────┬─────────┘                                                       │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────────┐                                                   │
│  │ Structure Predictor  │ ⟳ Running (65% - 3420ms elapsed)                 │
│  └────────┬─────────────┘                                                   │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                       │
│  │ Quality Assessor │ ⏸ Waiting                                             │
│  └────────┬─────────┘                                                       │
│           │                                                                  │
│           ▼                                                                  │
│  ┌────────────────────────┐                                                 │
│  │ Binding Site Identifier│ ⏸ Waiting                                       │
│  └────────┬───────────────┘                                                 │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                       │
│  │ Molecular Docking│ ⏸ Waiting                                             │
│  └────────┬─────────┘                                                       │
│           │                                                                  │
│           ▼                                                                  │
│  ┌───────────────────────────┐                                              │
│  │ Binding & Safety Evaluator│ ⏸ Waiting                                    │
│  └────────┬──────────────────┘                                              │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────────┐                                                   │
│  │ Drugability Scorer   │ ⏸ Waiting                                         │
│  └──────────────────────┘                                                   │
│                                                                              │
│  Progress: ████████░░░░░░░░░░░░░░░ 35% (2/7 agents complete)               │
│  Elapsed: 00:03.65 | Estimated: 00:10.20 remaining                          │
│                                                                              │
├─ Live LLM Activity ──────────────────────────────────────────────────────────┤
│  [19:45:12] Structure Predictor: "Analyzing sequence homology..."           │
│  [19:45:11] Structure Predictor: "Predicting secondary structure..."        │
│                                                                              │
├─ Agent Details (Structure Predictor) ────────────────────────────────────────┤
│  Status: RUNNING                                                             │
│  Input: Protein sequence (150 residues)                                     │
│  Model: mistral-7b-ov                                                       │
│  Tokens: 156 in / 42 out (so far)                                           │
│  Confidence: 78% (building...)                                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
[Tab] Switch View  [R] Refresh  [P] Pause  [Q] Quit
```

### Implementation (Textual Widgets)

```python
# ui/tui/widgets/agent_flow.py
from textual.widgets import Static, Tree, ProgressBar
from textual.containers import Container, Vertical
from rich.text import Text

class AgentFlowPanel(Container):
    """Visual DAG flow of agent execution"""
    
    def compose(self):
        yield Static("AGENT EXECUTION FLOW", id="flow-header")
        yield AgentFlowTree(id="flow-tree")
        yield ProgressBar(total=100, id="workflow-progress")
        yield Static("", id="progress-text")
    
    async def update_flow(self, workflow_state: dict):
        """Update agent statuses in real-time"""
        tree = self.query_one(AgentFlowTree)
        
        for agent in workflow_state['tasks']:
            status_icon = {
                'completed': '✓',
                'running': '⟳',
                'waiting': '⏸',
                'failed': '✗'
            }[agent['status']]
            
            color = {
                'completed': 'green',
                'running': 'yellow',
                'waiting': 'dim',
                'failed': 'red'
            }[agent['status']]
            
            tree.update_node(
                agent['id'],
                f"{status_icon} {agent['name']} - {agent.get('duration', 'waiting')}"
            )

class AgentFlowTree(Tree):
    """Tree widget showing agent dependencies"""
    
    def __init__(self, **kwargs):
        super().__init__("Workflow", **kwargs)
        self.root.expand()
    
    def build_flow(self, dag: dict):
        """Build tree from DAG structure"""
        self.clear()
        
        # Add nodes in topological order
        for agent in dag['tasks']:
            parent = self.get_node_by_id(agent.get('parent', 'root'))
            parent.add(agent['name'], data=agent)
```

---

## Web Dashboard - Agent Flow Visualization

### React Component Design

```typescript
// frontend/src/components/AgentFlowVisualization.tsx
import { useEffect, useState } from 'react';
import ReactFlow, { 
  Node, 
  Edge, 
  Background, 
  Controls 
} from 'reactflow';
import 'reactflow/dist/style.css';

interface AgentNode {
  id: string;
  name: string;
  status: 'completed' | 'running' | 'waiting' | 'failed';
  duration?: number;
  output?: any;
}

export function AgentFlowVisualization({ workflowId }: { workflowId: string }) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  useEffect(() => {
    // Subscribe to workflow updates via SSE
    const eventSource = new EventSource(`/api/events?workflow_id=${workflowId}`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      updateFlowVisualization(data);
    };

    return () => eventSource.close();
  }, [workflowId]);

  const updateFlowVisualization = (workflowState: any) => {
    // Convert DAG to ReactFlow nodes
    const flowNodes: Node[] = workflowState.tasks.map((task: AgentNode, idx: number) => ({
      id: task.id,
      type: 'agentNode',
      position: { x: 250, y: idx * 100 },
      data: {
        label: task.name,
        status: task.status,
        duration: task.duration,
      },
      style: {
        background: getStatusColor(task.status),
        border: '2px solid #222',
        borderRadius: '8px',
        padding: '10px',
      },
    }));

    // Create edges from dependencies
    const flowEdges: Edge[] = workflowState.dependencies.map((dep: any) => ({
      id: `${dep.from}-${dep.to}`,
      source: dep.from,
      target: dep.to,
      animated: dep.to_status === 'running',
      style: { stroke: '#888' },
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#10b981'; // Green
      case 'running': return '#f59e0b'; // Yellow
      case 'waiting': return '#6b7280'; // Gray
      case 'failed': return '#ef4444'; // Red
      default: return '#6b7280';
    }
  };

  return (
    <div style={{ width: '100%', height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}

// Custom node component
function AgentNodeComponent({ data }: { data: any }) {
  const statusIcon = {
    completed: '✓',
    running: '⟳',
    waiting: '⏸',
    failed: '✗',
  }[data.status];

  return (
    <div className="agent-node">
      <div className="agent-icon">{statusIcon}</div>
      <div className="agent-name">{data.label}</div>
      {data.duration && (
        <div className="agent-duration">{data.duration}ms</div>
      )}
    </div>
  );
}
```

### Live Animation Features

1. **Real-time Updates**: SSE stream updates node statuses
2. **Animated Edges**: Flowing animation on active connections
3. **Progress Indicators**: Circular progress for running agents
4. **Click to Expand**: Click agent node to see details
5. **Pan & Zoom**: Explore large DAGs

---

## Semiconductor Workflow (Parallel Paths Example)

```
TUI Visualization:

  ┌─ Wafer Image Path ────────┐     ┌─ Sensor Data Path ─────┐
  │                            │     │                         │
  │  Defect Analysis      ✓    │     │  Process Intelligence ✓ │
  │  (2.3s)                    │     │  (1.8s)                 │
  │         │                  │     │         │               │
  │         ▼                  │     │         │               │
  │  Defect Classifier    ⟳    │     │         │               │
  │  (running)                 │     │         │               │
  └────────┬───────────────────┘     └─────────┬───────────────┘
           │                                    │
           └──────────┬─────────────────────────┘
                      ▼
           ┌──────────────────┐
           │ Yield Aggregator │ ⏸
           │   (waiting)      │
           └──────────────────┘
```

Web Visualization: Side-by-side parallel branches converging to aggregator

---

## Agent Detail Modal (Click any agent)

```
┌─ Agent Details: Structure Predictor ─────────────────────────────┐
│                                                                   │
│  Status: RUNNING                                                  │
│  Started: 19:45:10.234                                            │
│  Duration: 3.42s (estimated 5s total)                             │
│                                                                   │
│  Input:                                                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Protein Sequence:                                           │ │
│  │ MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVAT... │ │
│  │ Length: 150 residues                                        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  LLM Reasoning:                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Step 1: Analyzing sequence homology with known structures  │ │
│  │ Step 2: Predicting secondary structure (α-helices, β-sheets)│ │
│  │ Step 3: Generating 3D coordinates...                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Metrics:                                                         │
│  • Model: mistral-7b-ov                                           │
│  • Tokens: 156 in / 42 out (so far)                               │
│  • Latency: 287ms (LLM call)                                      │
│  • Current Confidence: 78%                                        │
│                                                                   │
│  [View Full Output]  [Cancel Agent]  [Close]                     │
└───────────────────────────────────────────────────────────────────┘
```

---

## API Endpoint for Flow Data

```python
# src/api/rest_server.py

@app.get("/api/workflows/{workflow_id}/flow")
async def get_workflow_flow(workflow_id: str):
    """Get current workflow execution flow for visualization"""
    workflow = await orchestrator.get_workflow(workflow_id)
    
    return {
        "workflow_id": workflow_id,
        "tasks": [
            {
                "id": task.id,
                "name": task.name,
                "status": task.status,
                "started_at": task.started_at,
                "duration_ms": task.duration_ms,
                "dependencies": task.depends_on,
                "output_preview": task.output[:100] if task.output else None
            }
            for task in workflow.tasks
        ],
        "edges": [
            {"from": dep.from_task, "to": dep.to_task}
            for dep in workflow.dependencies
        ],
        "progress": {
            "completed": len([t for t in workflow.tasks if t.status == "completed"]),
            "total": len(workflow.tasks),
            "percentage": workflow.progress_percentage
        }
    }
```

---

## Summary

**TUI**: ASCII tree view with real-time status updates  
**Web**: ReactFlow interactive DAG with animations  
**Both**: Live SSE updates, agent detail modals, progress tracking  

Ready to implement Phase 1!
