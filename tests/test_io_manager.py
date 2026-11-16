"""Tests for the IO Manager (run from the repo root:
python -m unittest discover -s tests -p "test_io_manager.py" -v)."""

import unittest

from io_manager_part2 import (ConsoleView, CountrySearchValidator,
                              EmailValidator, InputReader, InputValidator,
                              LocationValidator, PriceRangeValidator,
                              WeightValidator)


def make_view(answers):
    """A ConsoleView that reads from a list of answers instead of the
    keyboard. Returns (view, prompts shown, lines printed)."""
    remaining = list(answers)
    prompts, output = [], []

    def fake_input(prompt):
        prompts.append(prompt)
        if not remaining:
            raise EOFError
        return remaining.pop(0)

    return ConsoleView(fake_input, output.append), prompts, output


class ValidatorInterface(unittest.TestCase):
    def test_every_validator_is_an_input_validator(self):
        for validator in (LocationValidator, PriceRangeValidator,
                          EmailValidator, WeightValidator,
                          CountrySearchValidator):
            self.assertTrue(issubclass(validator, InputValidator),
                            validator.__name__)

    def test_interface_cannot_be_created(self):
        with self.assertRaises(TypeError):
            InputValidator()


class LocationValidation(unittest.TestCase):
    def setUp(self):
        self.validator = LocationValidator()

    def test_real_country_and_city_are_accepted(self):
        self.assertEqual(self.validator.validate("Singapore"), (True, ""))
        self.assertEqual(self.validator.validate("  tokyo "), (True, ""))

    def test_empty_location_is_rejected(self):
        self.assertFalse(self.validator.validate("")[0])
        self.assertFalse(self.validator.validate("   ")[0])

    def test_unknown_place_is_rejected(self):
        is_valid, error = self.validator.validate("Qxzvland")

        self.assertFalse(is_valid)
        self.assertIn("not found", error)

    def test_numbers_and_symbols_are_rejected(self):
        self.assertFalse(self.validator.validate("12345")[0])
        self.assertFalse(self.validator.validate("Sing@pore")[0])


class PriceRangeValidation(unittest.TestCase):
    def setUp(self):
        self.validator = PriceRangeValidator()

    def test_simple_range(self):
        is_valid, error, price_range = self.validator.validate("100-250")

        self.assertTrue(is_valid)
        self.assertEqual(error, "")
        self.assertEqual(price_range,
                         {"min": 100.0, "max": 250.0, "currency": "SGD"})

    def test_currency_words_and_spaces_are_allowed(self):
        for text in ("SGD 100 - SGD 250", "$100 to $250", "100,250"):
            is_valid, _error, price_range = self.validator.validate(text)
            self.assertTrue(is_valid, text)
            self.assertEqual((price_range["min"], price_range["max"]),
                             (100.0, 250.0), text)

    def test_text_that_is_not_a_range_is_rejected(self):
        for text in ("", "abc", "100", "100-"):
            is_valid, _error, price_range = self.validator.validate(text)
            self.assertFalse(is_valid, text)
            self.assertIsNone(price_range)

    def test_minimum_above_maximum_is_rejected(self):
        is_valid, error, _price_range = self.validator.validate("300-100")

        self.assertFalse(is_valid)
        self.assertIn("minimum price", error)

    def test_zero_price_is_rejected(self):
        self.assertFalse(self.validator.validate("0-100")[0])


class EmailValidation(unittest.TestCase):
    def setUp(self):
        self.validator = EmailValidator()

    def test_valid_emails(self):
        for email in ("amy@mail.com", "amy.tan+hotels@sit.edu.sg"):
            self.assertEqual(self.validator.validate(email), (True, ""), email)

    def test_invalid_emails(self):
        for email in ("", "amy", "amy@", "amy@mail", "@mail.com",
                      "amy tan@mail.com"):
            self.assertFalse(self.validator.validate(email)[0], email)


class WeightValidation(unittest.TestCase):
    def test_whole_number_within_what_is_left(self):
        self.assertEqual(WeightValidator(100).validate("40"), (True, "", 40))
        self.assertEqual(WeightValidator(30).validate("30"), (True, "", 30))
        self.assertEqual(WeightValidator(30).validate("0"), (True, "", 0))

    def test_more_than_what_is_left_is_rejected(self):
        is_valid, error, points = WeightValidator(30).validate("31")

        self.assertFalse(is_valid)
        self.assertIn("30 point(s) left", error)
        self.assertIsNone(points)

    def test_anything_but_a_whole_number_is_rejected(self):
        for text in ("", "abc", "-5", "2.5", " 10"):
            self.assertFalse(WeightValidator(100).validate(text)[0], text)


class CountrySearchValidation(unittest.TestCase):
    def setUp(self):
        self.validator = CountrySearchValidator()

    def test_part_of_a_country_name_is_accepted(self):
        for text in ("singa", "Singapore", "United States", "Cote d'Ivoire"):
            self.assertEqual(self.validator.validate(text), (True, ""), text)

    def test_empty_short_or_non_letter_text_is_rejected(self):
        for text in ("", "  ", "s", "123", "sing@"):
            self.assertFalse(self.validator.validate(text)[0], text)


class Reader(unittest.TestCase):
    def test_spaces_around_the_answer_are_removed(self):
        reader = InputReader(lambda prompt: "  hello  ")

        self.assertEqual(reader.read("Say something: "), "hello")

    def test_cancelling_raises_eof_error_with_a_message(self):
        def cancelled(prompt):
            raise KeyboardInterrupt

        with self.assertRaises(EOFError) as raised:
            InputReader(cancelled).read("Say something: ")

        self.assertIn("Input cancelled", str(raised.exception))


class MainMenu(unittest.TestCase):
    def test_valid_choice_is_returned(self):
        view, _prompts, _output = make_view(["2"])

        self.assertEqual(view.show_main_menu(), "2")

    def test_invalid_choices_are_asked_again(self):
        view, prompts, output = make_view(["9", "abc", "", "4"])

        self.assertEqual(view.show_main_menu(), "4")
        self.assertEqual(len(prompts), 4)
        self.assertEqual(
            output.count("Invalid option. Please enter 1, 2, 3 or 4"), 3)


class SearchInputs(unittest.TestCase):
    def test_valid_inputs_are_returned(self):
        view, _prompts, _output = make_view(
            ["Singapore", "100-250", "amy@mail.com"])

        self.assertEqual(view.request_mandatory_inputs(), {
            "location": "Singapore",
            "price_range": {"min": 100.0, "max": 250.0, "currency": "SGD"},
            "email_address": "amy@mail.com",
        })

    def test_each_input_is_asked_again_until_valid(self):
        view, prompts, output = make_view(
            ["", "Singapore", "abc", "100-250", "not-an-email",
             "amy@mail.com"])

        inputs = view.request_mandatory_inputs()

        self.assertEqual(inputs["location"], "Singapore")
        self.assertEqual(inputs["email_address"], "amy@mail.com")
        self.assertEqual(len(prompts), 6)
        self.assertEqual(
            len([line for line in output if line.startswith("Error: ")]), 3)

    def test_preferences_can_be_left_blank(self):
        view, _prompts, _output = make_view([""])

        self.assertEqual(view.request_user_preferences(), "")

    def test_preferences_that_are_too_long_are_asked_again(self):
        view, prompts, _output = make_view(["x" * 2001, "near MRT, pool"])

        self.assertEqual(view.request_user_preferences(), "near MRT, pool")
        self.assertEqual(len(prompts), 2)


class RecordInputs(unittest.TestCase):
    def test_email_is_returned_in_lower_case(self):
        view, _prompts, _output = make_view(["Amy@Mail.com"])

        self.assertEqual(view.request_record_email(), "amy@mail.com")

    def test_q_leaves_the_email_question(self):
        view, _prompts, _output = make_view(["bad email", "Q"])

        self.assertIsNone(view.request_record_email())

    def test_view_option_is_asked_again_until_1_or_2(self):
        view, prompts, _output = make_view(["3", "1"])

        self.assertEqual(view.request_record_view_option(), "1")
        self.assertEqual(len(prompts), 2)

    def test_country_is_tidied_and_q_quits(self):
        view, _prompts, _output = make_view(["1", "  united   states "])
        self.assertEqual(view.request_record_country(), "united states")

        view, _prompts, _output = make_view(["q"])
        self.assertIsNone(view.request_record_country())


class AdminLogin(unittest.TestCase):
    def test_correct_username_and_password(self):
        view, _prompts, _output = make_view(["team8", "12345"])

        self.assertTrue(view.admin_login("team8", "12345"))

    def test_wrong_answers_are_asked_again(self):
        view, _prompts, output = make_view(
            ["someone", "team8", "wrong", "12345"])

        self.assertTrue(view.admin_login("team8", "12345"))
        self.assertIn("Wrong username", output)
        self.assertIn("Wrong password", output)

    def test_q_cancels_the_login(self):
        view, _prompts, _output = make_view(["q"])
        self.assertFalse(view.admin_login("team8", "12345"))

        view, _prompts, _output = make_view(["team8", "Q"])
        self.assertFalse(view.admin_login("team8", "12345"))


class RecordDisplay(unittest.TestCase):
    HOTEL = {"name": "Ibis Bencoolen", "city": "Singapore",
             "country": "Singapore", "price_per_night_sgd": 165.0,
             "rating": 4.1, "amenities": ["Free Wi-Fi", "Bar"],
             "nearby_food": ["Food Court"],
             "nearby_activities": [{"name": "Bugis Junction",
                                    "distance_m": 400}]}

    def test_no_records(self):
        view, _prompts, output = make_view([])

        view.display_records([])

        self.assertEqual(output, ["\nNo records found."])

    def test_records_show_email_search_number_and_hotel(self):
        view, _prompts, output = make_view([])

        view.display_records([{"email": "amy@mail.com",
                               "searches": [[self.HOTEL], [self.HOTEL]]}])
        text = "\n".join(output)

        self.assertIn("Email: amy@mail.com", text)
        self.assertIn("--- Search 1 ---", text)
        self.assertIn("--- Search 2 ---", text)
        self.assertIn("1. Ibis Bencoolen", text)
        self.assertIn("Amenities: Free Wi-Fi, Bar", text)
        self.assertIn("Nearby activities: Bugis Junction (400 m)", text)


if __name__ == "__main__":
    unittest.main()