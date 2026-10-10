"""result_display.py - temporary output for the logic manager's results.

Stand-in until io_manager has a results screen: whoever owns io_manager can
move show_recommendations() into it unchanged. All print() calls for results
live here, never in logic_manager.py.
"""
import textwrap

WIDTH = 78
HEAVY = "=" * 70
LIGHT = "-" * 70

FOOTER = (
    "About the ratings: every rating shown is the customer review rating "
    "(the average of guest reviews, as reported by the AI). It is not the "
    "hotel's number of stars. Scores come from fixed rules applied to the hotel "
    "data shown above."
)

NOTE_TEXT = {
    "rating_missing": "No customer review rating was available.",
    "rating_may_be_stars": (
        "The rating is a whole number, so it may be a hotel's number of stars "
        "rather than an average of guest reviews. Please verify."),
    "amenities_missing": "No amenities were listed.",
    "distance_unknown": "Distance to a requested place is unknown.",
}


def _wrap(text, indent):
    return textwrap.fill(text, width=WIDTH, initial_indent=indent,
                         subsequent_indent=indent)


def _money(value):
    return "S$%g" % value


def _join(items):
    return ", ".join(items) if items else "Not listed"


def _activity_text(activity):
    if isinstance(activity, dict):
        name = activity.get("name", "")
        distance = activity.get("distance_m")
        if isinstance(distance, (int, float)):
            return "%s (%s m)" % (name, "{:,}".format(int(distance)))
        return str(name)
    return str(activity)


def _show_hotel(hotel):
    rating = hotel.get("rating")
    rating_text = "%.1f / 5" % rating if isinstance(rating, (int, float)) \
        else "Not available"

    print()
    print("#%d  %s" % (hotel["rank"], hotel["name"]))
    print("    SCORE: %d/%d - %s" % (
        hotel["score"], hotel["score_max"], hotel["verdict"]))
    print("    Price: %s per night" % _money(hotel["price_per_night_sgd"]))
    print("    Customer review rating: %s (average of guest reviews, "
          "not hotel stars)" % rating_text)
    for item in hotel.get("distance_to_preferences") or []:
        distance = item.get("distance_m")
        if isinstance(distance, (int, float)):
            print("    Distance: %s m from %s" % (
                "{:,}".format(int(distance)), item.get("target")))
    print(_wrap("Amenities: " + _join(hotel.get("amenities")), "    "))
    print(_wrap("Nearby food: " + _join(hotel.get("nearby_food")), "    "))
    print(_wrap("Nearby activities: " + _join(
        [_activity_text(a) for a in hotel.get("nearby_activities") or []]),
        "    "))

    print()
    print("    Why %d/%d:" % (hotel["score"], hotel["score_max"]))
    for line in hotel["breakdown"]:
        print("      %-24s %2d / %2d" % (
            line["category"], line["points"], line["max"]))
        print(_wrap(line["reason"], "        "))
    print("      %-24s %2d / %2d" % ("TOTAL", hotel["score"],
                                     hotel["score_max"]))

    if hotel.get("flags"):
        print()
        for flag in hotel["flags"]:
            print(_wrap("Note: " + NOTE_TEXT.get(flag, flag), "    "))
    print(LIGHT)