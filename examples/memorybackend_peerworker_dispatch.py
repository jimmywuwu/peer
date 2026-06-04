from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peer import Commitment, HermesProfileExecutor, WorkerProfile


commitment = Commitment(
    request_id="mem-ca3-001",
    title="Initialize MemoryBackend implementation workspace",
    requester="jimmy",
    success_criteria=(
        "ca3 contains a documented MemoryBackend implementation scaffold",
        "worker reports files changed and tests run",
    ),
    related_project="MemoryBackend",
)

executor = HermesProfileExecutor(
    worker=WorkerProfile(
        profile_name="peerworker",
        workdir="/home/jimmywu0621/interview/ca3",
    ),
    dry_run=True,
)

dispatch = executor.dispatch(commitment, architect_agent_id="jayda")

print("worker:", dispatch.worker_profile)
print("repo:", "/home/jimmywu0621/interview/ca3")
print("command:", " ".join(dispatch.command[:5]), "...")
print("task:", commitment.title)
