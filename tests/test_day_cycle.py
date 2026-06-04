from peer import (
    AgentProfile,
    AgentState,
    CollaborationPolicy,
    Contract,
    ContractRegistry,
    Event,
    EventType,
    Request,
    RequestBoard,
    RequestStatus,
    RiskLevel,
    TickBudget,
    TickContext,
    TickType,
    run_tick,
    standard_15_tick_schedule,
)


def test_standard_schedule_has_exactly_15_ticks_with_expected_modes():
    schedule = standard_15_tick_schedule()

    assert len(schedule) == 15
    assert [tick.tick_number for tick in schedule] == list(range(1, 16))
    assert [tick.tick_type for tick in schedule].count(TickType.ORIENTATION) == 1
    assert [tick.tick_type for tick in schedule].count(TickType.SENSING) == 3
    assert [tick.tick_type for tick in schedule].count(TickType.EXECUTION) == 5
    assert [tick.tick_type for tick in schedule].count(TickType.COLLABORATION) == 3
    assert [tick.tick_type for tick in schedule].count(TickType.DELIVERY) == 1
    assert [tick.tick_type for tick in schedule].count(TickType.MAINTENANCE) == 1
    assert [tick.tick_type for tick in schedule].count(TickType.REFLECTION) == 1


def test_tick_promotes_relevant_memorybackend_request_to_active_commitment():
    profile = AgentProfile(
        agent_id="jayda",
        role="MemoryBackend collaborator",
        goals=("Design MemoryBackend operating loop",),
        collaboration_policy=CollaborationPolicy(protected_contracts=("jayda-jaquan-trading-system",)),
    )
    state = AgentState(agent_id="jayda")
    request = Request(
        request_id="req-1",
        from_agent="jimmy",
        to_agent="jayda",
        title="Implement tick loop MVP",
        context="Use this first for Jayda and MemoryBackend collaboration.",
        success_criteria=("15 tick schedule exists", "request lifecycle exists"),
        priority=90,
        related_project="MemoryBackend",
    )
    board = RequestBoard(requests=(request,))

    output = run_tick(
        TickContext(
            profile=profile,
            state=state,
            tick_type=TickType.COLLABORATION,
            events=(),
            request_board=board,
            contracts=ContractRegistry(),
            budget=TickBudget(max_commitments=2),
        )
    )

    assert output.updated_requests[0].request_id == "req-1"
    assert output.updated_requests[0].status == RequestStatus.ACCEPTED
    assert output.state.active_commitments[0].request_id == "req-1"
    assert output.state.active_commitments[0].success_criteria == request.success_criteria
    assert "MemoryBackend" in output.summary


def test_tick_defers_low_relevance_event_without_creating_commitment():
    profile = AgentProfile(agent_id="jayda", role="MemoryBackend collaborator", goals=("MemoryBackend",))
    state = AgentState(agent_id="jayda")
    event = Event(
        event_id="evt-1",
        source="ambient-interest-feed",
        event_type=EventType.OPPORTUNITY,
        title="Abstract art exhibition",
        importance=20,
        urgency=10,
        role_relevance=5,
        actionability=20,
    )

    output = run_tick(
        TickContext(
            profile=profile,
            state=state,
            tick_type=TickType.SENSING,
            events=(event,),
            request_board=RequestBoard(),
            contracts=ContractRegistry(),
        )
    )

    assert output.deferred_events == (event,)
    assert output.state.active_commitments == ()
    assert output.memory_writes == ()


def test_protected_jaquan_contract_is_not_modified_by_memorybackend_tick():
    profile = AgentProfile(
        agent_id="jayda",
        role="MemoryBackend collaborator",
        goals=("MemoryBackend",),
        collaboration_policy=CollaborationPolicy(protected_contracts=("jayda-jaquan-trading-system",)),
    )
    protected_contract = Contract(
        contract_id="jayda-jaquan-trading-system",
        participants=("jayda", "jaquan"),
        purpose="Trading system DataProvider ↔ research runtime collaboration",
        status="protected",
        version=1,
    )
    registry = ContractRegistry(contracts=(protected_contract,))
    request = Request(
        request_id="req-contract",
        from_agent="jimmy",
        to_agent="jayda",
        title="Use loop for MemoryBackend but keep Jaquan workflow unchanged",
        context="Do not change Jayda and Jaquan trading_system collaboration yet.",
        success_criteria=("protected contract remains unchanged",),
        priority=100,
        related_project="MemoryBackend",
        requested_contract_change="jayda-jaquan-trading-system",
    )

    output = run_tick(
        TickContext(
            profile=profile,
            state=AgentState(agent_id="jayda"),
            tick_type=TickType.COLLABORATION,
            events=(),
            request_board=RequestBoard(requests=(request,)),
            contracts=registry,
        )
    )

    assert output.contract_change_proposals == ()
    assert output.risk_flags == ("protected_contract_change_blocked:jayda-jaquan-trading-system",)
    assert output.contracts.get("jayda-jaquan-trading-system") == protected_contract


def test_tick_budget_limits_number_of_new_commitments():
    profile = AgentProfile(agent_id="jayda", role="MemoryBackend collaborator", goals=("MemoryBackend",))
    requests = tuple(
        Request(
            request_id=f"req-{idx}",
            from_agent="jimmy",
            to_agent="jayda",
            title=f"Important MemoryBackend task {idx}",
            context="MemoryBackend",
            success_criteria=("accepted",),
            priority=100 - idx,
            related_project="MemoryBackend",
        )
        for idx in range(3)
    )

    output = run_tick(
        TickContext(
            profile=profile,
            state=AgentState(agent_id="jayda"),
            tick_type=TickType.COLLABORATION,
            events=(),
            request_board=RequestBoard(requests=requests),
            contracts=ContractRegistry(),
            budget=TickBudget(max_commitments=1),
        )
    )

    assert [commitment.request_id for commitment in output.state.active_commitments] == ["req-0"]
    assert [request.status for request in output.updated_requests] == [
        RequestStatus.ACCEPTED,
        RequestStatus.DEFERRED,
        RequestStatus.DEFERRED,
    ]
