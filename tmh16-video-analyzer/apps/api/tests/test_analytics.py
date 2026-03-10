import unittest

from app.services.analytics import summarize_turning_events, summarize_queue_events, school_mode_flags


class AnalyticsTests(unittest.TestCase):
    def test_turning_summary_peak(self):
        data = [
            {'event_time_s': 10, 'movement': 'left'},
            {'event_time_s': 20, 'movement': 'left'},
            {'event_time_s': 910, 'movement': 'right'},
        ]
        summary = summarize_turning_events(data)
        self.assertEqual(summary['peak_interval']['interval_index'], 0)

    def test_queue_summary(self):
        data = [
            {'event_time_s': 0, 'occupied_count': 0},
            {'event_time_s': 10, 'occupied_count': 2},
            {'event_time_s': 20, 'occupied_count': 2},
        ]
        summary = summarize_queue_events(data)
        self.assertEqual(summary['max_queue'], 2)
        self.assertGreaterEqual(summary['queue_duration_s'], 10)

    def test_school_flags(self):
        flags = school_mode_flags({'max_queue': 7, 'average_queue': 4.5}, {'total_crossings': 25}, 150)
        self.assertTrue(flags)


if __name__ == '__main__':
    unittest.main()
