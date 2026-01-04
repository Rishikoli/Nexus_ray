# Nexus Ray Framework Design Document

**Version**: 1.0  
**Status**: Final  
**Date**: January 2026

---

## 1. Executive Summary

**Nexus Ray** is an enterprise-grade AI Agent Framework designed to orchestrate complex, multi-step agentic workflows. Unlike simple agent scripts, Nexus Ray uses a robust **DAG (Directed Acyclic Graph)** execution engine, decoupled **event-driven architecture** (via Apache Kafka), and optimized **local inference** (via Intel® OpenVINO™).

This document outlines the architectural decisions, component design, and integration strategies that enable Nexus Ray to meet the requirements of scalable, audit-ready AI systems.

---

## 2. High-Level Architecture

The system follows a layered architecture pattern, separating ingress, orchestration, execution, and storage.

<p align="center">
  <img src="../assets/architecture.svg" width="100%" alt="Nexus Ray Architecture">
</p>

### 2.1 Core Layers

1.  **Interface Layer ("Ingress")**: Managed by a **FastAPI** backend, this layer handles flow definitions, triggers executions, and provides real-time status updates via Server-Sent Events (SSE).
2.  **Core Orchestrator**: The "Brain" of the system. It parses DAG definitions, manages state transitions, enforces guardrails, and schedules tasks.
3.  **Execution Runtime**: Decoupled workers that process tasks.
    *   **OpenVINO LLM**: Dedicated workers running Intel® optimized models.
    *   **Tools**: Isolated environments for code execution and API calls.
4.  **Intelligence Buffer ("Memory")**: A vector-based semantic memory system allowing agents to retain context across steps.
5.  **Observability**: A dedicated monitoring stack (Prometheus/Grafana) fed by Kafka events to audit every decision made by an agent.

---

## 3. Component Design & Technology Choices

### 3.1 Orchestration: Why DAGs?
We chose a **DAG-based approach** (over simple state machines) to allow for:
*   **Parallel Execution**: Agents that don't depend on each other can run simultaneously.
*   **Determinism**: The flow of data is explicit and traceable.
*   **Fault Tolerance**: If a node fails, the graph state is preserved, allowing for intelligent retries.

### 3.2 Messaging: Why Apache Kafka?
To meet the "enterprise" requirement, we rejected in-memory queues (like Python's `asyncio.Queue`) in favor of **Apache Kafka**.
*   **Decoupling**: The Orchestrator doesn't know *who* executes a task, only that it has been published.
*   **Durability**: Events are persisted, enabling "Time Travel" auditing of agent behavior.
*   **Scalability**: We can spin up 100 LLM workers to consume from the Kafka topic without changing the core code.

### 3.3 Inference: Why Intel® OpenVINO™?
Local inference is critical for privacy and cost control. We leverage **Intel® OpenVINO™** to optimize standard Hugging Face models (like Mistral-7B).
*   **INT8 Quantization**: Reduces memory footprint by ~47% (8.9GB vs 16.5GB).
*   **Throughput**: Increases token generation speed by ~200% on CPU hardware.
*   **NPU Support**: Ready for deployment on Intel® Core™ Ultra processors with dedicated NPUs.

---

## 4. Data Flow Lifecycle

A typical request flows through the system as follows:

1.  **Submission**: User submits a `WorkflowDefinition` JSON to the REST API.
2.  **Validation**: Orchestrator validates the DAG structure (checking for cycles).
3.  **Scheduling**:
    *   The Graph Engine identifies "Ready" nodes (zero unsatisfied dependencies).
    *   Task events are published to the `agent-tasks` Kafka topic.
4.  **Execution**:
    *   An available **Agent Worker** consumes the event.
    *   It retrieves context from **Vector Memory**.
    *   It invokes the **OpenVINO LLM** for reasoning.
    *   Result is published to `agent-results`.
5.  **State Update**: Orchestrator marks the node as `COMPLETED` and unlocks downstream nodes.
6.  **Completion**: When all nodes are done, the final result is stored and the user is notified.

---

## 5. Security & Guardrails

Nexus Ray implements a "Trust but Verify" approach:
*   **Input Guardrails**: All LLM inputs are scanned for injection attacks relative to the domain (e.g., PII masking).
*   **Output Validation**: Structured outputs (JSON) are validated against Pydantic schemas. If validation fails, a "Reflection Loop" is triggered to self-correct.
*   **Human-in-the-Loop (HITL)**: Critical nodes can be flagged as `requires_approval`, pausing the DAG until an operator signs off via the UI.

---

## 6. Performance & Optimization

Benchmarks managed via `scripts/benchmark_models.py` on Intel® DevCloud.

| Metric | Baseline (FP16) | Optimized (INT8) | Gain |
| :--- | :---: | :---: | :---: |
| **Throughput** | 1.2 tok/s | 2.28 tok/s | **+90%** |
| **Memory** | 16.5 GB | 8.9 GB | **-46%** |
| **Startup** | 14.5s | 8.2s | **-43%** |

---

## 7. Future Roadmap

*   **Federated Learning**: Allowing agents to update weights based on user corrections.
*   **Swarm Protocol**: Implementing gossip-based communication for leaderless agent swarms.
