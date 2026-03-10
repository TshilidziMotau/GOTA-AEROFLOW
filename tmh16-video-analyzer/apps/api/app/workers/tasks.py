from app.db.session import SessionLocal
from app.services.cv_pipeline import run_pipeline
from app.workers.celery_app import celery_app


@celery_app.task(name='app.workers.tasks.run_analysis_pipeline')
def run_analysis_pipeline(run_id: int):
    db = SessionLocal()
    try:
        return run_pipeline(db, run_id)
    finally:
        db.close()
