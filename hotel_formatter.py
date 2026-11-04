"""Builds the lines of text for recommendations and records (never prints)."""

import textwrap


class HotelFormatter:
    WIDTH = 78
    HEAVY_LINE = "=" * 70
    LIGHT_LINE = "-" * 70

    RATING_FOOTER = (
        "About the ratings: Every rating shown is the customer review rating "
        "(the average of guest reviews, as reported by the AI). It is not the "
        "hotel's number of stars. Scores come from fixed rules applied to the "
        "hotel data shown above.")

    # -- small helpers -----------------------------------------------------
    def _wrap(self, text, indent):
        return textwrap.fill(text, width=self.WIDTH, initial_indent=indent,
                             subsequent_indent=indent)

    @staticmethod
    def _money(value):
        return "S$%g" % value

    @staticmethod
    def _join(items):
        return ", ".join(items) if items else "Not listed"

    @staticmethod
    def _activity_text(activity):
        if isinstance(activity, dict):
            name = activity.get("name", "")
            distance = activity.get("distance_m")
            if isinstance(distance, (int, float)):
                return "%s (%s m)" % (name, "{:,}".format(int(distance)))
            return str(name)
        return str(activity)          # older saved records

    # -- saved records -----------------------------------------------------
    def hotel_list(self, hotels):
        """Lines for a plain list of hotel dictionaries (saved records)."""
        lines = []
        for number, hotel in enumerate(hotels, start=1):
            lines.append(f"\n  {number}. {hotel['name']}")
            lines.append(f"     {hotel['city']}, {hotel['country']}")
            lines.append(f"     SGD {hotel['price_per_night_sgd']} per night | "
                         f"Rating: {hotel['rating']}")
            lines.append(f"     Amenities: {', '.join(hotel['amenities'])}")
            lines.append("     Nearby food options: "
                         f"{', '.join(hotel['nearby_food'])}")
            activities = [self._plain_activity(a)
                          for a in hotel.get("nearby_activities", [])]
            lines.append(f"     Nearby activities: {', '.join(activities)}")
        return lines

    @staticmethod
    def _plain_activity(activity):
        if isinstance(activity, dict):
            name = activity.get("name", "Unknown")
            distance = activity.get("distance_m")
            return f"{name} ({distance}m)" if distance is not None else name
        return str(activity)

    def records(self, records):
        if not records:
            return ["\nNo records found."]
        lines = []
        for record in records:
            lines.append(f"\nEmail: {record['email']}")
            for number, hotels in enumerate(record["searches"], start=1):
                lines.append(f"\n  --- Search {number} ---")
                lines.extend(self.hotel_list(hotels))
        return lines

    # -- recommendation report ---------------------------------------------
    def recommendation_report(self, result, record):
        summary = result["summary"]
        requirements = result["requirements"]
        profile = result.get("profile")

        lines = ["", self.HEAVY_LINE, "TOP HOTEL RECOMMENDATIONS",
                 self.HEAVY_LINE,
                 "Destination : %s" % record.get("destination"),
                 "Budget      : %s - %s per night" % (
                     self._money(record.get("budget_min")),
                     self._money(record.get("budget_max"))),
                 "Preferences : %s" % (record.get("preferences") or "None")]
        if profile:
            lines.append("Priorities  : %s" % profile["label"])
        if requirements["targets"]:
            lines.append("Near        : %s" % ", ".join(requirements["targets"]))
        lines.append("Reviewed    : %d hotels | Shown: %d | Rejected: %d" % (
            summary["received"], summary["returned"], summary["rejected"]))
        lines.append(self.HEAVY_LINE)

        if requirements["unverified"]:
            lines.append(self._wrap(
                "Could not be checked against hotel data (so not scored): "
                + ", ".join(requirements["unverified"]) + ".", ""))
        for note in requirements["not_scored"]:
            lines.append(self._wrap(note, ""))

        if not result["top_hotels"]:
            lines += ["", "No hotels matched your requirements."]
        for hotel in result["top_hotels"]:
            lines.extend(self._hotel_block(hotel))

        if result["rejected_hotels"]:
            lines += ["", "REJECTED"]
            for hotel in result["rejected_hotels"]:
                lines.append(self._wrap(
                    "x %s: %s" % (hotel["name"], hotel["reject_reason"]), "  "))
            lines.append(self.LIGHT_LINE)

        lines += ["", self._wrap(self.RATING_FOOTER, ""), ""]
        return lines

    def _hotel_block(self, hotel):
        rating = hotel.get("rating")
        rating_text = ("%.1f / 5" % rating
                       if isinstance(rating, (int, float)) else "Not available")

        lines = ["", "#%d  %s" % (hotel["rank"], hotel["name"]),
                 "    SCORE: %d/%d - %s" % (hotel["score"], hotel["score_max"],
                                             hotel["verdict"]),
                 "    Price: %s per night" % self._money(
                     hotel["price_per_night_sgd"]),
                 "    Customer review rating: %s (average of guest reviews, "
                 "not hotel stars)" % rating_text]
        for item in hotel.get("distance_to_preferences") or []:
            distance = item.get("distance_m")
            if isinstance(distance, (int, float)):
                lines.append("    Distance: %s m from %s" % (
                    "{:,}".format(int(distance)), item.get("target")))
        lines.append(self._wrap("Amenities: " + self._join(
            hotel.get("amenities")), "    "))
        lines.append(self._wrap("Nearby food: " + self._join(
            hotel.get("nearby_food")), "    "))
        lines.append(self._wrap("Nearby activities: " + self._join(
            [self._activity_text(a)
             for a in hotel.get("nearby_activities") or []]), "    "))

        lines += ["", "    Why %d/%d:" % (hotel["score"], hotel["score_max"])]
        for line in hotel["breakdown"]:
            lines.append("      %-24s %2d / %2d" % (
                line["category"], line["points"], line["max"]))
            lines.append(self._wrap(line["reason"], "        "))
        lines.append("      %-24s %2d / %2d" % (
            "TOTAL", hotel["score"], hotel["score_max"]))

        if hotel.get("notes"):
            lines.append("")
            for note in hotel["notes"]:
                lines.append(self._wrap("Note: " + note, "    "))
        lines.append(self.LIGHT_LINE)
        return lines
