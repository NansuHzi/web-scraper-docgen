import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.adapters.scheduler_manager import SchedulerManager


class TestSchedulerManager:
    """SchedulerManager 单元测试"""

    def setup_method(self):
        """每个测试前创建新的 SchedulerManager 实例"""
        import src.adapters.scheduler_manager as sm
        self._orig_jobs_file = sm.JOBS_FILE
        self._orig_history_file = sm.HISTORY_FILE
        self._orig_data_dir = sm.DATA_DIR
        self._tmpdir = tempfile.TemporaryDirectory()
        tmp_path = Path(self._tmpdir.name)
        sm.DATA_DIR = tmp_path
        sm.JOBS_FILE = tmp_path / "scheduler_jobs.json"
        sm.HISTORY_FILE = tmp_path / "scheduler_history.json"
        self.manager = SchedulerManager()
        self.manager.start()

    def teardown_method(self):
        self.manager.stop()
        self._tmpdir.cleanup()
        import src.adapters.scheduler_manager as sm
        sm.JOBS_FILE = self._orig_jobs_file
        sm.HISTORY_FILE = self._orig_history_file
        sm.DATA_DIR = self._orig_data_dir

    def test_create_interval_job(self):
        job = self.manager.create_job({
            "name": "Test Job",
            "url": "https://example.com",
            "doc_type": "tech_doc",
            "schedule_type": "interval",
            "interval_seconds": 3600,
        })
        assert job["id"]
        assert job["name"] == "Test Job"
        assert job["schedule_type"] == "interval"
        assert job["interval_seconds"] == 3600
        assert job["enabled"] is True
        assert job["next_run"] is not None
        assert job["total_runs"] == 0

    def test_create_cron_job(self):
        job = self.manager.create_job({
            "name": "Cron Job",
            "url": "https://example.com",
            "schedule_type": "cron",
            "cron_expression": "0 9 * * *",
        })
        assert job["schedule_type"] == "cron"
        assert job["cron_expression"] == "0 9 * * *"

    def test_create_cron_job_invalid_expression(self):
        try:
            self.manager.create_job({
                "name": "Bad Cron",
                "url": "https://example.com",
                "schedule_type": "cron",
                "cron_expression": "invalid",
            })
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_create_interval_job_under_minimum(self):
        try:
            self.manager.create_job({
                "name": "Fast Job",
                "url": "https://example.com",
                "schedule_type": "interval",
                "interval_seconds": 10,
            })
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_list_jobs(self):
        self.manager.create_job({
            "name": "Job 1", "url": "https://a.com",
            "schedule_type": "interval", "interval_seconds": 3600,
        })
        self.manager.create_job({
            "name": "Job 2", "url": "https://b.com",
            "schedule_type": "cron", "cron_expression": "*/30 * * * *",
        })
        jobs = self.manager.list_jobs()
        assert len(jobs) == 2

    def test_get_job(self):
        created = self.manager.create_job({
            "name": "Find Me", "url": "https://example.com",
            "schedule_type": "interval", "interval_seconds": 7200,
        })
        job = self.manager.get_job(created["id"])
        assert job is not None
        assert job["name"] == "Find Me"

    def test_get_job_not_found(self):
        assert self.manager.get_job("nonexistent") is None

    def test_update_job(self):
        created = self.manager.create_job({
            "name": "Original", "url": "https://old.com",
            "schedule_type": "interval", "interval_seconds": 3600,
        })
        updated = self.manager.update_job(created["id"], {"name": "Updated", "enabled": False})
        assert updated is not None
        assert updated["name"] == "Updated"
        assert updated["enabled"] is False

    def test_delete_job(self):
        created = self.manager.create_job({
            "name": "To Delete", "url": "https://example.com",
            "schedule_type": "interval", "interval_seconds": 3600,
        })
        assert self.manager.delete_job(created["id"]) is True
        assert self.manager.get_job(created["id"]) is None
        assert self.manager.delete_job("nonexistent") is False

    def test_stats(self):
        self.manager.create_job({
            "name": "Active", "url": "https://a.com",
            "schedule_type": "interval", "interval_seconds": 3600, "enabled": True,
        })
        self.manager.create_job({
            "name": "Disabled", "url": "https://b.com",
            "schedule_type": "interval", "interval_seconds": 3600, "enabled": False,
        })
        stats = self.manager.get_stats()
        assert stats["total_jobs"] == 2
        assert stats["active_jobs"] == 1

    def test_persistence(self):
        self.manager.create_job({
            "name": "Persist", "url": "https://example.com",
            "schedule_type": "interval", "interval_seconds": 3600,
        })
        self.manager.stop()
        self.manager.start()
        jobs = self.manager.list_jobs()
        assert len(jobs) == 1
        assert jobs[0]["name"] == "Persist"
