"""Tests for the Data Manager (run from the repo root:
python -m unittest discover -s tests -v)."""

import os
import tempfile
import unittest

from data_managerpart2.data_manager import DataManager
from data_managerpart2.json_storage import JsonStorage
from data_managerpart2.memory_storage import MemoryStorage

SINGAPORE_HOTEL = {"name": "Ibis Bencoolen", "city": "Singapore",
                   "country": "Singapore", "price_per_night_sgd": 165.0,
                   "rating": 4.1}
JAPAN_HOTEL = {"name": "Tokyo Inn", "city": "Tokyo", "country": "Japan",
               "price_per_night_sgd": 210.0, "rating": 4.4}


class SaveAndQuery(unittest.TestCase):
    def setUp(self):
        self.manager = DataManager(MemoryStorage())

    def test_nothing_saved_yet(self):
        self.assertEqual(self.manager.load(), [])
        self.assertEqual(self.manager.query("amy@mail.com"), [])

    def test_saved_search_can_be_queried(self):
        self.assertTrue(self.manager.save({"amy@mail.com": [SINGAPORE_HOTEL]}))

        records = self.manager.query("amy@mail.com")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["email"], "amy@mail.com")
        self.assertEqual(len(records[0]["searches"]), 1)
        self.assertEqual(records[0]["searches"][0][0]["name"],
                         "Ibis Bencoolen")

    def test_email_ignores_case_and_spaces(self):
        self.manager.save({" Amy@Mail.com ": [SINGAPORE_HOTEL]})
        self.manager.save({"amy@mail.com": [JAPAN_HOTEL]})

        records = self.manager.query("AMY@mail.com")

        self.assertEqual(len(self.manager.load()), 1)
        self.assertEqual(len(records[0]["searches"]), 2)

    def test_load_returns_every_user(self):
        self.manager.save({"amy@mail.com": [SINGAPORE_HOTEL]})
        self.manager.save({"ben@mail.com": [JAPAN_HOTEL]})

        emails = sorted(record["email"] for record in self.manager.load())

        self.assertEqual(emails, ["amy@mail.com", "ben@mail.com"])

    def test_missing_fields_get_defaults(self):
        self.manager.save({"amy@mail.com": [{"name": "Bare Hotel"}]})

        hotel = self.manager.query("amy@mail.com")[0]["searches"][0][0]

        self.assertEqual(hotel["country"], "Unknown")
        self.assertEqual(hotel["rating"], "N/A")
        self.assertEqual(hotel["amenities"], [])

    def test_hotels_without_a_name_are_not_kept(self):
        self.manager.save({"amy@mail.com": [SINGAPORE_HOTEL, {"name": " "},
                                            "not a hotel"]})

        hotels = self.manager.query("amy@mail.com")[0]["searches"][0]

        self.assertEqual(len(hotels), 1)


class QueryByCountry(unittest.TestCase):
    def setUp(self):
        self.manager = DataManager(MemoryStorage())
        self.manager.save({"amy@mail.com": [SINGAPORE_HOTEL, JAPAN_HOTEL]})
        self.manager.save({"amy@mail.com": [JAPAN_HOTEL]})

    def test_part_of_the_country_name_is_enough(self):
        records = self.manager.query_by_country("amy@mail.com", "singa")

        self.assertEqual(len(records[0]["searches"]), 1)
        self.assertEqual(records[0]["searches"][0][0]["country"], "Singapore")

    def test_country_ignores_case(self):
        records = self.manager.query_by_country("amy@mail.com", "JAPAN")

        self.assertEqual(len(records[0]["searches"]), 2)

    def test_no_match_returns_empty_list(self):
        self.assertEqual(
            self.manager.query_by_country("amy@mail.com", "France"), [])
        self.assertEqual(
            self.manager.query_by_country("ben@mail.com", "Japan"), [])
        self.assertEqual(self.manager.query_by_country("amy@mail.com", ""), [])


class JsonFile(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, "records.json")

    def test_records_are_still_there_after_reopening(self):
        DataManager(JsonStorage(self.path)).save(
            {"amy@mail.com": [SINGAPORE_HOTEL]})

        records = DataManager(JsonStorage(self.path)).query("amy@mail.com")

        self.assertEqual(records[0]["searches"][0][0]["name"],
                         "Ibis Bencoolen")

    def test_missing_file_is_an_empty_store(self):
        self.assertEqual(DataManager(JsonStorage(self.path)).load(), [])

    def test_empty_or_corrupt_file_is_an_empty_store(self):
        for content in ("", "{not json", "[1, 2, 3]"):
            with open(self.path, "w", encoding="utf-8") as file:
                file.write(content)
            self.assertEqual(DataManager(JsonStorage(self.path)).load(), [],
                             repr(content))

    def test_save_reports_failure_when_file_cannot_be_written(self):
        bad_path = os.path.join(self.path, "no_such_folder", "records.json")

        saved = DataManager(JsonStorage(bad_path)).save(
            {"amy@mail.com": [SINGAPORE_HOTEL]})

        self.assertFalse(saved)


if __name__ == "__main__":
    unittest.main()
