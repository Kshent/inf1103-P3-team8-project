import html


class RecommendationEmail:
    """Turns the Top 3 hotels into an email that is easy to read.

    Builds three parts of the same email:
      subject()     - the subject line
      plain_text()  - a neat text version, for email apps without HTML
      html()        - a formatted version with one card per hotel

    It only formats; sending is done by EmailSender.
    """

    # Colours used in the HTML version
    __ACCENT = "#1f6f8b"
    __TEXT = "#1d2733"
    __MUTED = "#5f6b7a"
    __CARD_BORDER = "#dde3ea"
    __PAGE = "#f3f6f9"

    def __init__(self, destination, hotels):
        self.__destination = str(destination).strip() or "your trip"
        self.__hotels = [hotel for hotel in hotels if isinstance(hotel, dict)]

    # ---------------------------------------------------------------
    # The three parts of the email
    # ---------------------------------------------------------------
    def subject(self):
        return "Your top hotel picks for " + self.__destination

    def plain_text(self):
        lines = [
            "Your top hotel picks for " + self.__destination,
            "=" * 50,
            "",
            "Here are the hotels that best match your search, "
            "best match first.",
            "",
        ]
        for rank, hotel in enumerate(self.__hotels, start=1):
            lines.extend(self.__hotel_as_text(rank, hotel))
            lines.append("")
        lines.append("Prices are per night in Singapore dollars. "
                     "Ratings are average guest review scores out of 5.")
        lines.append("Happy travels!")
        return "\n".join(lines)

    def html(self):
        cards = "".join(self.__hotel_as_html(rank, hotel)
                        for rank, hotel in enumerate(self.__hotels, start=1))
        destination = html.escape(self.__destination)
        return f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:{self.__PAGE};font-family:Arial,Helvetica,sans-serif;color:{self.__TEXT};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{self.__PAGE};">
    <tr><td align="center" style="padding:24px 12px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;">
        <tr><td style="background:{self.__ACCENT};color:#ffffff;padding:24px;border-radius:10px 10px 0 0;">
          <div style="font-size:13px;letter-spacing:1px;text-transform:uppercase;opacity:0.85;">Hotel recommendations</div>
          <div style="font-size:24px;font-weight:bold;margin-top:6px;">Your top picks for {destination}</div>
        </td></tr>
        <tr><td style="background:#ffffff;padding:20px 24px 4px;border-radius:0 0 10px 10px;">
          <p style="margin:0 0 16px;font-size:15px;line-height:1.5;">Here are the hotels that best match your search, best match first.</p>
          {cards}
        </td></tr>
        <tr><td style="padding:16px 8px;font-size:12px;line-height:1.5;color:{self.__MUTED};text-align:center;">
          Prices are per night in Singapore dollars. Ratings are average guest review scores out of 5.<br>Happy travels!
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

    # ---------------------------------------------------------------
    # One hotel
    # ---------------------------------------------------------------
    def __hotel_as_text(self, rank, hotel):
        rows = [
            ("Location", self.__location(hotel)),
            ("Price/night", self.__price(hotel)),
            ("Guest rating", self.__rating(hotel)),
            ("Amenities", self.__join(self.__amenities(hotel))),
        ]
        distances = self.__distances(hotel)
        if distances:
            rows.append(("Distance to", self.__join(distances)))
        rows.append(("Food nearby", self.__join(self.__food(hotel))))
        rows.append(("Things to do", self.__join(self.__activities(hotel))))
        return [f"{rank}. {self.__name(hotel)}"] + [
            f"   {label:<12} : {value}" for label, value in rows]

    def __hotel_as_html(self, rank, hotel):
        rows = [
            ("Amenities", self.__amenities(hotel)),
            ("Distance to", self.__distances(hotel)),
            ("Food nearby", self.__food(hotel)),
            ("Things to do", self.__activities(hotel)),
        ]
        details = "".join(self.__detail_row(label, items)
                          for label, items in rows if items or label != "Distance to")
        return f"""\
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid {self.__CARD_BORDER};border-radius:8px;margin:0 0 16px;">
  <tr><td style="padding:16px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td width="36" valign="top">
          <div style="width:28px;height:28px;line-height:28px;border-radius:14px;background:{self.__ACCENT};color:#ffffff;text-align:center;font-weight:bold;font-size:14px;">{rank}</div>
        </td>
        <td valign="top">
          <div style="font-size:18px;font-weight:bold;">{html.escape(self.__name(hotel))}</div>
          <div style="font-size:14px;color:{self.__MUTED};margin-top:2px;">{html.escape(self.__location(hotel))}</div>
        </td>
      </tr>
    </table>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:12px 0 4px;">
      <tr>
        <td width="50%" style="padding-right:5px;">
          <div style="background:{self.__PAGE};border-radius:6px;padding:8px 10px;">
            <div style="font-size:12px;color:{self.__MUTED};">Price per night</div>
            <div style="font-size:16px;font-weight:bold;">{html.escape(self.__price(hotel))}</div>
          </div>
        </td>
        <td width="50%" style="padding-left:5px;">
          <div style="background:{self.__PAGE};border-radius:6px;padding:8px 10px;">
            <div style="font-size:12px;color:{self.__MUTED};">Guest rating</div>
            <div style="font-size:16px;font-weight:bold;">{html.escape(self.__rating(hotel))}</div>
          </div>
        </td>
      </tr>
    </table>
    {details}
  </td></tr>
</table>
"""

    def __detail_row(self, label, items):
        return (f'<div style="font-size:14px;line-height:1.5;margin-top:8px;">'
                f'<span style="font-weight:bold;">{html.escape(label)}:</span> '
                f'{html.escape(self.__join(items))}</div>')

    # ---------------------------------------------------------------
    # Reading the hotel fields safely (missing or odd values never crash)
    # ---------------------------------------------------------------
    @staticmethod
    def __name(hotel):
        return str(hotel.get("name") or "Unnamed hotel").strip()

    @staticmethod
    def __location(hotel):
        parts = [str(hotel.get(field) or "").strip() for field in ("city", "country")]
        parts = [part for part in parts if part and part != "Unknown"]
        # Avoid "Singapore, Singapore" when the city is the country
        if len(parts) == 2 and parts[0].lower() == parts[1].lower():
            parts = parts[:1]
        return ", ".join(parts) or "Location not listed"

    @staticmethod
    def __price(hotel):
        price = hotel.get("price_per_night_sgd")
        if isinstance(price, (int, float)) and not isinstance(price, bool):
            return f"S${price:,.0f}"
        return "Not listed"

    @staticmethod
    def __rating(hotel):
        rating = hotel.get("rating")
        if isinstance(rating, (int, float)) and not isinstance(rating, bool):
            return f"{rating:.1f} / 5"
        return "Not rated"

    @staticmethod
    def __amenities(hotel):
        return RecommendationEmail.__text_list(hotel.get("amenities"))

    @staticmethod
    def __food(hotel):
        return RecommendationEmail.__text_list(hotel.get("nearby_food"))

    @staticmethod
    def __distances(hotel):
        """Distance to each place the user asked to be near."""
        items = []
        for place in RecommendationEmail.__dict_list(hotel.get("distance_to_preferences")):
            target = str(place.get("target") or "").strip()
            if target:
                items.append(f"{target} ({RecommendationEmail.__metres(place.get('distance_m'))})")
        return items

    @staticmethod
    def __activities(hotel):
        items = []
        for activity in hotel.get("nearby_activities") or []:
            if isinstance(activity, dict):
                name = str(activity.get("name") or "").strip()
                if name:
                    distance = activity.get("distance_m")
                    if isinstance(distance, (int, float)) and not isinstance(distance, bool):
                        name += f" ({RecommendationEmail.__metres(distance)})"
                    items.append(name)
            elif str(activity).strip():
                items.append(str(activity).strip())
        return items

    @staticmethod
    def __metres(distance):
        if isinstance(distance, (int, float)) and not isinstance(distance, bool):
            if distance >= 1000:
                return f"{distance / 1000:.1f} km"
            return f"{distance:,.0f} m"
        return "distance unknown"

    @staticmethod
    def __text_list(value):
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    @staticmethod
    def __dict_list(value):
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    @staticmethod
    def __join(items):
        return ", ".join(items) if items else "Not listed"