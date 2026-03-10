import tempfile
import unittest
from pathlib import Path

from app.services.reporting import write_counts_csv, write_counts_xlsx, write_report_html


class ReportingTests(unittest.TestCase):
    def test_export_files_generated(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            intervals = [
                {'interval_index': 0, 'start_s': 0, 'end_s': 900, 'movements': {'left': 3, 'right': 1}, 'total': 4}
            ]
            csv_path = root / 'counts.csv'
            xlsx_path = root / 'counts.xlsx'
            html_path = root / 'report.html'

            write_counts_csv(csv_path, intervals)
            write_counts_xlsx(xlsx_path, intervals)
            write_report_html(html_path, {
                'project': {'name': 'Test', 'site_name': 'Site', 'site_type': 'school', 'location': 'L', 'survey_date': '2026-01-01', 'survey_period': 'AM'},
                'count_summary': {'intervals': intervals},
                'queue_summary': {'average_queue': 1.0, 'max_queue': 2},
                'ped_summary': {'total_crossings': 5},
                'school_flags': ['flag1'],
                'alignment_cards': [{'topic': 'peak', 'status': 'complete'}],
            })

            self.assertTrue(csv_path.exists())
            self.assertTrue(xlsx_path.exists())
            self.assertTrue(html_path.exists())


if __name__ == '__main__':
    unittest.main()
