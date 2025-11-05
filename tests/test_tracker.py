import unittest
from src.tankers_tracker import TankerTracker  # Adjust the import based on your actual class/function names
from src.utils.map_generator import create_map

class TestTankerTracker(unittest.TestCase):

    def setUp(self):
        self.tracker = TankerTracker()  # Initialize your main tracker class

    def test_initialization(self):
        self.assertIsNotNone(self.tracker)

    def test_create_map(self):
        map_instance = create_map()
        self.assertIsNotNone(map_instance)

    def test_update_map_with_tankers(self):
        self.tracker.update_tankers_data({
            '123456789': {'lat': 25.0, 'lon': 55.0, 'name': 'Test Tanker', 'speed': 10}
        })
        self.tracker.update_map()
        self.assertIn('123456789', self.tracker.tankers_data)

    def test_tanker_data_integrity(self):
        self.tracker.update_tankers_data({
            '987654321': {'lat': 26.0, 'lon': 54.0, 'name': 'Another Tanker', 'speed': 12}
        })
        tanker = self.tracker.tankers_data['987654321']
        self.assertEqual(tanker['name'], 'Another Tanker')
        self.assertEqual(tanker['speed'], 12)

if __name__ == '__main__':
    unittest.main()