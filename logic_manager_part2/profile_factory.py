
class ProfileFactory:

    # Hardcoded weightages for Options 1, 2 and 3
    PRESETS = {
        "balanced": {
            "rating": 25,
            "price": 20,
            "location": 25,
            "preferences": 20,
            "bonus": 10
        },

        "budget": {
            "rating": 15,
            "price": 45,
            "location": 20,
            "preferences": 10,
            "bonus": 10
        },

        "quality_focused": {
            "rating": 40,
            "price": 10,
            "location": 20,
            "preferences": 20,
            "bonus": 10
        }
    }

    LABELS = {
        "balanced": "Balanced Traveller",
        "budget": "Budget Traveller",
        "quality_focused": "Quality-Focused Traveller",
        "custom": "Customisation"
    }

    REQUIRED = {
        "rating",
        "price",
        "location",
        "preferences",
        "bonus"
    }

    def get_default_weights(self, style):

        if style not in self.PRESETS:
            raise ValueError("Invalid traveller style.")

        return self.PRESETS[style].copy()

    def validate_weights(self, weights):

        # Check 1: Input must be a dictionary
        if not isinstance(weights, dict):
            raise ValueError("Weightages must be a dictionary.")

        weights = weights.copy()

        # Convert the IO Manager's "amenities" key to "preferences"
        if "amenities" in weights and "preferences" not in weights:
            weights["preferences"] = weights.pop("amenities")

        # Check 2: All five criteria must be included
        if set(weights.keys()) != self.REQUIRED:
            raise ValueError("All five scoring criteria are required.")

        # Check 3: All values must be non-negative whole numbers
        for value in weights.values():
            if type(value) is not int or value < 0:
                raise ValueError(
                    "Weightages must be non-negative whole numbers."
                )

        # Check 4: Total must equal exactly 100
        if sum(weights.values()) != 100:
            raise ValueError(
                "Total weightage must equal exactly 100."
            )

        return weights.copy()

    def resolve(self, choice):

        if not isinstance(choice, dict):
            raise ValueError("Invalid traveller profile.")

        style = choice.get("name")

        # Options 1, 2 and 3
        if style in self.PRESETS:
            weights = self.get_default_weights(style)

        # Option 4
        elif style == "custom":
            weights = self.validate_weights(
                choice.get("weights")
            )

        else:
            raise ValueError("Invalid traveller style.")

        return {
            "name": style,
            "label": self.LABELS[style],
            "weights": weights
        }
