import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, time, timedelta
from freezegun import freeze_time
from zoneinfo import ZoneInfo
from src.core.scheduler import DigestScheduler
from src.utils.timezone import SYDNEY_TIMEZONE

@pytest.fixture
def mock_job_func():
    return MagicMock()

@pytest.fixture
def mock_logger():
    return MagicMock()

@freeze_time("2024-06-01 06:29:00+10:00")
def test_digest_scheduled_at_630_sydney(mock_job_func, mock_logger):
    scheduler = DigestScheduler(job_func=mock_job_func, logger=mock_logger)
    scheduler.schedule_digest()
    job = scheduler.job
    assert job.trigger.fields[5].expressions[0].first == 6  # hour
    assert job.trigger.fields[6].expressions[0].first == 30  # minute
    assert job.trigger.timezone == SYDNEY_TIMEZONE
    mock_logger.info.assert_any_call("digest_scheduled", hour=6, minute=30, timezone=str(SYDNEY_TIMEZONE))

@freeze_time("2024-06-01 06:30:00+10:00")
def test_manual_digest_trigger(mock_job_func, mock_logger):
    scheduler = DigestScheduler(job_func=mock_job_func, logger=mock_logger)
    scheduler.run_digest_now()
    mock_job_func.assert_called_once()
    mock_logger.info.assert_any_call("manual_digest_triggered")
    mock_logger.info.assert_any_call("manual_digest_completed")

@freeze_time("2024-06-01 07:00:00+10:00")
def test_configurable_schedule_time(mock_job_func, mock_logger):
    custom_time = time(7, 0)
    scheduler = DigestScheduler(job_func=mock_job_func, schedule_time=custom_time, logger=mock_logger)
    scheduler.schedule_digest()
    job = scheduler.job
    assert job.trigger.fields[5].expressions[0].first == 7  # hour
    assert job.trigger.fields[6].expressions[0].first == 0  # minute
    mock_logger.info.assert_any_call("digest_scheduled", hour=7, minute=0, timezone=str(SYDNEY_TIMEZONE))

@freeze_time("2024-06-01 06:30:00+10:00")
def test_missed_job_recovery(mock_job_func, mock_logger):
    scheduler = DigestScheduler(job_func=mock_job_func, logger=mock_logger)
    # Simulate a missed job event
    event = MagicMock()
    event.job_id = "digest_delivery"
    event.scheduled_run_time = datetime.now(SYDNEY_TIMEZONE)
    scheduler._on_job_missed(event)
    mock_logger.warning.assert_any_call("schedule_job_missed", job_id="digest_delivery", scheduled_run_time=str(event.scheduled_run_time))
    mock_logger.info.assert_any_call("schedule_recovery_attempt", job_id="digest_delivery")

@freeze_time("2024-06-01 06:30:00+10:00")
def test_logging_on_job_executed(mock_job_func, mock_logger):
    scheduler = DigestScheduler(job_func=mock_job_func, logger=mock_logger)
    event = MagicMock()
    event.job_id = "digest_delivery"
    event.scheduled_run_time = datetime.now(SYDNEY_TIMEZONE)
    scheduler._on_job_executed(event)
    mock_logger.info.assert_any_call("schedule_job_executed", job_id="digest_delivery", scheduled_run_time=str(event.scheduled_run_time)) 