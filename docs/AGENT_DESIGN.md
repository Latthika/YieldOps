# Agent Design: Current State and Requirements

## Current state

- LangGraph is not a dependency in `pyproject.toml` or `uv.lock`.
- `src/yieldops/agents/` contains only `.gitkeep`.
- There are zero agents, agent state graphs, LLM clients, agent tools, traces, retry policies, or agent evaluations.
- The app contains no shell, database, cloud, or infrastructure tool interface.
- No human approval step is implemented. The README's approval statement describes an intended platform policy only.

## Information flow today

There is no agent information flow. The API invokes a deterministic Python simulator directly and aggregates the result. FastAPI/Pydantic validation errors return HTTP 422; workload client connection errors are counted by the CLI. This is ordinary application control flow, not agent orchestration.

## Intended future design (not implemented)

The project instructions propose five roles: workload profiler, infrastructure diagnostician, optimizer, benchmark/evaluation, and policy/approval. Any future LangGraph implementation should use typed state, explicit application tools, bounded retries, auditable decisions, and an approval gate before infrastructure changes. Arithmetic, cost attribution, and benchmark comparisons should remain deterministic code rather than LLM-generated calculations.

Do not describe the current API as agentic or claim human-in-the-loop safety until there is executable graph/tool code and tests demonstrating the approval behavior.
