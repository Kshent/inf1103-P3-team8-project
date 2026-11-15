class DistanceFormatter:
    """Formats a distance-to-preference dictionary for display."""

    @staticmethod
    def format(item: dict) -> str:
        target = item.get(
            'target',
            'Location',
        )

        distance = item.get(
            'distance_m'
        )

        if isinstance(
            distance,
            (int, float),
        ):
            if distance >= 1000:
                return (
                    f'{target}: '
                    f'{distance / 1000:.1f} km'
                )

            return (
                f'{target}: '
                f'{int(distance)} m'
            )

        return (
            f'{target}: '
            'distance unavailable'
        )
