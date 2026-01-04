<p align="center">
  <img src="assets/logo.svg" width="560" alt="Nexus Ray Logo">
</p>

<h1 align="center">Nexus Ray Framework</h1>

<p align="center">
  <strong>Enterprise-grade AI agent workflow orchestration with real Intel® OpenVINO™ LLM integration</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/tests-passing-brightgreen" />
  <img src="https://img.shields.io/badge/python-3.9+-blue" />
  <img src="https://img.shields.io/badge/license-MIT-blue" />
</p>

---

## 🧠 Overview

**Nexus Ray** is a **production-ready framework** for building autonomous, multi-agent AI systems.  
It combines **DAG-based workflow orchestration**, **optimized local LLM inference using Intel® OpenVINO™**, and an **event-driven architecture** to deliver scalable, observable, and enterprise-safe AI pipelines.

Designed for:
- Agentic AI systems
- Research & industry automation
- Local-first, privacy-preserving inference
- Production deployments

---

## ✨ Key Capabilities

### 🔹 Core Orchestration
- **DAG Workflows** – Parallel execution, retries, and fault tolerance  
- **Multi-Agent Coordination** – Collaboration, consensus, and role-based agents  
- **Guardrails** – Safety validation, scoring, and approval gates  

### 🔹 Advanced Intelligence
- **OpenVINO LLM Inference** – Optimized Mistral-7B (INT8 / FP16)  
- **Vector Memory** – Semantic context retention and recall  
- **Reference Agents** – Research, science, and industry pipelines  

### 🔹 Enterprise-Ready
- **Kafka Messaging** – Event-driven, decoupled execution  
- **Observability** – Metrics, traces, and live execution feed  
- **Production APIs** – FastAPI backend with Docker support  

---

## 🏗️ Architecture

```mermaid
flowchart TD
    subgraph Interface ["Interface Layer"]
        SDK["Nexus SDK"]
        API["FastAPI Backend"]
    end

    subgraph Core ["Nexus Core (Orchestrator)"]
        direction TB
        Graph["DAG Engine"]
        Safety["Guardrails & Scoring"]
    end

    subgraph Runtime ["Execution Runtime"]
        direction LR
        OV["OpenVINO LLM"]
        Tools["Agent Tools"]
        Kafka["Kafka Messaging"]
    end

    subgraph Storage ["Intelligence Buffer"]
        Mem["Vector Memory"]
    end

    subgraph Monitoring ["Observability"]
        Live["Live Event Stream"]
        Metrics["Prometheus/Grafana"]
    end

    %% Flow Connections
    SDK ==> API
    API ==> Graph
    Graph --> Safety
    Safety -.-> Runtime
    Runtime ==> Mem
    Runtime -.-> Live
    Kafka ==> Monitoring

    %% Styling
    classDef interface fill:#E11D2E,stroke:#fff,stroke-width:2px,color:#fff
    classDef core fill:#1e293b,stroke:#E11D2E,stroke-width:2px,color:#fff
    classDef runtime fill:#334155,stroke:#0071C5,stroke-width:2px,color:#fff
    classDef storage fill:#0f172a,stroke:#888,stroke-width:1px,color:#fff
    classDef monitoring fill:#111,stroke:#10b981,stroke-width:2px,color:#fff

    class SDK,API interface
    class Graph,Safety core
    class OV,Tools,Kafka runtime
    class Mem storage
    class Live,Metrics monitoring
```

---

## ⚡ Quick Start

Run a multi-agent system in under 2 minutes.

### 1️⃣ Backend Server
```bash
pip install -r requirements.txt
uvicorn src.api.server:app --reload
```

### 2️⃣ Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```

🌐 Open [http://localhost:5173](http://localhost:5173) to access the **Live Graph Dashboard**:
- **Real-time workflow graph** visualization
- **Agent execution & token metrics** tracking
- **Human-in-the-Loop (HITL) approvals** for critical steps

---

## 📦 What’s Included

### 🧩 Framework Components
- **SDK & Graph Engine** – Build workflows with `WorkflowBuilder`
- **Agent Runtime** – LLM, tool, and agent executors
- **LLM Server** – High-performance local inference engine

### 📊 Monitoring & UX
- **Web Dashboard** – Real-time visualization
- **TUI Dashboard** – Terminal-based monitoring
- **Observability Layer** – Logs, metrics, and traces

---

## 🚀 Intel® OpenVINO™ Benchmarks

Nexus Ray includes first-class benchmarking for OpenVINO-optimized LLMs.

### ⚡ Pre-Optimization vs Post-Optimization

| Stage | Precision | Throughput | Latency | RAM Usage |
| :--- | :---: | :---: | :---: | :---: |
| Pre-Optimization | FP16 | ~1.2 tok/s | ~42s | 16.5 GB |
| **Post-Optimization** | **INT8** | **~2.28 tok/s** | **~22s** | **~8.9 GB** |
| **Improvement** | — | 🚀 **~2× Faster** | ⚡ **~50% Lower** | 💾 **~47% Less** |

> [!TIP]
> OpenVINO INT8 quantization enables high-quality inference on 16GB RAM systems while delivering nearly 2× performance gains.

### 🧪 Run Benchmarks
```bash
# 1️⃣ Verify & download models (Prerequisite)
python scripts/verify_downloads.py
python scripts/download_models.py

# 2️⃣ Run the benchmark suite
python scripts/benchmark_models.py

# 3️⃣ View results
cat benchmark_results.json
```

### 🛠️ Utility Scripts
Nexus Ray includes a suite of specialized tools for developers and researchers:
- **`check_hallucinations.py`** – Automated validation of LLM outputs against ground truth.
- **`stress_test_industrial.py`** – High-load simulation for industrial agent workflows.
- **`recover_from_cache.py`** – Manage and repair local model/result caches.
- **`verify_downloads.py`** – Integrity checks for OpenVINO model artifacts.

### 🔍 Troubleshooting
- Use **`scripts/debug_imports.py`** to resolve environment/dependency issues.
- Use **`scripts/debug_hf.py`** to diagnose Hugging Face model loading errors.

---

## 📚 Documentation
<h3 align="center"> 
  <a href="docs/quickstart_benchmarking.md">Benchmarking Guide</a> ⭐ **NEW** | 
  <a href="docs/benchmarking.md">Intel OpenVINO Optimization</a> ⭐ **NEW** |
  <a href="docs/dag_flows.md">DAG Workflows</a> ⭐ **NEW**
</h3>

---

## 🛡️ License
Released under the MIT License. Built for research, industry, and production AI systems.

---

## 👥 The Team

Meet the minds behind Nexus Ray:

| Avatar | Name | Role | GitHub |
| :---: | :--- | :--- | :--- |
| <img src="https://github.com/rishikoli.png" width="40" height="40" style="border-radius:50%"> |  **Rishikesh Koli** | Project Lead & Architect | [@rishikoli](https://github.com/rishikoli) |
| <img src="https://github.com/Yashraj045.png" width="40" height="40" style="border-radius:50%"> | **Yashraj Kulkarni** | Core Framework Developer | [@Yashraj045](https://github.com/Yashraj045) |
| <img src="https://github.com/svpcet0303.png" width="40" height="40" style="border-radius:50%"> | **Anagha Bhure** | QA & Optimization | [@svpcet0303](https://github.com/svpcet0303) |

---
<p align="center"> <strong>Nexus Ray — Architecting the future of autonomous agentic AI</strong> </p>
