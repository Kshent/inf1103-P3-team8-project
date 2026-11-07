"""Smoke tests for the io_manager package (run: python -m unittest -v)."""

import ast
import pathlib
import unittest

import io_manager
from io_manager import (ConsoleView, EmailValidator, InputReader,
                        InputValidator, LocationValidator, PriceRangeValidator)

PACKAGE_DIR = pathlib.Path(io_manager.__file__).parent


def make_view(answers):
    """A ConsoleView fed from a list of answers; returns (view, prompts, output)."""
    remaining = list(answers)
    prompts, output = [], []

    def fake_input(prompt):
        prompts.append(prompt)
        if not remaining:
            raise EOFError
        return remaining.pop(0)

    return ConsoleView(fake_input, output.append), prompts, output


class PackageStructure(unittest.TestCase):
    def test_public_classes_are_exported(self):
        for name in ("InputValidator", "LocationValidator", "PriceRangeValidator",
                     "EmailValidator", "InputReader", "ConsoleView"):
            self.assertTrue(hasattr(io_manager, name), name)

    def test_one_class_per_file(self):
        for path in PACKAGE_DIR.glob("*.py"):
            if path.name == "__init__.py":
                continue
            classes = [n for n in ast.parse(path.read_text()).body
                       if isinstance(n, ast.ClassDef)]
            self.assertEqual(len(classes), 1, path.name)

    def test_validators_share_one_interface(self):
        for cls in (LocationValidator, PriceRangeValidator, EmailValidator):
            self.assertTrue(issubclass(cls, InputValidator))


class Validators(unittest.TestCase):
    def test_location(self):
        self.assertEqual(LocationValidator().validate("Singapore"), (True, ""))
        self.assertFalse(LocationValidator().validate("")[0])
        self.assertFalse(LocationValidator().validate("Atlantis")[0])

    def test_price_range(self):
        ok, _, value = PriceRangeValidator().validate("SGD 100-SGD 250")
        self.assertTrue(ok)
        self.assertEqual(value, {"min": 100.0, "max": 250.0, "currency": "SGD"})
        for bad in ("", "abc", "250-100", "0-5"):
            self.assertFalse(PriceRangeValidator().validate(bad)[0], bad)

    def test_email(self):
        self.assertEqual(EmailValidator().validate("a@b.com"), (True, ""))
        self.assertFalse(EmailValidator().validate("nope")[0])


class Reader(unittest.TestCase):
    def test_cancellation_raises_eof_with_message(self):
        def cancel(_prompt):
            raise KeyboardInterrupt
        with self.assertRaises(EOFError) as caught:
            InputReader(cancel).read("x")
        self.assertIn("Input cancelled. Goodbye.", str(caught.exception))


class View(unittest.TestCase):
    def test_mandatory_inputs_retry_until_valid(self):
        view, prompts, output = make_view(
            ["Atlantis", "Singapore", "abc", "100-250", "nope", "a@b.com"])
        data = view.request_mandatory_inputs()
        self.assertEqual(data["location"], "Singapore")
        self.assertEqual(data["price_range"]["max"], 250.0)
        self.assertEqual(data["email_address"], "a@b.com")
        self.assertEqual(sum(1 for line in output if str(line).startswith("Error:")), 3)

    def test_preferences_optional_and_limited(self):
        self.assertEqual(make_view([""])[0].request_user_preferences(), "")
        view, _, output = make_view(["x" * 2001, "quiet"])
        self.assertEqual(view.request_user_preferences(), "quiet")
        self.assertIn("Error: Preferences must not exceed 2,000 characters.", output)

    def test_menu_rejects_bad_choices(self):
        view, _, output = make_view(["9", "", "3"])
        self.assertEqual(view.show_main_menu(), "3")
        self.assertEqual(output.count("Invalid option. Please enter 1, 2, 3 or 4"), 2)

    def test_record_email_q_returns_none(self):
        self.assertIsNone(make_view(["q"])[0].request_record_email())
        self.assertEqual(make_view(["bad", "A@B.com"])[0].request_record_email(), "a@b.com")

    def test_admin_login(self):
        self.assertTrue(make_view(["bob", "team8", "x", "12345"])[0].admin_login("team8", "12345"))
        self.assertFalse(make_view(["q"])[0].admin_login("team8", "12345"))

    def test_display_records(self):
        view, _, output = make_view([])
        view.display_records([])
        self.assertEqual(output, ["\nNo records found."])
        hotel = {"name": "H", "city": "C", "country": "K", "price_per_night_sgd": 100,
                 "rating": 4.5, "amenities": ["Gym"], "nearby_food": ["Cafe"],
                 "nearby_activities": [{"name": "Museum", "distance_m": 400}]}
        view, _, output = make_view([])
        view.display_records([{"email": "a@b.com", "searches": [[hotel]]}])
        self.assertIn("\nEmail: a@b.com", output)
        self.assertIn("     Nearby activities: Museum (400 m)", output)


if __name__ == "__main__":
    unittest.main()
