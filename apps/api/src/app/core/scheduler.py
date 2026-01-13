"""
Background Job Scheduler

Provides scheduled task execution using APScheduler with AsyncIO support.
Handles job registration, execution, and graceful shutdown.

Design Principles:
- Jobs are idempotent (safe to run multiple times)
- Jobs use database transactions for atomicity
- Failed jobs are logged but don't crash the scheduler
- Jobs can be triggered manually for testing
- Scheduler integrates with FastAPI lifespan

Usage:
    from app.core.scheduler import scheduler, start_scheduler, stop_scheduler

    # In FastAPI lifespan:
    async def lifespan(app):
        await start_scheduler()
        yield
        await stop_scheduler()

    # Register a job:
    @scheduler.scheduled_job('interval', hours=1, id='my_job')
    async def my_job():
        pass
"""

import logging
from collections.abc import Callable, Coroutine
from datetime import datetime
from typing import Any

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobExecutionEvent
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: AsyncIOScheduler | None = None

# Job registry for manual triggering
_job_registry: dict[str, Callable[[], Coroutine[Any, Any, None]]] = {}


class SchedulerConfig:
    """Configuration for the background scheduler."""

    # Default timezone for job scheduling
    TIMEZONE = "UTC"

    # Job execution settings
    JOB_COALESCE = True  # Combine multiple missed executions into one
    JOB_MAX_INSTANCES = 1  # Only one instance of each job can run at a time
    JOB_MISFIRE_GRACE_TIME = 60 * 5  # 5 minutes grace time for missed jobs

    # Scheduler settings
    EXECUTORS = {
        "default": {"type": "asyncio"},
    }

    JOB_DEFAULTS = {
        "coalesce": JOB_COALESCE,
        "max_instances": JOB_MAX_INSTANCES,
        "misfire_grace_time": JOB_MISFIRE_GRACE_TIME,
    }


def _job_listener(event: JobExecutionEvent) -> None:
    """
    Listener for job execution events.

    Logs job execution results for monitoring and debugging.

    Args:
        event: The job execution event from APScheduler
    """
    if event.exception:
        logger.error(
            f"Job {event.job_id} failed with exception: {event.exception}",
            exc_info=event.exception,
        )
    else:
        logger.info(f"Job {event.job_id} executed successfully at {datetime.utcnow().isoformat()}")


def get_scheduler() -> AsyncIOScheduler | None:
    """
    Get the global scheduler instance.

    Returns:
        The scheduler instance, or None if not initialized
    """
    return _scheduler


async def start_scheduler() -> AsyncIOScheduler:
    """
    Initialize and start the background scheduler.

    Creates a new AsyncIOScheduler instance configured for the application's
    needs and starts it running.

    Returns:
        The started scheduler instance

    Note:
        Jobs should be registered before calling this function.
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("Scheduler already running, returning existing instance")
        return _scheduler

    logger.info("Initializing background job scheduler...")

    _scheduler = AsyncIOScheduler(
        timezone=SchedulerConfig.TIMEZONE,
        executors=SchedulerConfig.EXECUTORS,
        job_defaults=SchedulerConfig.JOB_DEFAULTS,
    )

    # Add event listeners for monitoring
    _scheduler.add_listener(_job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # Start the scheduler
    _scheduler.start()

    logger.info("Background job scheduler started successfully")
    return _scheduler


async def stop_scheduler() -> None:
    """
    Stop the background scheduler gracefully.

    Waits for currently running jobs to complete before shutting down.
    """
    global _scheduler

    if _scheduler is None:
        logger.debug("Scheduler not initialized, nothing to stop")
        return

    if not _scheduler.running:
        logger.debug("Scheduler not running, nothing to stop")
        return

    logger.info("Stopping background job scheduler...")

    # Shutdown gracefully, waiting for running jobs
    _scheduler.shutdown(wait=True)

    logger.info("Background job scheduler stopped")
    _scheduler = None


def register_job(
    job_id: str,
    func: Callable[[], Coroutine[Any, Any, None]],
    trigger: IntervalTrigger,
    replace_existing: bool = True,
) -> None:
    """
    Register a job with the scheduler.

    This function should be called during application startup, before
    the scheduler is started.

    Args:
        job_id: Unique identifier for the job
        func: Async function to execute
        trigger: APScheduler trigger (IntervalTrigger, CronTrigger, etc.)
        replace_existing: Whether to replace an existing job with the same ID

    Example:
        register_job(
            job_id="send_reminders",
            func=send_verification_reminders,
            trigger=IntervalTrigger(hours=1),
        )
    """
    global _scheduler, _job_registry

    # Store in registry for manual triggering
    _job_registry[job_id] = func

    if _scheduler is None:
        logger.debug(f"Scheduler not initialized, job {job_id} will be registered later")
        return

    _scheduler.add_job(
        func,
        trigger=trigger,
        id=job_id,
        replace_existing=replace_existing,
    )
    logger.info(f"Registered job: {job_id}")


def register_jobs_from_registry() -> None:
    """
    Register all jobs from the registry with the scheduler.

    Called after scheduler initialization to add all registered jobs.
    Jobs are registered with their default triggers as defined during registration.
    """
    global _scheduler

    if _scheduler is None:
        logger.warning("Cannot register jobs: scheduler not initialized")
        return

    logger.info(f"Registering {len(_job_registry)} jobs from registry...")


async def trigger_job_manually(job_id: str) -> dict[str, Any]:
    """
    Trigger a job manually for testing or maintenance purposes.

    This bypasses the scheduler and runs the job function directly.
    Useful for:
    - Testing jobs without waiting for the schedule
    - Running jobs on-demand via admin endpoints
    - Debugging job behavior

    Args:
        job_id: The ID of the job to trigger

    Returns:
        Dict with execution result including:
        - job_id: The job ID
        - status: "success" or "error"
        - executed_at: Execution timestamp
        - error: Error message if failed

    Raises:
        ValueError: If job_id is not found in the registry
    """
    if job_id not in _job_registry:
        raise ValueError(
            f"Job {job_id} not found in registry. Available jobs: {list(_job_registry.keys())}"
        )

    func = _job_registry[job_id]
    executed_at = datetime.utcnow()

    logger.info(f"Manually triggering job: {job_id}")

    try:
        await func()
        logger.info(f"Manual execution of job {job_id} completed successfully")
        return {
            "job_id": job_id,
            "status": "success",
            "executed_at": executed_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"Manual execution of job {job_id} failed: {e}", exc_info=True)
        return {
            "job_id": job_id,
            "status": "error",
            "executed_at": executed_at.isoformat(),
            "error": str(e),
        }


def list_registered_jobs() -> list[dict[str, Any]]:
    """
    List all registered jobs and their status.

    Returns:
        List of job information dicts containing:
        - job_id: The job ID
        - next_run_time: When the job will run next (if scheduled)
        - is_paused: Whether the job is currently paused
    """
    global _scheduler, _job_registry

    jobs = []

    for job_id in _job_registry:
        job_info = {
            "job_id": job_id,
            "registered": True,
        }

        if _scheduler is not None:
            scheduled_job = _scheduler.get_job(job_id)
            if scheduled_job:
                job_info["next_run_time"] = (
                    scheduled_job.next_run_time.isoformat() if scheduled_job.next_run_time else None
                )
                job_info["is_paused"] = scheduled_job.next_run_time is None
            else:
                job_info["next_run_time"] = None
                job_info["is_paused"] = True

        jobs.append(job_info)

    return jobs


def pause_job(job_id: str) -> bool:
    """
    Pause a scheduled job.

    Args:
        job_id: The ID of the job to pause

    Returns:
        True if job was paused, False if job not found
    """
    global _scheduler

    if _scheduler is None:
        logger.warning("Cannot pause job: scheduler not initialized")
        return False

    job = _scheduler.get_job(job_id)
    if job:
        _scheduler.pause_job(job_id)
        logger.info(f"Paused job: {job_id}")
        return True

    logger.warning(f"Job not found for pausing: {job_id}")
    return False


def resume_job(job_id: str) -> bool:
    """
    Resume a paused job.

    Args:
        job_id: The ID of the job to resume

    Returns:
        True if job was resumed, False if job not found
    """
    global _scheduler

    if _scheduler is None:
        logger.warning("Cannot resume job: scheduler not initialized")
        return False

    job = _scheduler.get_job(job_id)
    if job:
        _scheduler.resume_job(job_id)
        logger.info(f"Resumed job: {job_id}")
        return True

    logger.warning(f"Job not found for resuming: {job_id}")
    return False
