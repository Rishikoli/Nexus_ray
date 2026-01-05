# Nexus Ray: DAG Workflow Flows

This document provides visual representations of the DAG (Directed Acyclic Graph) workflows in the Nexus Ray framework.

## Table of Contents

1. [Core DAG Architecture](#core-dag-architecture)
2. [Semiconductor Analysis Flow](#semiconductor-analysis-flow)
3. [Protein-Drug Discovery Flow](#protein-drug-discovery-flow)
4. [Generic Multi-Agent Flow](#generic-multi-agent-flow)
5. [Error Handling & Retries](#error-handling--retries)

---

## Core DAG Architecture

### High-Level System Flow

```mermaid
graph TD
    A[Client Request] --> B[API Server]
    B --> C[Orchestrator]
    C --> D[WorkflowDAG]
    D --> E[Task Scheduler]
    E --> F[Executor Pool]
    F --> G[LLM Executor]
    F --> H[Tool Executor]
    F --> I[Agent Executor]
    G --> J[OpenVINO LLM: Mistral-7B]
    H --> K[External Tools]
    I --> L[Custom Agents]
    J --> M[Response]
    K --> M
    L --> M
    M --> N[State Manager]
    N --> O[Memory Store]
    N --> P[Kafka Events]
    P --> Q[Observability]
    M --> R[Client Response]
```

### DAG Execution Model

```mermaid
graph LR
    A[Task Definition] --> B[Dependency Check]
    B --> C{All Deps Met?}
    C -->|No| D[Wait]
    D --> B
    C -->|Yes| E[Execute Task]
    E --> F{Success?}
    F -->|Yes| G[Update State]
    F -->|No| H{Retry?}
    H -->|Yes| I[Backoff]
    I --> E
    H -->|No| J[Mark Failed]
    G --> K[Notify Dependents]
    J --> K
    K --> L[Next Task]
```

---

## Semiconductor Analysis Flow

This is the workflow for the Semiconductor defect analysis reference agent.

### Overview

```mermaid
graph TD
    START[Wafer Data Input] --> VALIDATE[Validate Input]
    VALIDATE --> PREPROCESS[Preprocess Data]
    PREPROCESS --> PARALLEL{Parallel Analysis}
    
    PARALLEL -->|Branch 1| DEFECT[Defect Detection Agent]
    PARALLEL -->|Branch 2| HISTORIC[Historical Analysis Agent]
    PARALLEL -->|Branch 3| PATTERN[Pattern Recognition Agent]
    
    DEFECT --> CONSENSUS[Consensus Agent]
    HISTORIC --> CONSENSUS
    PATTERN --> CONSENSUS
    
    CONSENSUS --> ROOT[Root Cause Analysis Agent]
    ROOT --> OPTIMIZE[Optimization Recommendations Agent]
    OPTIMIZE --> REPORT[Generate Report]
    REPORT --> END[Return Results]
```

### Detailed Task DAG

```mermaid
graph TD
    subgraph "Input Stage"
        T1[Task 1: Validate Wafer ID]
        T2[Task 2: Check Defect Data]
    end
    
    subgraph "Preprocessing Stage"
        T3[Task 3: Normalize Data]
        T4[Task 4: Calculate Baselines]
    end
    
    subgraph "Parallel Analysis Stage"
        T5[Task 5: Defect Detection]
        T6[Task 6: Historical Comparison]
        T7[Task 7: Pattern Analysis]
        T8[Task 8: Spatial Clustering]
    end
    
    subgraph "Consensus Stage"
        T9[Task 9: Aggregate Findings]
        T10[Task 10: Confidence Scoring]
    end
    
    subgraph "Output Stage"
        T11[Task 11: Root Cause Analysis]
        T12[Task 12: Generate Recommendations]
        T13[Task 13: Format Report]
    end
    
    T1 --> T3
    T2 --> T3
    T3 --> T4
    T4 --> T5
    T4 --> T6
    T4 --> T7
    T4 --> T8
    T5 --> T9
    T6 --> T9
    T7 --> T9
    T8 --> T9
    T9 --> T10
    T10 --> T11
    T11 --> T12
    T12 --> T13
```

### Execution Order

The DAG scheduler determines the following execution batches:

**Batch 0 (Parallel):**
- Task 1: Validate Wafer ID
- Task 2: Check Defect Data

**Batch 1 (Sequential):**
- Task 3: Normalize Data

**Batch 2 (Sequential):**
- Task 4: Calculate Baselines

**Batch 3 (Parallel):**
- Task 5: Defect Detection
- Task 6: Historical Comparison
- Task 7: Pattern Analysis
- Task 8: Spatial Clustering

**Batch 4 (Sequential):**
- Task 9: Aggregate Findings

**Batch 5 (Sequential):**
- Task 10: Confidence Scoring

**Batch 6 (Sequential):**
- Task 11: Root Cause Analysis

**Batch 7 (Sequential):**
- Task 12: Generate Recommendations

**Batch 8 (Sequential):**
- Task 13: Format Report

---

## Protein-Drug Discovery Flow

Workflow for the Protein-Drug interaction analysis reference agent.

### Overview

```mermaid
graph TD
    START[Protein + Drug Input] --> VALIDATE[Validate Structures]
    VALIDATE --> PARALLEL{Parallel Analysis}
    
    PARALLEL -->|Branch 1| BINDING[Binding Site Prediction]
    PARALLEL -->|Branch 2| AFFINITY[Affinity Scoring]
    PARALLEL -->|Branch 3| TOXICITY[Toxicity Assessment]
    PARALLEL -->|Branch 4| SIMILAR[Similarity Search]
    
    BINDING --> CONSENSUS[Multi-Agent Consensus]
    AFFINITY --> CONSENSUS
    TOXICITY --> CONSENSUS
    SIMILAR --> CONSENSUS
    
    CONSENSUS --> RANKING[Candidate Ranking]
    RANKING --> VALIDATION[Cross-Validation]
    VALIDATION --> REPORT[Generate Report]
    REPORT --> END[Return Results]
```

### Agent Collaboration

```mermaid
sequenceDiagram
    participant Orchestrator
    participant BindingAgent
    participant AffinityAgent
    participant ToxicityAgent
    participant ConsensusAgent
    
    Orchestrator->>BindingAgent: Analyze binding sites
    Orchestrator->>AffinityAgent: Calculate affinity
    Orchestrator->>ToxicityAgent: Assess toxicity
    
    par Parallel Execution
        BindingAgent-->>Orchestrator: Binding results
        AffinityAgent-->>Orchestrator: Affinity score
        ToxicityAgent-->>Orchestrator: Safety profile
    end
    
    Orchestrator->>ConsensusAgent: Combine results
    ConsensusAgent->>ConsensusAgent: Vote + Weight
    ConsensusAgent-->>Orchestrator: Final recommendation
```

---

## Generic Multi-Agent Flow

Template for any multi-agent workflow in Nexus Ray.

### Pattern: Fork-Join with Consensus

```mermaid
graph TD
    INPUT[Input Task] --> FORK{Fork}
    
    FORK -->|Agent 1| A1[Research Agent]
    FORK -->|Agent 2| A2[Analysis Agent]
    FORK -->|Agent 3| A3[Validation Agent]
    
    A1 --> BARRIER[Synchronization Barrier]
    A2 --> BARRIER
    A3 --> BARRIER
    
    BARRIER --> CONSENSUS[Consensus Agent]
    CONSENSUS --> DECISION{Consensus Reached?}
    
    DECISION -->|Yes| OUTPUT[Final Output]
    DECISION -->|No| REFLECTION[Reflection Loop]
    REFLECTION --> A1
    
    OUTPUT --> END[Complete]
```

### Pattern: Sequential Pipeline

```mermaid
graph LR
    T1[Data Collection] --> T2[Preprocessing]
    T2 --> T3[Feature Extraction]
    T3 --> T4[Model Inference]
    T4 --> T5[Post-processing]
    T5 --> T6[Validation]
    T6 --> T7[Output Formatting]
```

### Pattern: Iterative Refinement

```mermaid
graph TD
    START[Initial Input] --> GEN[Generate Draft]
    GEN --> EVAL[Evaluate Quality]
    EVAL --> DECISION{Quality >= Threshold?}
    DECISION -->|No| CRITIQUE[Critique Agent]
    CRITIQUE --> REFINE[Refinement Agent]
    REFINE --> GEN
    DECISION -->|Yes| OUTPUT[Final Output]
    DECISION -->|Max Iterations| FALLBACK[Fallback Strategy]
    FALLBACK --> OUTPUT
```

---

## Error Handling & Retries

### Retry Logic Flow

```mermaid
graph TD
    START[Execute Task] --> CHECK{Success?}
    CHECK -->|Yes| DONE[Mark Complete]
    CHECK -->|No| COUNT{Retry Count < Max?}
    COUNT -->|Yes| BACKOFF[Exponential Backoff]
    BACKOFF --> RETRY[Retry Task]
    RETRY --> START
    COUNT -->|No| ERROR[Mark Failed]
    ERROR --> COMPENSATE{Compensation Handler?}
    COMPENSATE -->|Yes| COMP[Run Compensation]
    COMPENSATE -->|No| PROPAGATE[Propagate Error]
    COMP --> PROPAGATE
```

### Circuit Breaker Pattern

```mermaid
stateDiagram-v2
    [*] --> Closed
    Closed --> Open: Error Threshold Exceeded
    Open --> HalfOpen: Timeout Elapsed
    HalfOpen --> Closed: Success
    HalfOpen --> Open: Failure
    Closed --> Closed: Success
    Open --> Open: Request Blocked
```

---

## Task Dependencies Visualization

### Example: Complex Workflow

```mermaid
graph TD
    T1[Start] --> T2[Task A]
    T1 --> T3[Task B]
    T2 --> T4[Task D]
    T3 --> T4
    T2 --> T5[Task E]
    T3 --> T6[Task F]
    T4 --> T7[Task G]
    T5 --> T7
    T6 --> T7
    T7 --> T8[End]
    
    style T1 fill:#90EE90
    style T8 fill:#FFB6C1
    style T4 fill:#FFD700
    style T7 fill:#FFD700
```

**Dependency Matrix:**

| Task | Depends On | Can Run With |
|------|-----------|--------------|
| A | Start | B |
| B | Start | A |
| D | A, B | - |
| E | A | F |
| F | B | E |
| G | D, E, F | - |
| End | G | - |

---

## Execution Monitoring

### State Transitions

```mermaid
stateDiagram-v2
    [*] --> Pending
    Pending --> Ready: Dependencies Met
    Ready --> Running: Executor Assigned
    Running --> Success: Execution Complete
    Running --> Failed: Error Occurred
    Failed --> Retrying: Retry Available
    Retrying --> Running: Backoff Complete
    Failed --> Compensating: No Retries Left
    Compensating --> Compensated: Handler Complete
    Success --> [*]
    Compensated --> [*]
```

### Metrics Collection Points

```mermaid
graph LR
    A[Task Start] -->|Measure| B[Queue Time]
    B -->|Measure| C[Execution Time]
    C -->|Measure| D[Task End]
    A -.->|Log| E[Start Event]
    D -.->|Log| F[End Event]
    C -.->|Track| G[Resource Usage]
    G --> H[Memory]
    G --> I[CPU]
    G --> J[GPU]
```

---

## Real-World Example: Semiconductor Workflow Code

### Building the DAG

```python
from src.core.dag import WorkflowDAG
from src.core.task import TaskDefinition

# Create DAG
workflow = WorkflowDAG(workflow_id="semiconductor-analysis-001")

# Define tasks
validate_task = TaskDefinition(
    task_id="validate",
    name="Validate Input",
    task_type="validation",
    depends_on=[]
)

preprocess_task = TaskDefinition(
    task_id="preprocess",
    name="Preprocess Data",
    task_type="preprocessing",
    depends_on=["validate"]
)

defect_task = TaskDefinition(
    task_id="defect",
    name="Defect Detection",
    task_type="agent",
    depends_on=["preprocess"]
)

historic_task = TaskDefinition(
    task_id="historic",
    name="Historical Analysis",
    task_type="agent",
    depends_on=["preprocess"]
)

consensus_task = TaskDefinition(
    task_id="consensus",
    name="Consensus",
    task_type="agent",
    depends_on=["defect", "historic"]
)

# Add to DAG
workflow.add_task(validate_task)
workflow.add_task(preprocess_task)
workflow.add_task(defect_task)
workflow.add_task(historic_task)
workflow.add_task(consensus_task)

# Add dependencies
workflow.add_dependency("validate", "preprocess")
workflow.add_dependency("preprocess", "defect")
workflow.add_dependency("preprocess", "historic")
workflow.add_dependency("defect", "consensus")
workflow.add_dependency("historic", "consensus")

# Validate
workflow.validate()

# Get execution order
batches = workflow.get_execution_order()
# Output: [['validate'], ['preprocess'], ['defect', 'historic'], ['consensus']]
```

### Executing the Workflow

```python
from src.core.orchestrator import Orchestrator

orchestrator = Orchestrator()

# Execute workflow
result = await orchestrator.execute_workflow(
    workflow=workflow,
    initial_context={"wafer_id": "WAF-9982-X"}
)

print(f"Status: {result.status}")
print(f"Output: {result.output}")
```

---

## Best Practices

### 1. Task Granularity

✅ **Good:** Fine-grained tasks
```python
- Validate input
- Load model
- Run inference
- Post-process
```

❌ **Bad:** Coarse-grained tasks
```python
- Do everything
```

### 2. Dependency Management

✅ **Good:** Explicit dependencies
```python
task.depends_on = ["task_a", "task_b"]
```

❌ **Bad:** Implicit ordering
```python
# Relying on execution order without declaring deps
```

### 3. Error Handling

✅ **Good:** Graceful degradation
```python
task.retry_config = RetryConfig(
    max_retries=3,
    backoff_base=2.0
)
task.fallback_handler = fallback_fn
```

❌ **Bad:** Fail entire workflow
```python
# No retry or fallback
```

---

## Performance Optimization

### Maximizing Parallelism

```mermaid
graph TD
    subgraph "Before Optimization"
        A1[Task 1] --> A2[Task 2]
        A2 --> A3[Task 3]
        A3 --> A4[Task 4]
    end
    
    subgraph "After Optimization"
        B1[Task 1] --> B2[Task 2]
        B1 --> B3[Task 3]
        B2 --> B4[Task 4]
        B3 --> B4
    end
```

### Resource Allocation

```python
# Assign resource requirements
task.resource_requirements = {
    "cpu": 2,
    "memory_gb": 4,
    "gpu": 0
}

# Executor pool will schedule accordingly
```

---

## Debugging DAG Workflows

### Visualization Tools

```bash
# Generate ASCII visualization
python -c "
from src.core.dag import WorkflowDAG
dag = WorkflowDAG.from_file('workflow.json')
print(dag.visualize_ascii())
"
```

### Execution Trace

```python
# Enable detailed logging
workflow.execution_config.log_level = "DEBUG"

# This will log:
# - Task start/end times
# - Dependency resolution
# - Parallel batch execution
# - State transitions
```

---

## References

- [Core DAG Implementation](../src/core/dag.py)
- [Orchestrator](../src/core/orchestrator.py)
- [Task Definitions](../src/core/task.py)
- [Semiconductor Reference Agent](../reference_agents/semiconductor/)
- [Protein-Drug Reference Agent](../reference_agents/protein_drug/)

## Next Steps

- **[Try Examples](../examples/)** - Run pre-built workflows
