# Reference Agents & Workflows

**Nexus Ray** ships with two fully implemented reference agents that demonstrate the framework's capability to handle complex, domain-specific logic in **Life Sciences** and **Precision Manufacturing**.

These agents are not mock-ups; they are functional **7-agent workflows** that utilize the SDK, OpenVINO LLM inference, and the core orchestration engine.

---

## 1. Semiconductor Analysis Flow
This is the workflow for the Semiconductor defect analysis reference agent.

### Overview
```mermaid
%%{init: {'theme':'base', 'themeVariables': {'primaryColor':'#DC143C','primaryTextColor':'#fff','primaryBorderColor':'#8B0000','lineColor':'#36454F','secondaryColor':'#36454F','tertiaryColor':'#2F4F4F','background':'#1a1a1a','mainBkg':'#DC143C','secondBkg':'#36454F','lineColor':'#808080','border1':'#DC143C','border2':'#36454F','note':'#36454F','noteBkg':'#2F4F4F','noteText':'#fff','text':'#fff','labelText':'#fff','loopTextColor':'#fff','activationBorderColor':'#DC143C','activationBkgColor':'#36454F','sequenceNumberColor':'#1a1a1a'}}}%%
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
    
    OPTIMIZE --> GATE{HITL: Engineer Approval}
    GATE -->|Approved| REPORT[Generate Report]
    GATE -->|Rejected| REVISE[Revise Parameters]
    
    REPORT --> END[Return Results]
```

### Detailed Task DAG
```mermaid
%%{init: {'theme':'base', 'themeVariables': {'primaryColor':'#DC143C','primaryTextColor':'#fff','primaryBorderColor':'#8B0000','lineColor':'#36454F','secondaryColor':'#36454F','tertiaryColor':'#2F4F4F','background':'#1a1a1a','mainBkg':'#DC143C','secondBkg':'#36454F','lineColor':'#808080','border1':'#DC143C','border2':'#36454F','note':'#36454F','noteBkg':'#2F4F4F','noteText':'#fff','text':'#fff','labelText':'#fff','loopTextColor':'#fff','activationBorderColor':'#DC143C','activationBkgColor':'#36454F','sequenceNumberColor':'#1a1a1a'}}}%%
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
        T13[Task 13: HITL & Format Report]
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

*   **Batch 0 (Parallel)**: Task 1: Validate Wafer ID, Task 2: Check Defect Data
*   **Batch 1 (Sequential)**: Task 3: Normalize Data
*   **Batch 2 (Sequential)**: Task 4: Calculate Baselines
*   **Batch 3 (Parallel)**: Task 5: Defect Detection, Task 6: Historical Comparison, Task 7: Pattern Analysis, Task 8: Spatial Clustering
*   **Batch 4 (Sequential)**: Task 9: Aggregate Findings
*   **Batch 5 (Sequential)**: Task 10: Confidence Scoring
*   **Batch 6 (Sequential)**: Task 11: Root Cause Analysis
*   **Batch 7 (Sequential)**: Task 12: Generate Recommendations
*   **Batch 8 (HITL Node)**: Task 13: Engineer Approval & Format Report

---

## 2. Protein-Drug Discovery Flow
Workflow for the Protein-Drug interaction analysis reference agent.

### Overview
```mermaid
%%{init: {'theme':'base', 'themeVariables': {'primaryColor':'#DC143C','primaryTextColor':'#fff','primaryBorderColor':'#8B0000','lineColor':'#36454F','secondaryColor':'#36454F','tertiaryColor':'#2F4F4F','background':'#1a1a1a','mainBkg':'#DC143C','secondBkg':'#36454F','lineColor':'#808080','border1':'#DC143C','border2':'#36454F','note':'#36454F','noteBkg':'#2F4F4F','noteText':'#fff','text':'#fff','labelText':'#fff','loopTextColor':'#fff','activationBorderColor':'#DC143C','activationBkgColor':'#36454F','sequenceNumberColor':'#1a1a1a'}}}%%
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
    
    VALIDATION --> GATE{HITL: Expert Review}
    GATE -->|Approved| REPORT[Generate Report]
    GATE -->|Rejected| STOP[Stop Workflow]
    
    REPORT --> END[Return Results]
```

### Agent Collaboration
```mermaid
%%{init: {'theme':'base', 'themeVariables': {'primaryColor':'#DC143C','primaryTextColor':'#fff','primaryBorderColor':'#8B0000','lineColor':'#36454F','secondaryColor':'#36454F','tertiaryColor':'#2F4F4F','background':'#1a1a1a','mainBkg':'#DC143C','secondBkg':'#36454F','actorBorder':'#DC143C','actorBkg':'#36454F','actorTextColor':'#fff','actorLineColor':'#808080','signalColor':'#DC143C','signalTextColor':'#fff','labelBoxBkgColor':'#36454F','labelBoxBorderColor':'#DC143C','labelTextColor':'#fff','loopTextColor':'#fff','noteBorderColor':'#DC143C','noteBkgColor':'#2F4F4F','noteTextColor':'#fff','activationBorderColor':'#DC143C','activationBkgColor':'#36454F','sequenceNumberColor':'#1a1a1a'}}}%%
sequenceDiagram
    participant Orchestrator
    participant BindingAgent
    participant AffinityAgent
    participant ToxicityAgent
    participant ConsensusAgent
    participant HITL as Human Expert
    
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
    
    Orchestrator->>HITL: Request Approval (Gate)
    HITL-->>Orchestrator: Approved
```

---

## 3. Running the Reference Agents

You can trigger these agents directly from the CLI or the Web Dashboard.

```bash
# Run Protein Discovery
python -m src.cli.run_workflow --name protein_drug_discovery

# Run Semiconductor Optimization
python -m src.cli.run_workflow --name semiconductor_yield
```
