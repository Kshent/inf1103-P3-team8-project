
class ProfileFactory:

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

    @classmethod
    def get_default_weights(cls, style):

        if style not in cls.PRESETS:
            raise ValueError("Invalid traveller style.")

        return cls.PRESETS[style].copy()


    @classmethod
    def catalog(cls):

        labels = {
            "balanced": "Balanced Traveller",
            "budget": "Budget Traveller",
            "quality_focused": "Quality-Focused Traveller"
        }

        profiles = []

        for name, weights in cls.PRESETS.items():
            profiles.append({
                "name": name,
                "label": labels[name],
                "weights": weights.copy()
            })

        return profiles


    @staticmethod
    def validate_weights(weights):

        required = {
            "rating",
            "price",
            "location",
            "preferences",
            "bonus"
        }

        # Check 1: Must be a dictionary
        if not isinstance(weights, dict):
            raise ValueError("Weightages must be a dictionary.")

        # Check 2: Must contain all five criteria
        if set(weights.keys()) != required:
            raise ValueError("All five scoring criteria are required.")

        # Check 3: All weightages must be non-negative whole numbers
        for value in weights.values():
            if type(value) is not int or value < 0:
                raise ValueError(
                    "Weightages must be non-negative whole numbers."
                )

        # Check 4: Total must equal 100
        if sum(weights.values()) != 100:
            raise ValueError("Total weightage must equal 100.")

        return weights.copy()
