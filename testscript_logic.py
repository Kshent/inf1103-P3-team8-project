
import copy
import json
from pathlib import Path
import logic_manager as LogicManager


# =====================================================
# HARDCODED SAMPLE AI DATA
# =====================================================

TARGET = "Singapore Institute of Technology"

user_input = {
    "destination": "Singapore",
    "budget_min": 200,
    "budget_max": 500,
    "email_address": "test@example.com",
    "preferences": "Near SIT, swimming pool"
}


def make_hotel(name, price, rating, distance, amenities=None):

    return {
        "name": name,
        "city": "Singapore",
        "country": "Singapore",
        "price_per_night_sgd": price,
        "rating": rating,
        "amenities": (
            amenities if amenities is not None
            else ["Swimming pool"]
        ),
        "distance_to_preferences": [
            {
                "target": TARGET,
                "distance_m": distance
            }
        ],
        "nearby_food": ["Test Restaurant"],
        "nearby_activities": [
            {
                "name": "Test Attraction",
                "distance_m": 300
            }
        ]
    }


hotels = [
    make_hotel("Hotel A", 250, 4.8, 150),
    make_hotel("Hotel B", 300, 4.2, 900, ["Gym"]),
    make_hotel("Hotel C", 600, 4.9, 100),
    make_hotel("Hotel D", 280, 3.2, 100),
    make_hotel("Hotel E", 260, 4.5, 2600)
]


ai_output = {
    "proximity_preference": {
        "specified": True,
        "preferences": [TARGET]
    },
    "hotels": hotels
}


# =====================================================
# TEST 1: BUILD REQUIREMENTS
# =====================================================

def test_build_requirements():

    requirements = LogicManager.build_requirements(
        ai_output, user_input
    )

    assert requirements["targets"] == [TARGET]
    assert "swimming pool" in requirements["pref_checks"]
    assert sum(requirements["maxima"].values()) == 90


# =====================================================
# TEST 2: VALIDATE HOTELS
# =====================================================

def test_validate_hotels():

    test_data = copy.deepcopy(ai_output)

    # Add duplicate hotel
    test_data["hotels"].append(
        make_hotel("Hotel A", 250, 4.8, 150)
    )

    # Add hotel with invalid price
    test_data["hotels"].append(
        make_hotel("Invalid Hotel", 0, 4.0, 100)
    )

    valid = LogicManager.validate_hotels(test_data)

    assert len(valid) == 5
    assert len(set(h["name"] for h in valid)) == 5


# =====================================================
# TEST 3: FILTER HOTELS
# =====================================================

def test_filter_hotels():

    requirements = LogicManager.build_requirements(
        ai_output, user_input
    )

    valid = LogicManager.validate_hotels(ai_output)

    kept, rejected = LogicManager.filter_hotels(
        valid, requirements
    )

    assert len(kept) == 2
    assert len(rejected) == 3

    assert [h["name"] for h in kept] == [
        "Hotel A",
        "Hotel B"
    ]

    assert {h["name"] for h in rejected} == {
        "Hotel C",
        "Hotel D",
        "Hotel E"
    }


# =====================================================
# TEST 4: CALCULATE SCORE
# =====================================================

def test_calculate_score():

    requirements = LogicManager.build_requirements(
        ai_output, user_input
    )

    scored = LogicManager.calculate_score(
        hotels[0], requirements
    )

    # Same floating-point arithmetic and rounding
    # currently used by Logic Manager
    rating = hotels[0]["rating"]

    rating_share = (rating - 3.0) / (5.0 - 3.0)
    expected_rating_points = int(rating_share * 25 + 0.5)

    expected_score = (
        expected_rating_points
        + 20  # Price
        + 25  # Location
        + 20  # Preferences
        + 10  # Bonus
    )

    assert scored["score"] == expected_score
    assert scored["score_max"] == 100

    assert sum(
        item["points"] for item in scored["breakdown"]
    ) == scored["score"]


# =====================================================
# TEST 5: MULTI-CONDITION BONUS
# =====================================================

def test_bonus_points():

    requirements = LogicManager.build_requirements(
        ai_output, user_input
    )

    good = LogicManager.calculate_score(
        hotels[0], requirements
    )

    bad = LogicManager.calculate_score(
        hotels[1], requirements
    )

    good_bonus = next(
        item["points"]
        for item in good["breakdown"]
        if item["key"] == "bonus"
    )

    bad_bonus = next(
        item["points"]
        for item in bad["breakdown"]
        if item["key"] == "bonus"
    )

    assert good_bonus == 10
    assert bad_bonus == 0


# =====================================================
# TEST 6: RANK HOTELS
# =====================================================

def test_rank_hotels():

    sample = [
        {
            "name": "A",
            "score": 70,
            "rating": 4.0,
            "price_per_night_sgd": 200
        },
        {
            "name": "B",
            "score": 90,
            "rating": 4.5,
            "price_per_night_sgd": 300
        },
        {
            "name": "C",
            "score": 80,
            "rating": 4.2,
            "price_per_night_sgd": 250
        }
    ]

    ranked = LogicManager.rank_hotels(sample)

    assert [h["name"] for h in ranked] == [
        "B",
        "C",
        "A"
    ]


# =====================================================
# TEST 7: GET TOP THREE
# =====================================================

def test_get_top_three():

    ranked = [
        {"name": "Hotel A"},
        {"name": "Hotel B"},
        {"name": "Hotel C"},
        {"name": "Hotel D"}
    ]

    top = LogicManager.get_top_three(ranked)

    assert len(top) == 3

    assert [h["rank"] for h in top] == [
        1, 2, 3
    ]

    assert [h["name"] for h in top] == [
        "Hotel A",
        "Hotel B",
        "Hotel C"
    ]


# =====================================================
# TEST 8: COMPLETE LOGIC PROCESS
# =====================================================

def test_process_hotels():

    result = LogicManager.process_hotels(
        ai_output, user_input
    )

    assert result["summary"]["received"] == 5
    assert result["summary"]["rejected"] == 3
    assert result["summary"]["returned"] == 2

    assert [
        h["name"] for h in result["top_hotels"]
    ] == ["Hotel A", "Hotel B"]


# =====================================================
# TEST 9: ALL HOTELS REJECTED
# =====================================================

def test_all_rejected():

    test_data = copy.deepcopy(ai_output)

    test_data["hotels"] = copy.deepcopy(hotels[2:])

    result = LogicManager.process_hotels(
        test_data, user_input
    )

    assert result["top_hotels"] == []
    assert result["summary"]["rejected"] == 3
    assert result["summary"]["returned"] == 0


# =====================================================
# RUN ALL TEST FUNCTIONS
# =====================================================

def run_all_tests():

    tests = [
        test_build_requirements,
        test_validate_hotels,
        test_filter_hotels,
        test_calculate_score,
        test_bonus_points,
        test_rank_hotels,
        test_get_top_three,
        test_process_hotels,
        test_all_rejected
    ]

    results = []
    passed = 0
    failed = 0

    for test in tests:

        try:
            test()

            passed += 1

            results.append({
                "test_name": test.__name__,
                "status": "PASSED",
                "error": None
            })

        except Exception as error:

            failed += 1

            results.append({
                "test_name": test.__name__,
                "status": "FAILED",
                "error": (
                    f"{type(error).__name__}: {error}"
                )
            })

    report = {
        "total_tests": len(tests),
        "passed": passed,
        "failed": failed,
        "overall_status": (
            "PASSED" if failed == 0 else "FAILED"
        ),
        "test_results": results
    }

    output_file = (
        Path("/data") / "logic_test_results.json"
    )

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    return failed == 0


# =====================================================
# EXECUTE TEST SCRIPT
# =====================================================

if __name__ == "__main__":

    success = run_all_tests()

    if not success:
        raise SystemExit(1)
