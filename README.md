# Peer: Tick-based Agent Runtime

`peer` is a small Python package for experimenting with a bounded, auditable agent day cycle.

The initial scope is intentionally narrow:

- support Jayda ↔ Jimmy collaboration on the MemoryBackend project;
- model every agent run as a fixed protocol tick;
- provide request/contract primitives for future multi-agent collaboration;
- keep Jayda ↔ Jaquan's existing trading_system collaboration contract protected and unchanged.

## Core idea

Each agent gets a fixed number of runs per day. The default day has **15 ticks**. Every tick executes the same conceptual loop:

```text
Sense → Triage → Align → Commit → Act → Verify → Communicate → Remember
```

The current MVP implements the durable state-transition skeleton:

- 15-tick schedule
- event triage
- request lifecycle updates
- active commitments
- protected contract guardrails
- tick summaries for traceability

## Quick start

```bash
python3 -m pytest -q
```

Minimal example:

```python
from peer import (
    AgentProfile,
    AgentState,
    ContractRegistry,
    Request,
    RequestBoard,
    TickContext,
    TickType,
    run_tick,
)

profile = AgentProfile(
    agent_id="jayda",
    role="MemoryBackend collaborator",
    goals=("Design MemoryBackend operating loop",),
)

request = Request(
    request_id="req-1",
    from_agent="jimmy",
    to_agent="jayda",
    title="Implement 15-tick loop",
    context="Use first for Jayda and MemoryBackend collaboration.",
    success_criteria=("schedule exists", "request lifecycle exists"),
    priority=90,
    related_project="MemoryBackend",
)

output = run_tick(
    TickContext(
        profile=profile,
        state=AgentState(agent_id="jayda"),
        tick_type=TickType.COLLABORATION,
        events=(),
        request_board=RequestBoard(requests=(request,)),
        contracts=ContractRegistry(),
    )
)

print(output.summary)
```

## Default 15-tick day

The current day rhythm is:

1. orientation
2. sensing
3. execution
4. collaboration
5. sensing
6. execution
7. execution
8. collaboration
9. sensing
10. execution
11. collaboration
12. execution
13. delivery
14. maintenance
15. reflection

## Design notes

See [`docs/agent-day-cycle.md`](docs/agent-day-cycle.md) for the operating protocol and collaboration architecture.
