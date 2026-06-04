from __future__ import annotations

import subprocess
from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable, Protocol


class TickType(str, Enum):
    ORIENTATION = "orientation"
    SENSING = "sensing"
    EXECUTION = "execution"
    COLLABORATION = "collaboration"
    DELIVERY = "delivery"
    MAINTENANCE = "maintenance"
    REFLECTION = "reflection"


class EventType(str, Enum):
    REQUEST = "request"
    CONTRACT = "contract"
    GOAL = "goal"
    DATA = "data"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    REFLECTION = "reflection"


class RequestStatus(str, Enum):
    CREATED = "created"
    SEEN = "seen"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    NEEDS_CLARIFICATION = "needs_clarification"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DELIVERED = "delivered"
    VERIFIED = "verified"
    CLOSED = "closed"
    DEFERRED = "deferred"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class CollaborationPolicy:
    protected_contracts: tuple[str, ...] = ()
    auto_accept_projects: tuple[str, ...] = ("MemoryBackend",)
    minimum_acceptance_score: int = 60


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    role: str
    goals: tuple[str, ...] = ()
    collaboration_policy: CollaborationPolicy = CollaborationPolicy()


@dataclass(frozen=True)
class Event:
    event_id: str
    source: str
    event_type: EventType
    title: str
    importance: int = 0
    urgency: int = 0
    role_relevance: int = 0
    actionability: int = 0
    confidence: int = 100

    @property
    def triage_score(self) -> int:
        return round(
            self.importance * 0.35
            + self.urgency * 0.20
            + self.role_relevance * 0.30
            + self.actionability * 0.15
        )


@dataclass(frozen=True)
class Request:
    request_id: str
    from_agent: str
    to_agent: str
    title: str
    context: str
    success_criteria: tuple[str, ...]
    priority: int = 0
    related_project: str | None = None
    requested_contract_change: str | None = None
    status: RequestStatus = RequestStatus.CREATED


@dataclass(frozen=True)
class RequestBoard:
    requests: tuple[Request, ...] = ()

    def pending_for(self, agent_id: str) -> tuple[Request, ...]:
        return tuple(
            request
            for request in self.requests
            if request.to_agent == agent_id
            and request.status in {RequestStatus.CREATED, RequestStatus.SEEN, RequestStatus.DEFERRED}
        )


@dataclass(frozen=True)
class Contract:
    contract_id: str
    participants: tuple[str, ...]
    purpose: str
    status: str = "active"
    version: int = 1


@dataclass(frozen=True)
class ContractRegistry:
    contracts: tuple[Contract, ...] = ()

    def get(self, contract_id: str) -> Contract | None:
        for contract in self.contracts:
            if contract.contract_id == contract_id:
                return contract
        return None


@dataclass(frozen=True)
class Commitment:
    request_id: str
    title: str
    requester: str
    success_criteria: tuple[str, ...]
    related_project: str | None = None


@dataclass(frozen=True)
class WorkerProfile:
    profile_name: str
    workdir: str
    toolsets: tuple[str, ...] = ("terminal", "file")


@dataclass(frozen=True)
class WorkerDispatch:
    request_id: str
    worker_profile: str
    command: tuple[str, ...]
    prompt: str
    dry_run: bool
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


class WorkerExecutor(Protocol):
    def dispatch(self, commitment: Commitment, architect_agent_id: str) -> WorkerDispatch:
        """Dispatch one commitment to an isolated worker profile."""


@dataclass(frozen=True)
class HermesProfileExecutor:
    worker: WorkerProfile
    dry_run: bool = True
    timeout_seconds: int = 600

    def dispatch(self, commitment: Commitment, architect_agent_id: str) -> WorkerDispatch:
        prompt = build_worker_prompt(
            commitment,
            architect_agent_id=architect_agent_id,
            repo_path=self.worker.workdir,
        )
        command = (
            "hermes",
            "--profile",
            self.worker.profile_name,
            "chat",
            "-q",
            prompt,
            "--toolsets",
            ",".join(self.worker.toolsets),
        )
        if self.dry_run:
            return WorkerDispatch(
                request_id=commitment.request_id,
                worker_profile=self.worker.profile_name,
                command=command,
                prompt=prompt,
                dry_run=True,
            )

        completed = subprocess.run(
            command,
            cwd=self.worker.workdir,
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        return WorkerDispatch(
            request_id=commitment.request_id,
            worker_profile=self.worker.profile_name,
            command=command,
            prompt=prompt,
            dry_run=False,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


def build_worker_prompt(commitment: Commitment, *, architect_agent_id: str, repo_path: str) -> str:
    criteria = "\n".join(f"- {criterion}" for criterion in commitment.success_criteria)
    project = commitment.related_project or "unspecified"
    return f"""You are the isolated implementation worker for the peer Agent Loop experiment.

Architect / discussion owner: {architect_agent_id}
Requester: {commitment.requester}
Project: {project}
Repository: {repo_path}
Request ID: {commitment.request_id}
Task: {commitment.title}

Success criteria:
{criteria}

Operating boundaries:
- Keep architecture/product discussion with {architect_agent_id}; focus on implementation inside the repository.
- Use tests first for behavior changes.
- Keep changes small and report exact files changed, tests run, and any blockers.
- Do not change Jayda ↔ Jaquan's trading_system collaboration workflow or protected contract.
"""


@dataclass(frozen=True)
class AgentState:
    agent_id: str
    active_commitments: tuple[Commitment, ...] = ()
    last_tick_summary: str | None = None


@dataclass(frozen=True)
class TickBudget:
    max_commitments: int = 1
    max_memory_writes: int = 3
    max_external_messages: int = 1
    max_tool_calls: int = 8


@dataclass(frozen=True)
class ScheduledTick:
    tick_number: int
    tick_type: TickType


@dataclass(frozen=True)
class TickContext:
    profile: AgentProfile
    state: AgentState
    tick_type: TickType
    events: tuple[Event, ...]
    request_board: RequestBoard
    contracts: ContractRegistry
    budget: TickBudget = TickBudget()
    worker_executor: WorkerExecutor | None = None


@dataclass(frozen=True)
class TickOutput:
    state: AgentState
    contracts: ContractRegistry
    updated_requests: tuple[Request, ...]
    deferred_events: tuple[Event, ...]
    memory_writes: tuple[str, ...]
    contract_change_proposals: tuple[str, ...]
    risk_flags: tuple[str, ...]
    worker_dispatches: tuple[WorkerDispatch, ...]
    summary: str


def standard_15_tick_schedule() -> tuple[ScheduledTick, ...]:
    tick_types = (
        TickType.ORIENTATION,
        TickType.SENSING,
        TickType.EXECUTION,
        TickType.COLLABORATION,
        TickType.SENSING,
        TickType.EXECUTION,
        TickType.EXECUTION,
        TickType.COLLABORATION,
        TickType.SENSING,
        TickType.EXECUTION,
        TickType.COLLABORATION,
        TickType.EXECUTION,
        TickType.DELIVERY,
        TickType.MAINTENANCE,
        TickType.REFLECTION,
    )
    return tuple(ScheduledTick(index + 1, tick_type) for index, tick_type in enumerate(tick_types))


def run_tick(context: TickContext) -> TickOutput:
    relevant_events, deferred_events = _triage_events(context.events)
    updated_requests, new_commitments, risk_flags = _triage_requests(context)

    active_commitments = context.state.active_commitments + new_commitments
    worker_dispatches = _dispatch_worker_tasks(context, active_commitments)
    summary = _summarize(context.tick_type, relevant_events, new_commitments, risk_flags, worker_dispatches)
    next_state = replace(
        context.state,
        active_commitments=active_commitments,
        last_tick_summary=summary,
    )

    return TickOutput(
        state=next_state,
        contracts=context.contracts,
        updated_requests=updated_requests,
        deferred_events=deferred_events,
        memory_writes=(),
        contract_change_proposals=(),
        risk_flags=risk_flags,
        worker_dispatches=worker_dispatches,
        summary=summary,
    )


def _triage_events(events: Iterable[Event]) -> tuple[tuple[Event, ...], tuple[Event, ...]]:
    relevant: list[Event] = []
    deferred: list[Event] = []
    for event in events:
        if event.triage_score >= 60:
            relevant.append(event)
        else:
            deferred.append(event)
    return tuple(relevant), tuple(deferred)


def _triage_requests(context: TickContext) -> tuple[tuple[Request, ...], tuple[Commitment, ...], tuple[str, ...]]:
    pending = sorted(
        context.request_board.pending_for(context.profile.agent_id),
        key=lambda request: request.priority,
        reverse=True,
    )
    commitments: list[Commitment] = []
    updated: list[Request] = []
    risk_flags: list[str] = []

    for request in pending:
        blocked_contract = _blocked_protected_contract(context, request)
        if blocked_contract is not None:
            risk_flags.append(f"protected_contract_change_blocked:{blocked_contract}")

        can_accept = (
            len(commitments) < context.budget.max_commitments
            and _request_score(context.profile, request) >= context.profile.collaboration_policy.minimum_acceptance_score
        )

        if can_accept:
            updated.append(replace(request, status=RequestStatus.ACCEPTED))
            commitments.append(
                Commitment(
                    request_id=request.request_id,
                    title=request.title,
                    requester=request.from_agent,
                    success_criteria=request.success_criteria,
                    related_project=request.related_project,
                )
            )
        else:
            updated.append(replace(request, status=RequestStatus.DEFERRED))

    return tuple(updated), tuple(commitments), tuple(risk_flags)


def _blocked_protected_contract(context: TickContext, request: Request) -> str | None:
    requested = request.requested_contract_change
    if requested is None:
        return None
    if requested not in context.profile.collaboration_policy.protected_contracts:
        return None
    if context.contracts.get(requested) is None:
        return None
    return requested


def _request_score(profile: AgentProfile, request: Request) -> int:
    score = request.priority
    if request.related_project in profile.collaboration_policy.auto_accept_projects:
        score += 20
    goal_text = " ".join(profile.goals).lower()
    if request.related_project and request.related_project.lower() in goal_text:
        score += 10
    return min(score, 100)


def _dispatch_worker_tasks(context: TickContext, active_commitments: tuple[Commitment, ...]) -> tuple[WorkerDispatch, ...]:
    if context.tick_type is not TickType.EXECUTION or context.worker_executor is None:
        return ()
    return tuple(
        context.worker_executor.dispatch(commitment, architect_agent_id=context.profile.agent_id)
        for commitment in active_commitments
    )


def _summarize(
    tick_type: TickType,
    relevant_events: tuple[Event, ...],
    commitments: tuple[Commitment, ...],
    risk_flags: tuple[str, ...],
    worker_dispatches: tuple[WorkerDispatch, ...],
) -> str:
    projects = sorted({commitment.related_project for commitment in commitments if commitment.related_project})
    parts = [f"{tick_type.value} tick"]
    if relevant_events:
        parts.append(f"observed {len(relevant_events)} relevant event(s)")
    if commitments:
        parts.append(f"accepted {len(commitments)} commitment(s)")
    if projects:
        parts.append("projects: " + ", ".join(projects))
    if risk_flags:
        parts.append("risk flags: " + ", ".join(risk_flags))
    if worker_dispatches:
        parts.append(f"dispatched {len(worker_dispatches)} worker task(s)")
    return "; ".join(parts)


__all__ = [
    "AgentProfile",
    "AgentState",
    "CollaborationPolicy",
    "Commitment",
    "Contract",
    "ContractRegistry",
    "Event",
    "EventType",
    "HermesProfileExecutor",
    "Request",
    "RequestBoard",
    "RequestStatus",
    "RiskLevel",
    "ScheduledTick",
    "TickBudget",
    "TickContext",
    "TickOutput",
    "TickType",
    "WorkerDispatch",
    "WorkerExecutor",
    "WorkerProfile",
    "build_worker_prompt",
    "run_tick",
    "standard_15_tick_schedule",
]
