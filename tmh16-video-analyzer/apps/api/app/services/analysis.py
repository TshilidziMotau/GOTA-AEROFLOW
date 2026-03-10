from app.workers.celery_app import celery_app


def enqueue_analysis(run_id: int) -> None:
    celery_app.send_task('app.workers.tasks.run_analysis_pipeline', args=[run_id])
