from __future__ import annotations

import csv
from pathlib import Path



def write_counts_csv(path: Path, intervals: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['interval_index', 'start_s', 'end_s', 'movement', 'count'])
        for row in intervals:
            for movement, count in row.get('movements', {}).items():
                writer.writerow([row['interval_index'], row['start_s'], row['end_s'], movement, count])


def write_counts_xlsx(path: Path, intervals: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = 'turning_counts'
        ws.append(['interval_index', 'start_s', 'end_s', 'movement', 'count'])
        for row in intervals:
            for movement, count in row.get('movements', {}).items():
                ws.append([row['interval_index'], row['start_s'], row['end_s'], movement, count])
        wb.save(path)
    except ModuleNotFoundError:
        # Fallback for restricted runtime: still emit a machine-readable delimited file at .xlsx path.
        with path.open('w', encoding='utf-8') as f:
            f.write('interval_index,start_s,end_s,movement,count\n')
            for row in intervals:
                for movement, count in row.get('movements', {}).items():
                    f.write(f"{row['interval_index']},{row['start_s']},{row['end_s']},{movement},{count}\n")


def write_report_html(path: Path, context: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    project = context['project']
    count_summary = context['count_summary']
    queue_summary = context['queue_summary']
    ped_summary = context['ped_summary']
    school_flags = context['school_flags']
    alignment_cards = context['alignment_cards']

    interval_rows = ''.join(f"<li>Interval {r['interval_index']} total: {r['total']}</li>" for r in count_summary.get('intervals', []))
    school_rows = ''.join(f'<li>{f}</li>' for f in school_flags)
    alignment_rows = ''.join(f"<li>{c['topic']}: {c['status']}</li>" for c in alignment_cards)

    html = f"""<!doctype html>
<html>
<head><meta charset='utf-8'><title>TMH16 Evidence Draft</title></head>
<body>
  <h1>TMH16 Video Analyzer - Draft Evidence Report</h1>
  <p><strong>Professional review required.</strong> Automated outputs are assumptions-based and must be checked by a qualified traffic engineer.</p>
  <h2>Project details</h2>
  <p>{project['name']} - {project['site_name']} ({project['site_type']})</p>
  <p>Location: {project['location']}</p>
  <h2>Survey details</h2>
  <p>Date: {project['survey_date']} | Period: {project['survey_period']}</p>
  <h2>Turning movement summary</h2>
  <ul>{interval_rows}</ul>
  <h2>Queue summary</h2>
  <p>Average queue: {queue_summary.get('average_queue', 0)} | Max queue: {queue_summary.get('max_queue', 0)}</p>
  <h2>Pedestrian summary</h2>
  <p>Total crossings: {ped_summary.get('total_crossings', 0)}</p>
  <h2>School mode flags</h2>
  <ul>{school_rows}</ul>
  <h2>TMH16 alignment notes</h2>
  <ul>{alignment_rows}</ul>
  <h2>Professional disclaimer</h2>
  <p>This draft evidence pack supports review only and does not constitute legal compliance certification or municipal approval.</p>
</body>
</html>"""
    path.write_text(html, encoding='utf-8')
