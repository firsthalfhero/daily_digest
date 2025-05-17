import sys
from datetime import datetime, time, timedelta
from typing import Optional, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from zoneinfo import ZoneInfo
from src.utils.timezone import SYDNEY_TIMEZONE, convert_to_timezone
from src.utils.logging import get_logger

class DigestScheduler:
    def __init__(self, 
                 job_func: Callable,
                 schedule_time: time = time(6, 30),
                 timezone: ZoneInfo = SYDNEY_TIMEZONE,
                 logger=None):
        self.logger = logger or get_logger(__name__)
        self.scheduler = BackgroundScheduler(timezone=timezone)
        self.job_func = job_func
        self.schedule_time = schedule_time
        self.timezone = timezone
        self.job = None
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        self.scheduler.add_listener(self._on_job_missed, EVENT_JOB_MISSED)

    def _on_job_executed(self, event):
        self.logger.info("schedule_job_executed", job_id=event.job_id, scheduled_run_time=str(event.scheduled_run_time))

    def _on_job_error(self, event):
        self.logger.error("schedule_job_error", job_id=event.job_id, scheduled_run_time=str(event.scheduled_run_time))
        self._recover_job(event)

    def _on_job_missed(self, event):
        self.logger.warning("schedule_job_missed", job_id=event.job_id, scheduled_run_time=str(event.scheduled_run_time))
        self._recover_job(event)

    def _recover_job(self, event):
        # Basic recovery: log and optionally re-run missed/failed jobs
        self.logger.info("schedule_recovery_attempt", job_id=event.job_id)
        # TODO: Implement more robust recovery logic (e.g., re-queue, alert)

    def start(self):
        if not self.job:
            self.schedule_digest()
        self.logger.info("scheduler_started", schedule_time=str(self.schedule_time), timezone=str(self.timezone))
        self.scheduler.start()

    def shutdown(self, wait=True):
        self.logger.info("scheduler_shutdown")
        self.scheduler.shutdown(wait=wait)

    def schedule_digest(self, schedule_time: Optional[time] = None, timezone: Optional[ZoneInfo] = None):
        schedule_time = schedule_time or self.schedule_time
        timezone = timezone or self.timezone
        if self.job:
            self.scheduler.remove_job(self.job.id)
        self.job = self.scheduler.add_job(
            self.job_func,
            trigger=CronTrigger(hour=schedule_time.hour, minute=schedule_time.minute, timezone=timezone),
            id="digest_delivery",
            replace_existing=True,
            misfire_grace_time=3600,  # 1 hour grace
        )
        self.logger.info("digest_scheduled", hour=schedule_time.hour, minute=schedule_time.minute, timezone=str(timezone))

    def run_digest_now(self):
        self.logger.info("manual_digest_triggered")
        try:
            self.job_func()
            self.logger.info("manual_digest_completed")
        except Exception as e:
            self.logger.error("manual_digest_failed", error=str(e))
            self._recover_job(event=None)

    # Monitoring stubs
    def get_status(self):
        # Return current schedule and last run info
        return {
            "next_run_time": str(self.job.next_run_time) if self.job else None,
            "timezone": str(self.timezone),
        }

    def get_history(self):
        # TODO: Implement persistent job history tracking
        return []

# Example usage (to be placed in main or a script):
# from src.digest_email.sender import EmailSender
# def send_digest():
#     sender = EmailSender()
#     sender.send_templated_email("digest.html", context={})
# scheduler = DigestScheduler(send_digest)
# scheduler.start() 