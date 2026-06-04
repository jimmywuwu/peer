# Agent Day Cycle

This document describes the first implementation target for `peer`: a bounded, tick-based agent loop that can later support collaboration among multiple long-running agents.

## Scope for the first version

This repository starts with the collaboration context Jimmy specified:

- The loop is first used for collaboration with Jayda on the MemoryBackend project.
- Jayda and Jaquan's existing trading_system collaboration pattern is **not changed**.
- That existing Jayda ↔ Jaquan contract is represented as a protected contract guardrail so MemoryBackend ticks cannot silently modify it.

## Why ticks instead of always-on agents?

A fixed tick budget makes agent behavior:

- bounded: each agent has a known maximum number of runs per day;
- auditable: every tick emits a summary and state transition;
- cheaper to reason about: cost is roughly `agent_count × ticks_per_day × average_tick_cost`;
- calmer: agents collaborate asynchronously instead of recursively interrupting one another.

The default budget is **15 ticks/day**.

## Standard loop

Every tick follows the same conceptual loop:

```text
1. Sense
2. Triage
3. Align
4. Commit
5. Act
6. Verify
7. Communicate
8. Remember
```

The MVP currently implements the state skeleton for these stages. It does not yet execute external tools or write durable memory.

## Tick input

A tick receives a `TickContext`:

- `profile`: who the agent is, its role, goals, and collaboration policy;
- `state`: active commitments and previous tick summary;
- `tick_type`: one of orientation/sensing/execution/collaboration/delivery/maintenance/reflection;
- `events`: normalized environmental events;
- `request_board`: structured requests addressed to the agent;
- `contracts`: active/protected collaboration contracts;
- `budget`: per-tick action limits.

## Tick output

A tick returns a `TickOutput`:

- updated `state`;
- unchanged or updated `contracts`;
- `updated_requests` with lifecycle transitions;
- `deferred_events` that were sensed but not actionable enough;
- `memory_writes` reserved for future MemoryBackend integration;
- `contract_change_proposals` reserved for explicit contract negotiation;
- `risk_flags` for blocked or risky transitions;
- a compact `summary` for traceability.

## Collaboration model

The intended collaboration architecture has three layers.

### 1. Request board

Agents do not free-chat by default. They exchange structured requests:

```text
Request:
- id
- from_agent
- to_agent
- title
- context
- success_criteria
- priority
- related_project
- requested_contract_change
- status
```

The MVP supports request states including `created`, `accepted`, `deferred`, `blocked`, `delivered`, `verified`, and `closed`.

### 2. Contract registry

Stable collaboration expectations are modeled as contracts:

```text
Contract:
- contract_id
- participants
- purpose
- status
- version
```

The first protected contract is expected to be Jayda ↔ Jaquan's trading_system collaboration. MemoryBackend ticks may observe that contract, but should not mutate it unless Jimmy explicitly decides to change that workflow later.

### 3. Shared workspace

Future versions should add a shared workspace abstraction containing:

- event log;
- request board;
- contract registry;
- task state;
- artifact store;
- memory backend;
- tick traces.

## Default 15-tick day

The default schedule is intentionally rhythmic rather than purely reactive:

```text
01 orientation
02 sensing
03 execution
04 collaboration
05 sensing
06 execution
07 execution
08 collaboration
09 sensing
10 execution
11 collaboration
12 execution
13 delivery
14 maintenance
15 reflection
```

This is a starting point, not a universal law. The important invariant is that a day has a fixed budget and each tick emits a traceable state transition.

## Guardrail: Jayda ↔ Jaquan contract remains unchanged

The MVP includes a test and runtime guard for this requirement:

- If a MemoryBackend request attempts to change a protected contract, the tick records a risk flag.
- It does not create a contract-change proposal.
- It returns the original contract registry unchanged.

This lets `peer` be used for MemoryBackend collaboration without disturbing the current trading_system collaboration pattern.

## Next implementation steps

Good next increments:

1. Add JSON serialization for all tick input/output objects.
2. Add a persistent workspace backed by local files or SQLite.
3. Add explicit task lifecycle beyond accepted commitments.
4. Add memory write policy: durable fact vs task log vs skill candidate vs archive.
5. Add a scheduler that materializes one 15-tick day for one or more agents.
6. Add human approval policies for high-risk side effects.
