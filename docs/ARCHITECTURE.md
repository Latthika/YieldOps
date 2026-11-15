# YieldOps Architecture (Initial)

## Goal

Measure inference workloads and recommend changes that reduce cost while meeting explicit quality, latency, throughput, and reliability constraints. All proposed infrastructure changes require human approval.

## Initial component boundaries

```text
Workload generator
      |
      v
FastAPI service ----> Inference adapter (simulator first; vLLM later)
      |                              |
      +---- request metadata <-------+
                    |
           telemetry/storage
            |             |
      Prometheus       PostgreSQL
            |             |
         Grafana     cost and forecasting
                          |
                 deterministic optimizer
                          |
                 benchmark/evaluation
                          |
             LangGraph coordination layer
                          |
              policy + human approval
```

The API, simulator adapter, request schemas, and bounded in-memory telemetry summary are implemented. The initial milestone keeps inference timing in-process and simulated. PostgreSQL, Prometheus, Grafana, model serving, durable storage, and agent orchestration remain planned components.

## Measurement labels

Every metric or derived result must carry provenance: `simulated`, `measured`, or `estimated`. Cost estimates must record the pricing source, allocation rule, and measurement period. Never describe simulated GPU utilization, latency, or cost as real hardware measurements.

## Deployment boundary

Local macOS is for development and simulation. Real NVIDIA/CUDA benchmarking requires an authorized compatible Linux host with appropriate GPU, driver, CUDA/runtime, and model capacity. Cloud provisioning and externally reachable deployments are out of scope until explicitly approved.

## Security and data handling

Do not record raw prompts or model responses by default. Agents call bounded, explicitly defined application tools; they do not receive unrestricted shell, database, or infrastructure credentials. Record recommendations and approvals for audit.
