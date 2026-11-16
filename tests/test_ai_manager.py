"""Tests for the AI Manager (run from the repo root:
python -m unittest discover -s tests -p "test_ai_manager.py" -v).

No test calls the real Gemini API: a fake provider returns prepared text.
"""

import copy
import json
import unittest

from ai_managerpart2.ai_factory import AIManagerFactory
from ai_managerpart2.ai_logger import AILogger
from ai_managerpart2.ai_provider import AIProvider
from ai_managerpart2.ai_response_parser import AIResponseParser
from ai_managerpart2.base_ai_provider import BaseAIProvider
from ai_managerpart2.fatal_provider_error import FatalProviderError
from ai_managerpart2.hotel_prompt_builder import HotelPromptBuilder
from ai_managerpart2.hotel_response_validator import HotelResponseValidator
from ai_managerpart2.recoverable_provider_error import RecoverableProviderError

TARGET = "Bugis MRT Station"
RECORD = {"destination": "Singapore", "budget_min": 100, "budget_max": 300,
          "email_address": "amy@mail.com", "preferences": "near Bugis MRT"}


def make_hotel(number):
    return {
        "name": "Hotel %d" % number,
        "city": "Singapore",
        "country": "Singapore",
        "price_per_night_sgd": 150 + number,
        "rating": 4.2,
        "amenities": ["Free Wi-Fi"],
        "distance_to_preferences": [{"target": TARGET, "distance_m": 400}],
        "nearby_food": ["Food Court"],
        "nearby_activities": [{"name": "Bugis Junction", "distance_m": 300}],
    }


def make_response(hotel_count=10):
    """A response that passes validation when hotel_count is 10."""
    return {
        "proximity_preference": {"specified": True, "preferences": [TARGET]},
        "hotels": [make_hotel(number) for number in range(hotel_count)],
    }


VALID_TEXT = json.dumps(make_response())
INVALID_TEXT = json.dumps(make_response(hotel_count=3))


class MemoryLogger(AILogger):
    """Keeps the messages in lists instead of writing to the log file."""

    def __init__(self):
        self.warnings = []
        self.errors = []

    def warning(self, message, *args):
        self.warnings.append(message % args)

    def error(self, message, *args):
        self.errors.append(message % args)


class FakeProvider(AIProvider):
    """Returns prepared answers one by one, instead of calling Gemini."""

    def __init__(self, answers):
        self.__answers = list(answers)
        self.prompts = []

    @property
    def name(self):
        return "Fake"

    def call_api(self, prompt):
        self.prompts.append(prompt)
        return self.__answers.pop(0)


class FakeModels(BaseAIProvider):
    """A provider whose models behave as told: text is returned, an
    exception is raised."""

    def __init__(self, logger, behaviours):
        super().__init__(logger, behaviours.keys())
        self.__behaviours = behaviours
        self.models_tried = []

    @property
    def name(self):
        return "Fake"

    def _generate(self, model, prompt):
        self.models_tried.append(model)
        behaviour = self.__behaviours[model]
        if isinstance(behaviour, Exception):
            raise behaviour
        return behaviour


class GenerateCandidates(unittest.TestCase):
    def run_manager(self, answers):
        self.provider = FakeProvider(answers)
        self.logger = MemoryLogger()
        manager = AIManagerFactory.create_hotel_manager(
            self.provider, self.logger)
        return manager.generate_candidates(RECORD)

    def test_valid_first_response_is_returned(self):
        result = self.run_manager([VALID_TEXT])

        self.assertEqual(result, make_response())
        self.assertEqual(len(self.provider.prompts), 1)
        self.assertEqual(self.logger.errors, [])

    def test_invalid_response_gets_one_correction_attempt(self):
        result = self.run_manager([INVALID_TEXT, VALID_TEXT])

        self.assertEqual(result, make_response())
        self.assertEqual(len(self.provider.prompts), 2)
        # The correction prompt shows the AI its own invalid answer.
        self.assertIn(INVALID_TEXT, self.provider.prompts[1])
        self.assertEqual(len(self.logger.warnings), 1)

    def test_still_invalid_after_correction_gives_none(self):
        result = self.run_manager([INVALID_TEXT, "not json at all"])

        self.assertIsNone(result)
        self.assertEqual(len(self.provider.prompts), 2)
        self.assertEqual(len(self.logger.errors), 1)

    def test_no_response_gives_none_without_a_correction_attempt(self):
        result = self.run_manager([None])

        self.assertIsNone(result)
        self.assertEqual(len(self.provider.prompts), 1)
        self.assertEqual(len(self.logger.errors), 1)

    def test_no_response_during_correction_gives_none(self):
        result = self.run_manager([INVALID_TEXT, None])

        self.assertIsNone(result)
        self.assertEqual(len(self.provider.prompts), 2)


class ModelFallback(unittest.TestCase):
    def setUp(self):
        self.logger = MemoryLogger()

    def call(self, behaviours):
        self.provider = FakeModels(self.logger, behaviours)
        return self.provider.call_api("prompt")

    def test_first_model_answers(self):
        self.assertEqual(self.call({"first": "hello", "second": "unused"}),
                         "hello")
        self.assertEqual(self.provider.models_tried, ["first"])

    def test_next_model_is_tried_after_a_recoverable_error(self):
        answer = self.call({"first": RecoverableProviderError("429"),
                            "second": "hello"})

        self.assertEqual(answer, "hello")
        self.assertEqual(self.provider.models_tried, ["first", "second"])
        self.assertEqual(len(self.logger.warnings), 1)

    def test_next_model_is_tried_after_an_empty_response(self):
        self.assertEqual(self.call({"first": "", "second": "hello"}), "hello")

    def test_fatal_error_stops_without_trying_other_models(self):
        answer = self.call({"first": FatalProviderError("bad API key"),
                            "second": "hello"})

        self.assertIsNone(answer)
        self.assertEqual(self.provider.models_tried, ["first"])

    def test_unexpected_error_is_not_raised_to_the_caller(self):
        self.assertIsNone(self.call({"first": RuntimeError("boom"),
                                     "second": "hello"}))
        self.assertEqual(len(self.logger.errors), 1)

    def test_all_models_failing_gives_none(self):
        answer = self.call({"first": RecoverableProviderError("500"),
                            "second": RecoverableProviderError("503")})

        self.assertIsNone(answer)
        self.assertEqual(self.provider.models_tried, ["first", "second"])

    def test_at_least_one_model_is_required(self):
        with self.assertRaises(ValueError):
            FakeModels(self.logger, {})


class ResponseParsing(unittest.TestCase):
    def setUp(self):
        self.parser = AIResponseParser()

    def test_plain_json(self):
        self.assertEqual(self.parser.parse_response('{"hotels": []}'),
                         {"hotels": []})

    def test_json_inside_code_fences(self):
        text = '```json\n{"hotels": []}\n```'

        self.assertEqual(self.parser.parse_response(text), {"hotels": []})

    def test_json_with_commentary_around_it(self):
        text = 'Here you go:\n{"hotels": []}\nHope that helps!'

        self.assertEqual(self.parser.parse_response(text), {"hotels": []})

    def test_text_that_cannot_be_parsed_gives_none(self):
        for text in (None, 123, "", "   ", "no json here", '{"hotels": ',
                     "[1, 2, 3]"):
            self.assertIsNone(self.parser.parse_response(text), repr(text))


class ResponseValidation(unittest.TestCase):
    def setUp(self):
        self.validator = HotelResponseValidator()
        self.response = make_response()

    def assert_invalid(self, expected_text):
        errors = self.validator.find_errors(self.response)

        self.assertFalse(self.validator.validate_response(self.response))
        self.assertTrue(
            any(expected_text in error for error in errors), errors)

    def test_correct_response_has_no_errors(self):
        self.assertEqual(self.validator.find_errors(self.response), [])
        self.assertTrue(self.validator.validate_response(self.response))

    def test_no_proximity_preference_is_also_valid(self):
        self.response["proximity_preference"] = {"specified": False,
                                                 "preferences": []}
        for hotel in self.response["hotels"]:
            hotel["distance_to_preferences"] = []

        self.assertEqual(self.validator.find_errors(self.response), [])

    def test_response_must_be_a_dict(self):
        for response in (None, "text", []):
            self.assertFalse(self.validator.validate_response(response))

    def test_wrong_number_of_hotels(self):
        self.response["hotels"].pop()

        self.assert_invalid("Expected exactly 10 hotels, got 9.")

    def test_hotels_must_be_a_list(self):
        self.response["hotels"] = "none"

        self.assert_invalid("'hotels' must be a list.")

    def test_missing_hotel_field(self):
        del self.response["hotels"][0]["rating"]

        self.assert_invalid("hotels[0] is missing required fields.")

    def test_duplicate_hotel_name(self):
        self.response["hotels"][1]["name"] = " hotel 0 "

        self.assert_invalid("hotels[1].name is a duplicate.")

    def test_price_must_be_a_positive_number(self):
        for price in (0, -5, "150", None, True):
            self.response = make_response()
            self.response["hotels"][2]["price_per_night_sgd"] = price
            self.assert_invalid("hotels[2].price_per_night_sgd")

    def test_rating_must_be_0_to_5_or_missing(self):
        self.response["hotels"][0]["rating"] = None
        self.assertEqual(self.validator.find_errors(self.response), [])

        self.response["hotels"][0]["rating"] = 5.5
        self.assert_invalid("hotels[0].rating")

    def test_specified_must_match_the_preferences(self):
        self.response["proximity_preference"] = {"specified": True,
                                                 "preferences": []}

        self.assert_invalid("'specified' cannot be true")

    def test_distances_must_cover_the_requested_places(self):
        self.response["hotels"][0]["distance_to_preferences"] = [
            {"target": "Somewhere Else", "distance_m": 100}]

        self.assert_invalid("do not match the proximity preferences")

    def test_distance_cannot_be_negative(self):
        self.response["hotels"][0]["distance_to_preferences"][0][
            "distance_m"] = -1

        self.assert_invalid("invalid distance value")

    def test_validating_does_not_change_the_response(self):
        before = copy.deepcopy(self.response)

        self.validator.find_errors(self.response)

        self.assertEqual(self.response, before)


class Prompts(unittest.TestCase):
    def setUp(self):
        self.builder = HotelPromptBuilder()

    def test_prompt_contains_the_search_details(self):
        prompt = self.builder.build_prompt(RECORD)

        self.assertIn("Destination: Singapore", prompt)
        self.assertIn("100 to 300", prompt)
        self.assertIn("Preferences: near Bugis MRT", prompt)

    def test_prompt_says_so_when_there_are_no_preferences(self):
        for preferences in ("", "   ", None):
            prompt = self.builder.build_prompt(
                dict(RECORD, preferences=preferences))
            self.assertIn("Preferences: No additional preferences.", prompt)

    def test_correction_prompt_repeats_the_prompt_and_the_bad_answer(self):
        prompt = self.builder.build_correction_prompt(
            "ORIGINAL PROMPT", "BAD ANSWER")

        self.assertIn("ORIGINAL PROMPT", prompt)
        self.assertIn("BAD ANSWER", prompt)
        self.assertIn("CORRECTION", prompt)


if __name__ == "__main__":
    unittest.main()