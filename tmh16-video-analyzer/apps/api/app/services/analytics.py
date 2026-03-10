from __future__ import annotations

from collections import Counter, defaultdict


def summarize_turning_events(events: list[dict]) -> dict:
    intervals: dict[int, Counter] = defaultdict(Counter)
    for e in events:
        bucket = int(float(e['event_time_s']) // 900)
        intervals[bucket][e['movement']] += 1

    rows = []
    for bucket, movements in sorted(intervals.items()):
        rows.append(
            {
                'interval_index': bucket,
                'start_s': bucket * 900,
                'end_s': (bucket + 1) * 900,
                'movements': dict(movements),
                'total': int(sum(movements.values())),
            }
        )

    peak = max(rows, key=lambda r: r['total'], default=None)
    return {'intervals': rows, 'peak_interval': peak}


def summarize_queue_events(events: list[dict]) -> dict:
    if not events:
        return {'average_queue': 0.0, 'max_queue': 0, 'queue_duration_s': 0.0, 'timeline': []}

    timeline = sorted(events, key=lambda r: r['event_time_s'])
    values = [int(r['occupied_count']) for r in timeline]
    times = [float(r['event_time_s']) for r in timeline]

    duration = 0.0
    for idx in range(1, len(timeline)):
        if values[idx - 1] > 0:
            duration += max(0.0, times[idx] - times[idx - 1])

    return {
        'average_queue': float(sum(values) / len(values)),
        'max_queue': max(values),
        'queue_duration_s': duration,
        'timeline': timeline[:500],
    }


def summarize_pedestrian_events(events: list[dict]) -> dict:
    crossing_counts = Counter(e['crossing_name'] for e in events)
    return {
        'total_crossings': len(events),
        'crossing_counts': dict(crossing_counts),
        'events': events[:500],
    }


def school_mode_flags(queue_summary: dict, pedestrian_summary: dict, turning_total: int) -> list[str]:
    flags: list[str] = []
    if queue_summary.get('max_queue', 0) >= 6:
        flags.append('queue_buildup_near_gate_estimated')
    if pedestrian_summary.get('total_crossings', 0) >= 20:
        flags.append('high_pedestrian_activity_during_peak')
    if queue_summary.get('average_queue', 0) >= 4 and pedestrian_summary.get('total_crossings', 0) >= 10:
        flags.append('potential_vehicle_pedestrian_conflict_review_required')
    if turning_total >= 120:
        flags.append('high_vehicle_activity_school_window')
    return flags


def tmh16_alignment_card(
    *,
    has_peak_15: bool,
    has_movement_breakdown: bool,
    has_queue: bool,
    has_peds: bool,
    has_school: bool,
    has_parking: bool,
    has_public_transport: bool,
    has_service_heavy: bool,
) -> list[dict]:
    def st(value: bool) -> str:
        return 'complete' if value else 'incomplete'

    return [
        {'topic': 'peak_15_minute_data', 'status': st(has_peak_15)},
        {'topic': 'separate_movement_reporting', 'status': st(has_movement_breakdown)},
        {'topic': 'queue_evidence', 'status': st(has_queue)},
        {'topic': 'pedestrian_observations', 'status': st(has_peds)},
        {'topic': 'school_dropoff_observations', 'status': st(has_school)},
        {'topic': 'parking_observations', 'status': st(has_parking)},
        {'topic': 'public_transport_observations', 'status': 'not_observed' if not has_public_transport else 'complete'},
        {'topic': 'service_heavy_vehicle_observations', 'status': 'not_observed' if not has_service_heavy else 'complete'},
    ]
