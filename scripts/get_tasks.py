"""Script to fetch and display tasks from Motion API."""

import sys
from datetime import datetime, timedelta
from os import getenv
import traceback
import json

try:
    from dotenv import load_dotenv
    from src.api.motion import MotionClient
    from src.utils.config import MotionAPIConfig
    from src.utils.exceptions import MotionAPIError, ConfigurationError, ValidationError
    from src.core.models.task import TaskStatus, TaskPriority
except ImportError as e:
    print(f"Error importing required modules: {e}")
    traceback.print_exc()
    print("Please ensure you are in the virtual environment and all dependencies are installed.")
    sys.exit(1)

def main():
    # Move env var checks to the very top
    motion_api_key = getenv("MOTION_API_KEY")
    motion_api_url = getenv("MOTION_API_URL")
    if not motion_api_key or not motion_api_url:
        missing_vars = []
        if not motion_api_key:
            missing_vars.append("MOTION_API_KEY")
        if not motion_api_url:
            missing_vars.append("MOTION_API_URL")
        raise ConfigurationError(
            "Missing required environment variables",
            details={"missing_vars": missing_vars},
        )
    try:
        # Load environment variables from .env
        load_dotenv()
        print(f"[DEBUG] MOTION_API_KEY loaded: {motion_api_key!r}")
        print("[DEBUG] Environment variables loaded:")
        print(f"[DEBUG] MOTION_API_KEY: {motion_api_key[:8]}...")
        print(f"[DEBUG] MOTION_API_URL: {motion_api_url}")

        # Parse --date argument if present
        date_str = None
        if len(sys.argv) > 2 and sys.argv[1] == "--date":
            date_str = sys.argv[2]
        elif len(sys.argv) > 1 and sys.argv[1] == "--date":
            date_str = sys.argv[2] if len(sys.argv) > 2 else None

        try:
            # Initialize client with only Motion API config
            config = MotionAPIConfig(
                motion_api_key=motion_api_key,
                motion_api_url=motion_api_url
            )
            print("[DEBUG] APIConfig initialized successfully")
            client = MotionClient(config)
            print("[DEBUG] MotionClient initialized successfully")
        except Exception as e:
            print("[ERROR] Failed to initialize MotionClient or APIConfig:", e)
            traceback.print_exc()
            raise

        try:
            # Get scheduled tasks (optionally for a custom date)
            print("[DEBUG] Fetching tasks scheduled for today...")
            if date_str:
                tasks = client.get_tasks_scheduled_for_today(params={"due_date": date_str})
            else:
                tasks = client.get_tasks_scheduled_for_today()
            print(f"[DEBUG] Received {len(tasks) if tasks else 0} tasks")
            if tasks:
                print("[DEBUG] First task data:", tasks[0].model_dump_json(indent=2))
        except ValidationError:
            # Let ValidationError propagate for test to catch
            raise
        except Exception as e:
            print("[ERROR] Failed to fetch tasks:", e)
            traceback.print_exc()
            raise

        # Display tasks
        if not tasks:
            print("\nNo tasks scheduled for today.")
            return

        print("\nTasks Scheduled for Today:")
        for task in tasks:
            print(f"\nTask: {task.name}")
            print(f"Status: {task.status.value}")
            if task.priority:
                print(f"Priority: {task.priority.value}")
            if task.description:
                print(f"Description: {task.description}")
            if task.scheduled_start:
                print(f"Scheduled Start: {task.scheduled_start.strftime('%Y-%m-%d %H:%M:%S')}")
            if task.scheduled_end:
                print(f"Scheduled End: {task.scheduled_end.strftime('%Y-%m-%d %H:%M:%S')}")
            if task.project_id:
                print(f"Project ID: {task.project_id}")
            if task.assignee_id:
                print(f"Assignee ID: {task.assignee_id}")
            if task.tags:
                print(f"Tags: {', '.join(task.tags)}")

    except MotionAPIError as e:
        print(f"\nError accessing Motion API: {e}")
        if hasattr(e, 'details'):
            print(f"Details: {e.details}")
        traceback.print_exc()
        raise
    except ConfigurationError as e:
        print(f"\nConfiguration error: {e}")
        traceback.print_exc()
        raise
    # Do not catch ValidationError here; let it propagate for tests
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main() 