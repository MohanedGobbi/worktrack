from unittest.mock import MagicMock
import unittest

def filter_submissions(all_subs_queryset):
    # Filter to only get the latest version for each worker
    latest_subs = {}
    for sub in all_subs_queryset:
        if sub.worker_id not in latest_subs:
            latest_subs[sub.worker_id] = sub
    
    return sorted(latest_subs.values(), key=lambda s: s.worker.get_full_name() or s.worker.email)

class TestSubmissionFilter(unittest.TestCase):
    def test_filter(self):
        # Setup mocks
        w1 = MagicMock(id=1)
        w1.get_full_name.return_value = "Adam"
        w2 = MagicMock(id=2)
        w2.get_full_name.return_value = "Zoe"
        
        s1v1 = MagicMock(worker_id=1, version=1, worker=w1)
        s1v2 = MagicMock(worker_id=1, version=2, worker=w1)
        s2v1 = MagicMock(worker_id=2, version=1, worker=w2)
        
        # In descending order of version (how it's ordered in the queryset)
        queryset = [s1v2, s1v1, s2v1]
        
        result = filter_submissions(queryset)
        
        self.assertEqual(len(result), 2)
        self.assertIn(s1v2, result)
        self.assertIn(s2v1, result)
        self.assertNotIn(s1v1, result)
        self.assertEqual(result[0].worker.get_full_name(), "Adam")
        self.assertEqual(result[1].worker.get_full_name(), "Zoe")

if __name__ == "__main__":
    unittest.main()
