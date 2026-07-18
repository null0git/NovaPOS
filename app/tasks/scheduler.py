"""Registers all recurring background jobs on the shared APScheduler instance."""
from app.extensions import scheduler


def init_scheduler(app):
    from app.tasks.backup_tasks import nightly_backup_job
    from app.tasks.notification_tasks import stale_notification_cleanup_job
    from app.tasks.report_tasks import daily_report_snapshot_job

    if scheduler.running:
        return scheduler

    scheduler.add_job(
        func=lambda: nightly_backup_job(app),
        trigger="cron", hour=2, minute=0, id="nightly_backup", replace_existing=True,
    )
    scheduler.add_job(
        func=lambda: stale_notification_cleanup_job(app),
        trigger="cron", hour=3, minute=0, id="notification_cleanup", replace_existing=True,
    )
    scheduler.add_job(
        func=lambda: daily_report_snapshot_job(app),
        trigger="cron", hour=23, minute=55, id="daily_report_snapshot", replace_existing=True,
    )

    scheduler.start()
    return scheduler
