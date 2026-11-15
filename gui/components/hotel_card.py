from nicegui import ui

from .activity_formatter import ActivityFormatter
from .distance_formatter import DistanceFormatter


class HotelCard:
    """Renders one ranked hotel recommendation card."""

    def __init__(self, hotel: dict) -> None:
        self._hotel = hotel

    def render(self) -> None:
        hotel = self._hotel

        score = hotel.get(
            'score',
            0,
        )

        score_max = hotel.get(
            'score_max',
            100,
        )

        with ui.card().classes(
            'w-full rounded-3xl p-6 shadow-sm '
            'border border-purple-100'
        ):
            with ui.row().classes(
                'w-full items-start '
                'justify-between gap-4'
            ):
                with ui.row().classes(
                    'items-start gap-4'
                ):
                    with ui.element(
                        'div'
                    ).classes(
                        'w-14 h-14 rounded-2xl '
                        'bg-purple-100 flex '
                        'items-center justify-center'
                    ):
                        ui.icon(
                            'hotel',
                            size='2rem',
                            color='primary',
                        )

                    with ui.column().classes(
                        'gap-1'
                    ):
                        ui.label(
                            f"#{hotel.get('rank', '')}  "
                            f"{hotel.get('name', 'Hotel')}"
                        ).classes(
                            'text-xl font-bold '
                            'text-slate-900'
                        )

                        ui.label(
                            f"{hotel.get('city', '')}, "
                            f"{hotel.get('country', '')}"
                        ).classes(
                            'text-slate-500'
                        )

                        with ui.row().classes(
                            'gap-2 items-center '
                            'flex-wrap'
                        ):
                            ui.chip(
                                (
                                    f"S$"
                                    f"{hotel.get('price_per_night_sgd', 0):g}"
                                    " / night"
                                ),
                                icon='payments',
                            ).props(
                                'outline color=primary'
                            )

                            rating = hotel.get(
                                'rating'
                            )

                            if isinstance(
                                rating,
                                (int, float),
                            ):
                                rating_text = (
                                    f'{rating:.1f} / 5'
                                )
                            else:
                                rating_text = (
                                    'Rating unavailable'
                                )

                            ui.chip(
                                rating_text,
                                icon='star',
                            ).props(
                                'outline color=amber'
                            )

                with ui.column().classes(
                    'items-end gap-0'
                ):
                    ui.label(
                        f'{score}/{score_max}'
                    ).classes(
                        'text-4xl font-bold '
                        'text-purple-700'
                    )

                    ui.label(
                        hotel.get(
                            'verdict',
                            '',
                        )
                    ).classes(
                        'text-sm font-medium '
                        'text-slate-500'
                    )

            distances = (
                hotel.get(
                    'distance_to_preferences'
                )
                or []
            )

            if distances:
                ui.separator().classes(
                    'my-2'
                )

                ui.label(
                    'Distance to your requested places'
                ).classes(
                    'font-semibold text-slate-700'
                )

                with ui.row().classes(
                    'gap-2 flex-wrap'
                ):
                    for item in distances:
                        ui.chip(
                            DistanceFormatter.format(
                                item
                            ),
                            icon='location_on',
                        ).props(
                            'color=purple-1 '
                            'text-color=purple-9'
                        )

            amenities = (
                hotel.get('amenities')
                or []
            )

            if amenities:
                ui.label(
                    'Amenities'
                ).classes(
                    'font-semibold '
                    'text-slate-700 mt-2'
                )

                with ui.row().classes(
                    'gap-2 flex-wrap'
                ):
                    for amenity in amenities:
                        ui.chip(
                            str(amenity)
                        ).props(
                            'color=grey-2 '
                            'text-color=grey-9'
                        )

            with ui.grid(
                columns=2
            ).classes(
                'w-full gap-4 mt-3 '
                'max-md:grid-cols-1'
            ):
                with ui.card().classes(
                    'w-full bg-slate-50 '
                    'shadow-none rounded-xl'
                ):
                    ui.label(
                        'Nearby food'
                    ).classes(
                        'font-semibold'
                    )

                    ui.label(
                        ', '.join(
                            hotel.get(
                                'nearby_food'
                            )
                            or ['Not listed']
                        )
                    ).classes(
                        'text-sm text-slate-600 '
                        'leading-relaxed'
                    )

                with ui.card().classes(
                    'w-full bg-slate-50 '
                    'shadow-none rounded-xl'
                ):
                    ui.label(
                        'Nearby activities'
                    ).classes(
                        'font-semibold'
                    )

                    activities = [
                        ActivityFormatter.format(
                            activity
                        )
                        for activity in (
                            hotel.get(
                                'nearby_activities'
                            )
                            or []
                        )
                    ]

                    ui.label(
                        (
                            ', '.join(
                                activities
                            )
                            if activities
                            else 'Not listed'
                        )
                    ).classes(
                        'text-sm text-slate-600 '
                        'leading-relaxed'
                    )

            with ui.expansion(
                'View Score Breakdown',
                icon='analytics',
            ).classes(
                'w-full mt-3 bg-purple-50 '
                'rounded-xl text-purple-900'
            ):
                for line in hotel.get(
                    'breakdown',
                    [],
                ):
                    points = line.get(
                        'points',
                        0,
                    )

                    maximum = line.get(
                        'max',
                        0,
                    )

                    if maximum:
                        progress = (
                            points / maximum
                        )
                    else:
                        progress = 0

                    with ui.column().classes(
                        'w-full gap-1 mb-4'
                    ):
                        with ui.row().classes(
                            'w-full justify-between '
                            'items-center'
                        ):
                            ui.label(
                                line.get(
                                    'category',
                                    'Category',
                                )
                            ).classes(
                                'font-semibold'
                            )

                            ui.label(
                                f'{points} / {maximum}'
                            ).classes(
                                'font-bold'
                            )

                        ui.linear_progress(
                            value=progress,
                            show_value=False,
                        ).props(
                            'rounded color=primary'
                        )

                        ui.label(
                            line.get(
                                'reason',
                                '',
                            )
                        ).classes(
                            'text-sm text-slate-600 '
                            'leading-relaxed'
                        )
