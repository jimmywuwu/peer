# Profile Delegation Experiment

This note captures the first split-brain-safe operating model for the MemoryBackend / Agent Loop experiment.

Important framing: this is not yet a multi-agent collaboration structure. `peerworker` is Jayda's implementation worker. The success criterion is that Jayda can define reusable, bounded workflows that future agents can reuse; `peerworker` is the first executor proving the workflow.

## Roles

### Jayda profile

Jayda remains the discussion and architecture profile.

Responsibilities:

- discuss MemoryBackend architecture and product direction with Jimmy;
- decide what should become a concrete implementation commitment;
- protect existing collaboration context, especially the Jayda ↔ Jaquan trading_system workflow;
- review worker outputs before folding them back into durable architecture decisions.

Jayda should not casually absorb implementation-worker context into long-term memory. Worker outputs should be treated as artifacts/traces, not automatically as durable truth.

### peerworker profile

`peerworker` is the isolated implementation profile created for this experiment.

Created with:

```bash
hermes profile create peerworker --clone --clone-from jayda --no-alias \
  --description "Experimental worker profile for peer tick-based Agent Loop execution. Jayda discusses MemoryBackend architecture with Jimmy; peerworker performs isolated implementation ticks to avoid context mixing."
```

Verified with:

```bash
hermes --profile peerworker chat -q "Reply with exactly: peerworker ready" --toolsets safe --quiet
```

Result:

```text
peerworker ready
```

Responsibilities:

- convert Jayda-defined MemoryBackend commitments into concrete implementation work in `https://github.com/jimmywuwu/ca3`;
- follow reusable workflow contracts that can later be adopted by other specialized agents;
- use narrow toolsets when possible;
- report files changed, tests run, and blockers;
- avoid architecture drift and avoid changing protected collaboration contracts.

## How `peer` models this

The runtime now includes:

- `WorkerProfile`: Hermes profile name, working directory, and allowed toolsets;
- `HermesProfileExecutor`: builds and optionally runs a `hermes --profile <worker> chat -q ...` command;
- `WorkerDispatch`: captures the generated prompt, command, exit code, stdout/stderr, and dry-run status;
- `build_worker_prompt`: creates a bounded implementation prompt from a `Commitment`.

Execution ticks can dispatch active commitments to the worker profile:

```python
from peer import HermesProfileExecutor, WorkerProfile

executor = HermesProfileExecutor(
    worker=WorkerProfile(
        profile_name="peerworker",
        workdir="/home/jimmywu0621/interview/ca3",
    ),
    dry_run=True,
)
```

`dry_run=True` is the default safety mode. It produces the exact Hermes command and prompt without spawning the worker. Set `dry_run=False` only when the surrounding scheduler is ready to execute implementation ticks for real.

## Boundary rule

The worker prompt always includes:

```text
Do not change Jayda ↔ Jaquan's trading_system collaboration workflow or protected contract.
```

This keeps the MemoryBackend/peer experiment from silently altering the trading_system collaboration model.

## Future runtime behavior

A full execution tick should eventually:

1. read accepted commitments from the workspace;
2. dispatch bounded implementation tasks to `peerworker`;
3. collect `WorkerDispatch` traces;
4. write trace artifacts to the workspace;
5. return summaries to Jayda for architecture review;
6. only then update durable MemoryBackend decisions.

This creates a deliberate context membrane:

```text
Jimmy ↔ Jayda: architecture / product / memory decisions
Jayda → peer loop: accepted implementation commitment
peer loop → peerworker: isolated execution
peerworker → peer loop: trace + artifact summary
peer loop → Jayda: reviewable result
```

The point is not to make Jayda do less thinking. The point is to prevent implementation noise from becoming architecture memory by accident.
