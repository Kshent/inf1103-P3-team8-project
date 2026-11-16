import copy
import unittest
from logic_manager_part2 import LogicManager
from logic_manager_part2.profile_factory import ProfileFactory

TARGET = "Bugis MRT Station"


def make_hotel(name, price, rating, distance, amenities=("Free Wi-Fi",)):
    """One hotel in the shape the AI Manager returns."""
    return {
        "name": name,
        "city": "Singapore",
        "country": "Singapore",
        "price_per_night_sgd": price,
        "rating": rating,
        "amenities": list(amenities),
        "distance_to_preferences": [{"target": TARGET,
                                     "distance_m": distance}],
        "nearby_food": ["Food Court"],
        "nearby_activities": [{"name": "Bugis Junction", "distance_m": 100}],
    }


def make_ai_output(hotels):
    return {
        "proximity_preference": {"specified": True, "preferences": [TARGET]},
        "hotels": hotels,
    }


def make_record(profile="balanced", weights=None):
    """The user's search details in the shape app.py builds."""
    return {
        "destination": "Singapore",
        "budget_min": 100,
        "budget_max": 300,
        "email_address": "amy@mail.com",
        "preferences": "near Bugis MRT Station, swimming pool",
        "priority_profile": {"name": profile, "weights": weights},
    }

# Four hotels that pass every rule, then one that breaks each rule.
GOOD_HOTELS = [
    make_hotel("Great", 180, 4.7, 150, ("Swimming Pool", "Free Wi-Fi")),
    make_hotel("Good", 200, 4.2, 600),
    make_hotel("Okay", 280, 3.8, 1500),
    make_hotel("Fine", 150, 4.1, 900),
]
TOO_EXPENSIVE = make_hotel("Pricey", 450, 4.8, 100)
BADLY_RATED = make_hotel("Bad", 150, 3.0, 100)
TOO_FAR = make_hotel("Far", 150, 4.5, 5000)


def names(hotels):
    return [hotel["name"] for hotel in hotels]


class TopThree(unittest.TestCase):
    def setUp(self):
        self.result = LogicManager().process_hotels(
            make_ai_output(GOOD_HOTELS), make_record())
        self.top = self.result["top_hotels"]

    def test_at_most_three_hotels_are_returned(self):
        self.assertEqual(len(self.top), 3)

    def test_fewer_than_three_hotels_is_allowed(self):
        result = LogicManager().process_hotels(
            make_ai_output(GOOD_HOTELS[:2]), make_record())

        self.assertEqual(len(result["top_hotels"]), 2)

    def test_best_score_comes_first(self):
        scores = [hotel["score"] for hotel in self.top]

        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(self.top[0]["name"], "Great")
        self.assertEqual([hotel["rank"] for hotel in self.top], [1, 2, 3])

    def test_breakdown_adds_up_exactly_to_the_score(self):
        for hotel in self.top:
            points = sum(line["points"] for line in hotel["breakdown"])
            self.assertEqual(points, hotel["score"], hotel["name"])

    def test_score_is_out_of_100(self):
        for hotel in self.top:
            self.assertEqual(hotel["score_max"], 100)
            self.assertTrue(0 <= hotel["score"] <= 100, hotel["name"])

    def test_every_breakdown_line_has_a_reason(self):
        for hotel in self.top:
            for line in hotel["breakdown"]:
                self.assertTrue(line["reason"].strip(), line["key"])
                self.assertTrue(0 <= line["points"] <= line["max"],
                                line["key"])

    def test_summary_counts(self):
        self.assertEqual(self.result["summary"], {
            "received": 4, "valid": 4, "rejected": 0, "returned": 3})

    def test_requirements_show_what_was_understood(self):
        requirements = self.result["requirements"]

        self.assertEqual(requirements["budget_max"], 300)
        self.assertEqual(requirements["targets"], [TARGET])
        self.assertIn("swimming pool", requirements["pref_checks"])


class MandatoryRules(unittest.TestCase):
    def process(self, *extra_hotels):
        return LogicManager().process_hotels(
            make_ai_output(GOOD_HOTELS + list(extra_hotels)), make_record())

    def reason_for(self, hotel):
        rejected = self.process(hotel)["rejected_hotels"]
        self.assertEqual(names(rejected), [hotel["name"]])
        return rejected[0]["reject_reason"]

    def test_hotel_above_the_budget_is_rejected(self):
        self.assertIn("above your maximum budget",
                      self.reason_for(TOO_EXPENSIVE))

    def test_hotel_with_a_low_rating_is_rejected(self):
        self.assertIn("below the minimum", self.reason_for(BADLY_RATED))

    def test_hotel_too_far_away_is_rejected(self):
        self.assertIn("too far", self.reason_for(TOO_FAR))

    def test_rejected_hotels_never_reach_the_top_three(self):
        result = self.process(TOO_EXPENSIVE, BADLY_RATED, TOO_FAR)

        self.assertEqual(result["summary"]["rejected"], 3)
        for name in ("Pricey", "Bad", "Far"):
            self.assertNotIn(name, names(result["top_hotels"]))

    def test_all_hotels_rejected_gives_an_empty_top_three(self):
        result = LogicManager().process_hotels(
            make_ai_output([TOO_EXPENSIVE, BADLY_RATED, TOO_FAR]),
            make_record())

        self.assertEqual(result["top_hotels"], [])
        self.assertEqual(result["summary"]["returned"], 0)


class BadAiData(unittest.TestCase):
    def test_unusable_and_duplicate_hotels_are_dropped(self):
        hotels = GOOD_HOTELS + [
            make_hotel("great", 180, 4.7, 150),         # same name again
            {"name": "", "price_per_night_sgd": 100},   # no name
            make_hotel("No Price", None, 4.5, 100),     # no usable price
            "not a hotel",
        ]

        summary = LogicManager().process_hotels(
            make_ai_output(hotels), make_record())["summary"]

        self.assertEqual(summary["received"], 8)
        self.assertEqual(summary["valid"], 4)

    def test_missing_rating_is_flagged_not_rejected(self):
        result = LogicManager().process_hotels(
            make_ai_output([make_hotel("No Rating", 180, None, 150)]),
            make_record())

        hotel = result["top_hotels"][0]
        self.assertEqual(hotel["outcome"], "flagged")
        self.assertIn("rating_missing", hotel["flags"])

    def test_ai_output_that_is_not_a_dict_gives_an_empty_result(self):
        for ai_output in (None, "text", [], {"hotels": "none"}):
            result = LogicManager().process_hotels(ai_output, make_record())
            self.assertEqual(result["top_hotels"], [], repr(ai_output))
            self.assertEqual(result["summary"]["received"], 0)

    def test_input_is_not_changed(self):
        ai_output = make_ai_output(GOOD_HOTELS + [TOO_EXPENSIVE])
        record = make_record()
        ai_before = copy.deepcopy(ai_output)
        record_before = copy.deepcopy(record)

        LogicManager().process_hotels(ai_output, record)

        self.assertEqual(ai_output, ai_before)
        self.assertEqual(record, record_before)


class TravellerProfiles(unittest.TestCase):
    CHEAP_BUT_AVERAGE = make_hotel("Cheap", 110, 3.9, 300)
    DEAR_BUT_EXCELLENT = make_hotel("Dear", 290, 4.9, 300)

    def winner(self, profile, weights=None):
        result = LogicManager().process_hotels(
            make_ai_output([self.CHEAP_BUT_AVERAGE, self.DEAR_BUT_EXCELLENT]),
            make_record(profile, weights))
        return result["top_hotels"][0]["name"]

    def test_budget_profile_prefers_the_cheaper_hotel(self):
        self.assertEqual(self.winner("budget"), "Cheap")

    def test_quality_profile_prefers_the_better_rated_hotel(self):
        self.assertEqual(self.winner("quality_focused"), "Dear")

    def test_custom_weights_are_used(self):
        only_price = {"rating": 0, "price": 100, "location": 0,
                      "preferences": 0, "bonus": 0}
        only_rating = {"rating": 100, "price": 0, "location": 0,
                       "preferences": 0, "bonus": 0}

        self.assertEqual(self.winner("custom", only_price), "Cheap")
        self.assertEqual(self.winner("custom", only_rating), "Dear")

    def test_no_profile_means_balanced(self):
        record = make_record()
        without_profile = {key: value for key, value in record.items()
                           if key != "priority_profile"}
        ai_output = make_ai_output(GOOD_HOTELS)

        with_balanced = LogicManager().process_hotels(ai_output, record)
        with_none = LogicManager().process_hotels(ai_output, without_profile)

        self.assertEqual(with_none["top_hotels"], with_balanced["top_hotels"])


class Profiles(unittest.TestCase):
    def setUp(self):
        self.factory = ProfileFactory()

    def test_every_preset_adds_up_to_100(self):
        for style in ("balanced", "budget", "quality_focused"):
            profile = self.factory.resolve({"name": style, "weights": None})
            self.assertEqual(sum(profile["weights"].values()), 100, style)
            self.assertTrue(profile["label"], style)

    def test_valid_custom_weights_are_accepted(self):
        weights = {"rating": 30, "price": 30, "location": 20,
                   "preferences": 10, "bonus": 10}

        profile = self.factory.resolve({"name": "custom", "weights": weights})

        self.assertEqual(profile["weights"], weights)

    def test_custom_weights_must_add_up_to_100(self):
        weights = {"rating": 50, "price": 50, "location": 0,
                   "preferences": 0, "bonus": 10}

        with self.assertRaises(ValueError):
            self.factory.resolve({"name": "custom", "weights": weights})

    def test_custom_weights_need_all_five_criteria(self):
        with self.assertRaises(ValueError):
            self.factory.resolve({"name": "custom",
                                  "weights": {"rating": 100}})

    def test_custom_weights_must_be_whole_numbers_from_zero(self):
        for bad in (-10, 2.5, "10"):
            weights = {"rating": bad, "price": 100, "location": 0,
                       "preferences": 0, "bonus": 0}
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.factory.resolve({"name": "custom", "weights": weights})

    def test_unknown_profile_is_refused(self):
        for choice in ({"name": "luxury"}, "balanced", None):
            with self.assertRaises(ValueError, msg=repr(choice)):
                self.factory.resolve(choice)


if __name__ == "__main__":
    unittest.main()