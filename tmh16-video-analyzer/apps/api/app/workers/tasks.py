from app.workers.celery_app import celery_app


@celery_app.task(name='app.workers.tasks.run_analysis_pipeline')
def run_analysis_pipeline(run_id: int):
    # TODO: integrate OpenCV/YOLO/ByteTrack pipeline stages with persisted event outputs.
    return {'run_id': run_id, 'status': 'completed', 'notes': 'Skeleton pipeline executed'}
