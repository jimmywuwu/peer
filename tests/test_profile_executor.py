from peer import (
    AgentProfile,
    AgentState,
    Commitment,
    ContractRegistry,
    HermesProfileExecutor,
    Request,
    RequestBoard,
    TickContext,
    TickType,
    WorkerProfile,
    build_worker_prompt,
    run_tick,
)


def test_worker_prompt_keeps_strategy_discussion_with_jayda_and_execution_with_worker():
    commitment = Commitment(
        request_id="mem-42",
        title="Implement JSON tick trace",
        requester="jimmy",
        success_criteria=("TickOutput can serialize to JSON",),
        related_project="MemoryBackend",
    )

    prompt = build_worker_prompt(
        commitment,
        architect_agent_id="jayda",
        repo_path="/repo/peer",
    )

    assert "You are the isolated implementation worker for the peer Agent Loop experiment." in prompt
    assert "Architect / discussion owner: jayda" in prompt
    assert "Project: MemoryBackend" in prompt
    assert "Implement JSON tick trace" in prompt
    assert "TickOutput can serialize to JSON" in prompt
    assert "Do not change Jayda ↔ Jaquan's trading_system collaboration workflow" in prompt


def test_profile_executor_builds_safe_hermes_command_without_running_it():
    executor = HermesProfileExecutor(
        worker=WorkerProfile(profile_name="peerworker", workdir="/repo/peer"),
        dry_run=True,
    )
    commitment = Commitment(
        request_id="mem-1",
        title="Add workspace persistence",
        requester="jimmy",
        success_criteria=("workspace writes tick traces",),
        related_project="MemoryBackend",
    )

    dispatch = executor.dispatch(commitment, architect_agent_id="jayda")

    assert dispatch.worker_profile == "peerworker"
    assert dispatch.request_id == "mem-1"
    assert dispatch.dry_run is True
    assert dispatch.exit_code is None
    assert dispatch.command[:5] == ("hermes", "--profile", "peerworker", "chat", "-q")
    assert "Add workspace persistence" in dispatch.prompt
    assert "workspace writes tick traces" in dispatch.prompt


def test_execution_tick_dispatches_active_commitments_to_worker_profile_in_dry_run():
    profile = AgentProfile(agent_id="jayda", role="MemoryBackend architect", goals=("MemoryBackend",))
    state = AgentState(
        agent_id="jayda",
        active_commitments=(
            Commitment(
                request_id="mem-2",
                title="Implement workspace trace persistence",
                requester="jimmy",
                success_criteria=("trace file exists",),
                related_project="MemoryBackend",
            ),
        ),
    )
    executor = HermesProfileExecutor(
        worker=WorkerProfile(profile_name="peerworker", workdir="/repo/peer"),
        dry_run=True,
    )

    output = run_tick(
        TickContext(
            profile=profile,
            state=state,
            tick_type=TickType.EXECUTION,
            events=(),
            request_board=RequestBoard(),
            contracts=ContractRegistry(),
            worker_executor=executor,
        )
    )

    assert len(output.worker_dispatches) == 1
    dispatch = output.worker_dispatches[0]
    assert dispatch.worker_profile == "peerworker"
    assert dispatch.request_id == "mem-2"
    assert dispatch.dry_run is True
    assert "Implement workspace trace persistence" in dispatch.prompt
    assert "dispatched 1 worker task(s)" in output.summary


def test_collaboration_tick_accepts_request_but_does_not_dispatch_until_execution_tick():
    request = Request(
        request_id="mem-3",
        from_agent="jimmy",
        to_agent="jayda",
        title="Implement task lifecycle",
        context="MemoryBackend loop work",
        success_criteria=("task states exist",),
        priority=90,
        related_project="MemoryBackend",
    )
    executor = HermesProfileExecutor(
        worker=WorkerProfile(profile_name="peerworker", workdir="/repo/peer"),
        dry_run=True,
    )

    output = run_tick(
        TickContext(
            profile=AgentProfile(agent_id="jayda", role="MemoryBackend architect", goals=("MemoryBackend",)),
            state=AgentState(agent_id="jayda"),
            tick_type=TickType.COLLABORATION,
            events=(),
            request_board=RequestBoard(requests=(request,)),
            contracts=ContractRegistry(),
            worker_executor=executor,
        )
    )

    assert output.updated_requests[0].request_id == "mem-3"
    assert output.worker_dispatches == ()
    assert output.state.active_commitments[0].request_id == "mem-3"
