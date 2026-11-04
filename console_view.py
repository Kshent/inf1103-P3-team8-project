"""Asks the traveller questions and shows results."""

from channels import ConsoleInput, ConsoleOutput
from hotel_formatter import HotelFormatter
from validators import (
    LocationValidator,
    PriceRangeValidator,
    EmailValidator,
    PreferencesValidator,
    ChoiceValidator,
    WeightValidator,
)


class ConsoleView:
    """Asks the traveller questions and shows results."""

    def __init__(self, source=None, sink=None, formatter=None):
        self.__source = source or ConsoleInput()
        self.__sink = sink or ConsoleOutput()
        self.__formatter = formatter or HotelFormatter()

    # -- internal helpers --------------------------------------------------
    def _show(self, lines):
        for line in lines:
            self.__sink.write(line)

    def _ask(self, prompt, validator):
        """Keep asking until the validator accepts the answer."""
        while True:
            result = validator.validate(self.__source.read(prompt))
            if result.ok:
                return result.value
            self.__sink.write(f"Error: {result.message}")

    # -- menus -------------------------------------------------------------
    def show_main_menu(self):
        """Show the main menu and return a valid choice: "1" to "4"."""
        validator = ChoiceValidator(("1", "2", "3", "4"),
                                    "Invalid option. Please enter 1, 2, 3 or 4")
        while True:
            self.__sink.write("\nWelcome to Team8's hotel recommendation app!\n")
            self.__sink.write("\n----------------------------------------------")
            self.__sink.write("1: Find a suitable hotel for your overseas "
                              "travel needs!")
            self.__sink.write("2: View your previous hotel records")
            self.__sink.write("3: Admin login (NOT FOR USERS)")
            self.__sink.write("4: Quit")

            result = validator.validate(self.__source.read(
                "Please enter option 1, 2, 3 or 4: "))
            if result.ok:
                return result.value
            self.__sink.write(result.message)

    # -- search inputs -----------------------------------------------------
    def request_mandatory_inputs(self):
        """Collect everything required before a search can begin."""
        self.__sink.write("\n=== Hotel Search ===")
        location = self._ask("Enter your destination country or city: ",
                             LocationValidator())
        price_range = self._ask(
            "Enter your price range in SGD, for example 100-250: ",
            PriceRangeValidator())
        email_address = self._ask("Enter your email address: ",
                                  EmailValidator())
        return {"location": location, "price_range": price_range,
                "email_address": email_address}

    def request_user_preferences(self):
        """Optional free-text preferences (an empty answer is allowed)."""
        self.__sink.write(
            "\nDescribe your hotel preferences. For example: near public "
            "transport, breakfast included, quiet room and swimming pool.")
        return self._ask("\nYour preferences: ", PreferencesValidator())

    def request_priority_profile(self, options, categories, saved=None):
        """Let the traveller choose how hotels are scored (new feature).

        options    - [{"name", "label", "weights"}, ...] the fixed profiles
        categories - [{"key", "label"}, ...] the five scoring criteria
        saved      - the profile dict saved from last time, or None

        Options 1 to N are the fixed profiles; the last option is
        Customisation, where the traveller assigns the points themselves.
        Returns {"name": ..., "weights": {...} or None}."""
        write = self.__sink.write
        write("\n=== Traveller Priorities ===")
        write("Choose how hotels are scored. Every option adds up to 100 "
              "points.")

        choices = {}
        for number, option in enumerate(options, start=1):
            write(f"\n{number}: {option['label']}")
            self._show_weights(option["weights"], categories)
            choices[str(number)] = option["name"]

        custom_number = str(len(options) + 1)
        write(f"\n{custom_number}: Customisation (customise the scoring "
              "weightages)")
        self._show_weights({c["key"]: 0 for c in categories}, categories)
        write("   (you will assign these yourself; they must add up to /100)")
        choices[custom_number] = "custom"

        if saved:
            hint = ("press Enter to keep your saved choice: "
                    f"{saved.get('label') or saved.get('name')}")
        else:
            hint = f"press Enter for {options[0]['label']}"
        validator = ChoiceValidator(
            [""] + list(choices),
            f"Please enter a number from 1 to {custom_number}.")
        answer = self._ask(f"\nChoose 1-{custom_number} ({hint}): ", validator)

        if answer == "":
            return saved if saved else {"name": options[0]["name"],
                                        "weights": None}
        name = choices[answer]
        if name != "custom":
            return {"name": name, "weights": None}

        earlier = saved.get("weights") if saved and saved.get("name") == "custom" else None
        return {"name": "custom",
                "weights": self._request_custom_weights(categories, earlier)}

    def _show_weights(self, weights, categories):
        """One line per criterion, like 'Price:  /20', then the total."""
        write = self.__sink.write
        for category in categories:
            write("   %-26s/%d" % (category["label"] + ":",
                                   weights[category["key"]]))
        write("   %-26s/%d" % ("Total:", sum(weights.values())))

    def _request_custom_weights(self, categories, previous=None):
        """Ask for the points of each criterion with a running total.
        Each answer is limited to the points still left, and if the five
        answers do not add up to exactly 100 the traveller is alerted and
        asked again (Enter keeps the earlier answer)."""
        write = self.__sink.write
        limit = 100
        previous = dict(previous or {})
        write(f"\nAssign the points for each criterion. They must add up "
              f"to exactly {limit}.")

        while True:
            weights = {}
            running = 0
            for position, category in enumerate(categories):
                key, label = category["key"], category["label"]
                remaining = limit - running
                keep = previous.get(key)

                range_text = f"0-{remaining}"
                if position == len(categories) - 1:
                    range_text += f"; {remaining} makes {limit}"
                if keep is not None:
                    range_text += f"; Enter keeps {keep}"
                prompt = f"  {label} ({range_text}): "

                validator = WeightValidator(remaining)
                while True:
                    raw = self.__source.read(prompt)
                    if raw == "" and keep is not None:
                        raw = str(keep)
                    result = validator.validate(raw)
                    if result.ok:
                        break
                    write(f"Error: {result.message}")

                weights[key] = result.value
                running += result.value
                write(f"    Running total: {running}/{limit} "
                      f"({limit - running} left)")

            if running == limit:
                write("\nYour scoring weightages:")
                self._show_weights(weights, categories)
                return weights

            write(f"\nAlert: your weightages add up to {running}, not "
                  f"{limit}. {limit - running} point(s) are still "
                  "unassigned. Please assign them again.")
            previous = weights

    # -- records and admin -------------------------------------------------
    def request_record_email(self):
        """Ask for the email whose records to view. Returns the lower-case
        email, or None if the user typed q."""
        validator = EmailValidator()
        while True:
            email = self.__source.read("Enter your email or q to quit: ")
            if email.lower() == "q":
                self.__sink.write("Exiting view hotel records")
                return None
            result = validator.validate(email)
            if result.ok:
                return result.value.lower()
            self.__sink.write(f"Invalid input : {result.message}")

    def admin_login(self, authenticator):
        """Returns True if login succeeds, False if the user quits with Q.
        `authenticator` is any object with check_username / check_password."""
        while True:
            username = self.__source.read("Enter username or Q to exit: ")
            if username.upper() == "Q":
                return False
            if not authenticator.check_username(username):
                self.__sink.write("Wrong username")
                continue

            while True:
                password = self.__source.read("Enter password or Q to exit: ")
                if password.upper() == "Q":
                    return False
                if not authenticator.check_password(password):
                    self.__sink.write("Wrong password")
                    continue
                return True

    # -- display -----------------------------------------------------------
    def display_message(self, message):
        self.__sink.write(message)

    def display_ai_dictionary(self, ai_dictionary):
        """Show the AI Manager's output as a plain dictionary."""
        self.__sink.write(ai_dictionary)

    def display_top_three_dictionary(self, top_three_dict):
        """Show the chosen top hotels as a plain dictionary."""
        self.__sink.write("\n=== TOP 3 HOTELS (DICTIONARY OUTPUT) ===")
        self.__sink.write(top_three_dict)
        self.__sink.write("=== END OF TOP 3 HOTELS (DICTIONARY OUTPUT) ===\n")

    def display_recommendations(self, result, record):
        """Show the Logic Manager's top hotels with score and breakdown."""
        self._show(self.__formatter.recommendation_report(result, record))

    def display_records(self, records):
        """Show records shaped like
        [{"email": email, "searches": [[hotels], ...]}]."""
        self._show(self.__formatter.records(records))
