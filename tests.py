import unittest
from cli import compare_version_release

class TestCompareVersionRelease(unittest.TestCase):
    def test_version_release_greater(self):
        self.assertEqual(compare_version_release("2.0-1", "1.0-1"), 1)
        self.assertEqual(compare_version_release("1.1-1", "1.0-1"), 1)
        self.assertEqual(compare_version_release("1.0-2", "1.0-1"), 1)

    def test_version_release_less(self):
        self.assertEqual(compare_version_release("1.0-1", "2.0-1"), -1)
        self.assertEqual(compare_version_release("1.0-1", "1.1-1"), -1)
        self.assertEqual(compare_version_release("1.0-1", "1.0-2"), -1)

    def test_version_release_equal(self):
        self.assertEqual(compare_version_release("1.0-1", "1.0-1"), 0)
        self.assertEqual(compare_version_release("2.0-1", "2.0-1"), 0)
        self.assertEqual(compare_version_release("1.1-1", "1.1-1"), 0)

if __name__ == '__main__':
    unittest.main()