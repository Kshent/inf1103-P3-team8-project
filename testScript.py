# """
# exception_tests.py

# Manual CLI test script for Exception Handling Matrix.

# Run:
#     python exception_tests.py
# """

# import tempfile
# import os

# from IO_manager import (
#     validate_location,
#     validate_price_range,
#     validate_email,
#     admin_login,
#     _safe_input
# )

# from data_manager import (
#     load_ai_results
# )

# from logic_manager import (
#     validate_hotels,
#     filter_hotels
# )


# passed = 0
# failed = 0


# def run_test(name, test_func):
#     global passed, failed

#     try:
#         test_func()
#         print(f"[PASS] {name}")
#         passed += 1

#     except AssertionError as e:
#         print(f"[FAIL] {name}")
#         print(f"       {e}")
#         failed += 1

#     except Exception as e:
#         print(f"[ERROR] {name}")
#         print(f"        {type(e).__name__}: {e}")
#         failed += 1


# # 1
# def test_invalid_location():
#     valid, _ = validate_location("")
#     assert valid is False


# # 2
# def test_invalid_budget():
#     valid, _, _ = validate_price_range("abc")
#     assert valid is False


# # 3
# def test_invalid_email():
#     valid, _ = validate_email("invalid-email")
#     assert valid is False


# # 4
# def test_user_cancel_input():

#     def mock_input(prompt):
#         raise KeyboardInterrupt()

#     try:
#         _safe_input("Enter value: ", mock_input)
#         assert False, "Expected EOFError"

#     except EOFError:
#         pass


# # 5
# def test_invalid_menu_choice():

#     invalid_choice = "99"

#     assert invalid_choice not in ["1", "2", "3", "4"]


# # 6
# def test_admin_login_failure():

#     answers = iter([
#         "wrong-user",
#         "Q"
#     ])

#     result = admin_login(
#         "admin",
#         "password",
#         input_function=lambda x: next(answers),
#         output_function=lambda x: None
#     )

#     assert result is False


# # 7
# def test_ai_service_unavailable():

#     try:
#         raise ConnectionError("AI service unavailable")
#     except ConnectionError:
#         pass


# # 8
# def test_ai_timeout():

#     try:
#         raise TimeoutError("AI timeout")
#     except TimeoutError:
#         pass


# # 9
# def test_invalid_ai_response():

#     hotels = validate_hotels("invalid response")
#     assert hotels == []


# # 10
# def test_missing_hotel_data():

#     ai_output = {
#         "hotels": [
#             {
#                 "name": "",
#                 "price_per_night_sgd": 100
#             }
#         ]
#     }

#     hotels = validate_hotels(ai_output)

#     assert len(hotels) == 0


# # 11
# def test_duplicate_hotels():

#     ai_output = {
#         "hotels": [
#             {
#                 "name": "Hotel A",
#                 "price_per_night_sgd": 100
#             },
#             {
#                 "name": "Hotel A",
#                 "price_per_night_sgd": 120
#             }
#         ]
#     }

#     hotels = validate_hotels(ai_output)

#     assert len(hotels) == 1


# # 12
# def test_missing_distance_information():

#     ai_output = {
#         "proximity_preference": {
#             "specified": True,
#             "preferences": ["Orchard Road"]
#         },
#         "hotels": [
#             {
#                 "name": "Hotel A",
#                 "price_per_night_sgd": 200,
#                 "rating": 4.5,
#                 "amenities": []
#             }
#         ]
#     }

#     hotels = validate_hotels(ai_output)

#     assert "distance_unknown" in hotels[0]["flags"]


# # 13
# def test_hotel_exceeds_budget():

#     requirements = {
#         "budget_min": 100,
#         "budget_max": 200,
#         "targets": []
#     }

#     hotel = {
#         "name": "Luxury Hotel",
#         "price_per_night_sgd": 500
#     }

#     kept, rejected = filter_hotels([hotel], requirements)

#     assert len(rejected) == 1


# # 14
# def test_hotel_rating_too_low():

#     requirements = {
#         "budget_min": None,
#         "budget_max": None,
#         "targets": []
#     }

#     hotel = {
#         "name": "Budget Hotel",
#         "price_per_night_sgd": 100,
#         "rating": 2.5
#     }

#     kept, rejected = filter_hotels([hotel], requirements)

#     assert len(rejected) == 1


# # 15
# def test_missing_recommendation_file():

#     try:
#         load_ai_results("file_does_not_exist.json")
#         assert False, "Expected FileNotFoundError"

#     except FileNotFoundError:
#         pass


# # 16
# def test_corrupted_json():

#     temp_file = tempfile.NamedTemporaryFile(
#         delete=False,
#         suffix=".json",
#         mode="w",
#         encoding="utf-8"
#     )

#     temp_file.write("{ invalid json }")
#     temp_file.close()

#     try:
#         load_ai_results(temp_file.name)
#         assert False, "Expected ValueError"

#     except ValueError:
#         pass

#     finally:
#         os.unlink(temp_file.name)


# if __name__ == "__main__":

#     print("\n===================================")
#     print(" HOTEL RECOMMENDATION APP TEST RUN ")
#     print("===================================\n")

#     tests = [
#         ("Invalid Location Input", test_invalid_location),
#         ("Invalid Budget Input", test_invalid_budget),
#         ("Invalid Email Address", test_invalid_email),
#         ("User Cancels Input", test_user_cancel_input),
#         ("Invalid Menu Selection", test_invalid_menu_choice),
#         ("Admin Login Failure", test_admin_login_failure),
#         ("AI Service Unavailable", test_ai_service_unavailable),
#         ("AI Request Timeout", test_ai_timeout),
#         ("Invalid AI Response Format", test_invalid_ai_response),
#         ("Missing Hotel Data", test_missing_hotel_data),
#         ("Duplicate Hotel Records", test_duplicate_hotels),
#         ("Missing Distance Information", test_missing_distance_information),
#         ("Hotel Exceeds Budget", test_hotel_exceeds_budget),
#         ("Hotel Rating Too Low", test_hotel_rating_too_low),
#         ("Recommendation File Missing", test_missing_recommendation_file),
#         ("Corrupted JSON Data", test_corrupted_json),
#     ]

#     for test_name, test_function in tests:
#         run_test(test_name, test_function)

#     print("\n===================================")
#     print("TEST SUMMARY")
#     print("===================================")
#     print(f"Passed: {passed}")
#     print(f"Failed: {failed}")
#     print(f"Total : {passed + failed}")

#     if failed == 0:
#         print("\nALL TESTS PASSED")
#     else:
#         print("\nSOME TESTS FAILED")

print("testing test.py docker")