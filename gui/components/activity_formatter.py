class ActivityFormatter:
    """Formats nearby activity data for display."""

    @staticmethod
    def format(activity) -> str:
        if not isinstance(
            activity,
            dict,
        ):
            return str(activity)

        name = activity.get(
            'name',
            'Activity',
        )

        distance = activity.get(
            'distance_m'
        )

        if isinstance(
            distance,
            (int, float),
        ):
            return (
                f'{name} '
                f'({int(distance)} m)'
            )

        return name
