from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peer import (
    AgentProfile,
    AgentState,
    CollaborationPolicy,
    Contract,
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
    collaboration_policy=CollaborationPolicy(
        protected_contracts=("jayda-jaquan-trading-system",),
    ),
)

contracts = ContractRegistry(
    contracts=(
        Contract(
            contract_id="jayda-jaquan-trading-system",
            participants=("jayda", "jaquan"),
            purpose="Trading system DataProvider ↔ research runtime collaboration",
            status="protected",
        ),
    )
)

request = Request(
    request_id="mem-001",
    from_agent="jimmy",
    to_agent="jayda",
    title="Implement bounded tick loop for MemoryBackend collaboration",
    context="Use first between Jimmy and Jayda. Do not change Jaquan collaboration yet.",
    success_criteria=(
        "15-tick day schedule exists",
        "request lifecycle exists",
        "Jaquan contract remains protected",
    ),
    priority=95,
    related_project="MemoryBackend",
)

output = run_tick(
    TickContext(
        profile=profile,
        state=AgentState(agent_id="jayda"),
        tick_type=TickType.COLLABORATION,
        events=(),
        request_board=RequestBoard(requests=(request,)),
        contracts=contracts,
    )
)

print(output.summary)
for commitment in output.state.active_commitments:
    print(f"accepted: {commitment.request_id} — {commitment.title}")
