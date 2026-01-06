
<h1 align="center">Nexus Ray Framework</h1>

<p align="center">
  <strong>Agentic AI agent workflow orchestration with real Intel® OpenVINO™ LLM integration</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/tests-passing-brightgreen?style=for-the-badge" />
  <img src="https://img.shields.io/badge/python-3.10+-DC143C?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/license-MIT-36454F?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Intel-OpenVINO-0071C5?style=for-the-badge&logo=intel&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Kafka-Enabled-231F20?style=for-the-badge&logo=apachekafka&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Status-Production_Ready-8B0000?style=for-the-badge" />
</p>

<br>

## Overview

**Nexus Ray** is a **production-ready framework** for building autonomous, multi-agent AI systems.  
It combines **DAG-based workflow orchestration**, **optimized local LLM inference using Intel® OpenVINO™**, and an **event-driven architecture** to deliver scalable and observable AI pipelines.

**Designed for:**
*   Agentic AI systems
*   Research & industry automation
*   Local-first, privacy-preserving inference
*   Production deployments

<br>

## Beyond the Core Specialized Innovations

<div align="center">

![Latest Breakthroughs](assets/whats_new.svg)

</div>

<br>

## Technical Stack

<p align="left">
  <img src="https://img.shields.io/badge/Language-Python_3.10-E11D48?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/AI_Engine-Intel_OpenVINO-F43F5E?style=for-the-badge&logo=intel&logoColor=white" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-9F1239?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Messaging-Apache_Kafka-475569?style=for-the-badge&logo=apachekafka&logoColor=white" />
  <img src="https://img.shields.io/badge/Vector_DB-ChromaDB-64748B?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Frontend-React_Input-94A3B8?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Profiler-Intel_VTune-475569?style=for-the-badge&logo=intel&logoColor=white" />
  <img src="https://img.shields.io/badge/Security-Intel_SGX-475569?style=for-the-badge&logo=intel&logoColor=white" />
  <img src="https://img.shields.io/badge/Platform-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
</p>

<br>

## Key Capabilities

### Core Orchestration
*   **DAG Workflows**: Parallel execution, retries, and fault tolerance.
*   **Multi-Agent Coordination**: Collaboration, consensus, and role-based agents.
*   **Guardrails**: Safety validation, scoring, and approval gates.

### Advanced Intelligence
*   **OpenVINO LLM Inference**: Optimized Mistral-7B (INT8 / FP16).
*   **Vector Memory**: Semantic context retention and recall.
*   **Reference Agents**: Research, science, and industry pipelines (7-agent workflows).

### Deployment Readiness
*   **Kafka Messaging**: Event-driven, decoupled execution.
*   **Observability**: Metrics, traces, and live execution feed.
*   **Production APIs**: FastAPI backend with Docker support.

<br>

## Architecture

![Core DAG Architecture](assets/architecture_diagram.svg)

<br>

## Workspace Demo

![Nexus Ray Demo](assets/screenshots/Demo.gif)

<br>

## Quick Start

Run a multi-agent system in under 2 minutes.

### 1. Backend Server
```bash
pip install -r requirements.txt
uvicorn src.api.server:app --reload
```

### 2. Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```

### 3. Containerized Deployment (Alternative)
For isolated production-like environments, use the provided Docker configuration:
```bash
# Build the backend image
docker build -t nexus-ray-backend .

# Run the container
docker run -p 8000:8000 nexus-ray-backend
```

**Access the Live Graph Dashboard at [http://localhost:5173](http://localhost:5173):**
*   **Real-time workflow graph** visualization
*   **Agent execution & token metrics** tracking
*   **Human-in-the-Loop (HITL) approvals** for critical steps

<br>

## System Components

### Framework
*   **SDK & Graph Engine**: Build workflows with `WorkflowBuilder`
*   **Agent Runtime**: LLM, tool, and agent executors
*   **LLM Server**: High-performance local inference engine

### Monitoring & UX
*   **Web Dashboard**: Real-time visualization
*   **Observability Layer**: Logs, metrics, and traces

<br>

## Intel® OpenVINO™ Benchmarks

Nexus Ray includes first-class benchmarking for OpenVINO-optimized LLMs.

### Performance Comparison

![OpenVINO Performance Benchmarks](./assets/performance_comparison.svg)

> [!TIP]
> OpenVINO INT8 quantization enables high-quality inference on 16GB RAM systems while delivering nearly 2× performance gains.

### Quick Run
```bash
# 1. Verify & download models (Prerequisite)
python scripts/verify_downloads.py
python scripts/download_models.py

# 2. Run the benchmark suite
python scripts/benchmark_models.py

# 3. View results
cat benchmark_results.json
```

### Utility Scripts
Nexus Ray includes a suite of specialized tools for developers and researchers:
*   **`check_hallucinations.py`**: Automated validation of LLM outputs against ground truth.
*   **`stress_test_industrial.py`**: High-load simulation for industrial agent workflows.
*   **`recover_from_cache.py`**: Manage and repair local model/result caches.
*   **`verify_downloads.py`**: Integrity checks for OpenVINO model artifacts.

### Troubleshooting
*   Use **`scripts/debug_imports.py`** to resolve environment/dependency issues.
*   Use **`scripts/debug_hf.py`** to diagnose Hugging Face model loading errors.

<br>

## Documentation

### Formal Deliverables
<div align="center">

<br>

> ### **[<u>System Design</u>](docs/DESIGN.md)**
> *Deep Dive into Framework Architecture, Multi-Agent Orchestration, and Core Design Decisions*

<br>

> ### **[<u>SDK API Reference</u>](docs/SDK_API.md)**
> *Comprehensive Guide to the `WorkflowBuilder` Fluent API and Programmatic Agent Coordination*

<br>

> ### **[<u>Reference Agents</u>](docs/REFERENCE_AGENTS.md)**
> *In-depth Documentation for 7-Agent Reference Pipelines in Life Sciences and Semiconductor Manufacturing*

<br>

> ### **[<u>Performance Report</u>](docs/PERFORMANCE_REPORT.md)**
> *Comparative Performance Analysis of Intel® OpenVINO™ Optimizations (INT8 vs. FP16 Baseline)*

<br>

</div>

<br>

<br>

## Intel® Technology Roadmap: The Path to Confidential AI

To ensure Nexus Ray remains at the forefront of secure, industrial-grade agent orchestration, our roadmap focuses on deep integration with the Intel® software and hardware ecosystem:

*   **Confidential Agent Coordination (Intel® SGX)**: Implementing **Intel® Software Guard Extensions** to create secure enclaves for agent execution. This ensures that sensitive medical data in Life Sciences and proprietary yield parameters in Semiconductor manufacturing remain encrypted even during active processing.
*   **Cross-Architecture Scaling (Intel® oneAPI)**: Leveraging the **Intel® oneAPI** abstraction layer to seamlessly scale Nexus Ray's multi-agent logic from Xeon® CPUs to Intel® Arc™ and Data Center GPUs without codebase modifications.
*   **Enterprise Swarm Orchestration (Intel® Tiber™ AI Cloud)**: Providing a native deployment path to **Intel® Tiber™ AI Cloud** for orchestrating massive-scale industrial agent swarms across global infrastructure.
*   **Sustainability & Green AI**: By optimizing for high-throughput execution on **Intel® CPUs + OpenVINO™**, Nexus Ray significantly reduces the carbon footprint and energy overhead compared to traditional GPU-reliant agent frameworks.

<br>

## License
Released under the MIT License. Built for research, industry, and production AI systems.

<br>

<h2 align="center">The Team</h2>

<div align="center">

Meet the minds behind Nexus Ray:

|       | Name | Role | GitHub |
| :---: | :--- | :--- | :--- |
| <img src="https://github.com/rishikoli.png" width="40" height="40" style="border-radius:50%"> |  **Rishikesh Koli** | Project Lead & Architect | [@rishikoli](https://github.com/rishikoli) |
| <img src="https://github.com/svpcet0303.png" width="40" height="40" style="border-radius:50%"> | **Anagha Bhure** | QA & Optimization | [@svpcet0303](https://github.com/svpcet0303) |
| <img src="https://github.com/Yashraj045.png" width="40" height="40" style="border-radius:50%"> | **Yashraj Kulkarni** | Core Framework Developer | [@Yashraj045](https://github.com/Yashraj045) |

</div>
