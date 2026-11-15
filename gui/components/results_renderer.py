from nicegui import ui

from .hotel_card import HotelCard


class ResultsRenderer:
    """Renders the complete hotel recommendation result section."""

    def __init__(self, bundle: dict) -> None:
        self._bundle = bundle

    def render(self) -> None:
        bundle = self._bundle

        logic_result = bundle[
            'logic_result'
        ]

        record = bundle[
            'user_input_details'
        ]

        top_hotels = logic_result.get(
            'top_hotels',
            [],
        )

        summary = logic_result.get(
            'summary',
            {},
        )

        requirements = logic_result.get(
            'requirements',
            {},
        )

        with ui.card().classes(
            'w-full rounded-3xl p-6 '
            'bg-gradient-to-r '
            'from-purple-50 to-indigo-50 '
            'shadow-none border '
            'border-purple-100'
        ):
            with ui.row().classes(
                'w-full items-center '
                'justify-between gap-4 '
                'flex-wrap'
            ):
                with ui.column().classes(
                    'gap-1'
                ):
                    ui.label(
                        (
                            f"Your "
                            f"{record.get('destination', '')} "
                            "recommendations"
                        )
                    ).classes(
                        'text-2xl font-bold '
                        'text-slate-900'
                    )

                    ui.label(
                        (
                            f"{bundle['profile_name']} "
                            "traveller profile"
                        )
                    ).classes(
                        'text-purple-700 '
                        'font-semibold'
                    )

                ui.badge(
                    (
                        f"{summary.get('received', 0)} "
                        "reviewed • "
                        f"{summary.get('returned', 0)} "
                        "recommended"
                    )
                ).props(
                    'color=primary'
                )

            with ui.row().classes(
                'gap-2 flex-wrap mt-2'
            ):
                ui.chip(
                    (
                        f"S$"
                        f"{record.get('budget_min', 0):g}"
                        " - S$"
                        f"{record.get('budget_max', 0):g}"
                        " / night"
                    ),
                    icon='payments',
                )

                if record.get(
                    'preferences'
                ):
                    ui.chip(
                        record[
                            'preferences'
                        ],
                        icon='tune',
                    )

            if (
                top_hotels
                and top_hotels[0].get(
                    'breakdown'
                )
            ):
                ui.label(
                    'Applied scoring'
                ).classes(
                    'font-semibold '
                    'text-slate-700 mt-3'
                )

                with ui.row().classes(
                    'gap-2 flex-wrap'
                ):
                    for line in (
                        top_hotels[0][
                            'breakdown'
                        ]
                    ):
                        ui.chip(
                            (
                                f"{line.get('category')}: "
                                f"{line.get('max')} pts"
                            )
                        ).props(
                            'outline color=primary'
                        )

        for note in requirements.get(
            'not_scored',
            [],
        ):
            ui.label(
                note
            ).classes(
                'w-full bg-amber-50 '
                'text-amber-900 p-3 '
                'rounded-xl text-sm'
            )

        if not top_hotels:
            with ui.card().classes(
                'w-full p-8 '
                'items-center rounded-2xl'
            ):
                ui.icon(
                    'search_off',
                    size='3rem',
                    color='grey',
                )

                ui.label(
                    'No hotels matched '
                    'your requirements.'
                ).classes(
                    'text-xl font-semibold'
                )

            return

        for hotel in top_hotels:
            HotelCard(
                hotel
            ).render()

        rejected = logic_result.get(
            'rejected_hotels',
            [],
        )

        if rejected:
            with ui.expansion(
                (
                    f'View '
                    f'{len(rejected)} '
                    'excluded hotel(s)'
                ),
                icon='visibility_off',
            ).classes(
                'w-full bg-slate-100 '
                'rounded-xl'
            ):
                for hotel in rejected:
                    ui.label(
                        (
                            f"• "
                            f"{hotel.get('name', 'Hotel')}: "
                            f"{hotel.get('reject_reason', 'Did not meet requirements')}"
                        )
                    ).classes(
                        'text-sm text-slate-600'
                    )

        if bundle.get(
            'saved'
        ):
            with ui.row().classes(
                'w-full bg-emerald-50 '
                'text-emerald-800 '
                'rounded-xl p-3 '
                'items-center gap-2'
            ):
                ui.icon(
                    'check_circle'
                )

                ui.label(
                    'Recommendations saved successfully.'
                )
