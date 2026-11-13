from __future__ import annotations

from nicegui import ui


def setup_page() -> None:
    """Apply common styling to every page."""

    ui.query('body').classes(
        'bg-slate-50 text-slate-800'
    )

    ui.query('.nicegui-content').classes(
        'w-full'
    )


def page_header(
    title: str,
    subtitle: str = '',
    back_to: str | None = None,
) -> None:

    with ui.row().classes(
        'w-full max-w-6xl mx-auto '
        'items-center gap-4 px-6 pt-6'
    ):

        if back_to:

            ui.button(
                icon='arrow_back',
                on_click=lambda:
                ui.navigate.to(back_to),
            ).props(
                'flat round color=primary'
            )

        with ui.column().classes('gap-0'):

            ui.label(
                title
            ).classes(
                'text-3xl font-bold text-slate-900'
            )

            if subtitle:

                ui.label(
                    subtitle
                ).classes(
                    'text-slate-500 text-base'
                )


def menu_card(
    icon: str,
    title: str,
    description: str,
    button_text: str,
    destination: str,
) -> None:

    with ui.card().classes(
        'w-full p-6 rounded-2xl shadow-sm '
        'border border-slate-100 '
        'hover:shadow-lg transition-all'
    ):

        with ui.row().classes(
            'items-center gap-3'
        ):

            ui.icon(
                icon,
                size='2.4rem',
                color='primary',
            )

            ui.label(
                title
            ).classes(
                'text-xl font-bold text-slate-900'
            )

        ui.label(
            description
        ).classes(
            'text-slate-500 leading-relaxed '
            'min-h-[48px]'
        )

        ui.button(
            button_text,
            icon='arrow_forward',
            on_click=lambda:
            ui.navigate.to(destination),
        ).props(
            'unelevated rounded color=primary'
        ).classes(
            'mt-2'
        )


def _distance_text(
    item: dict,
) -> str:

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


def _activity_text(
    activity,
) -> str:

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


def hotel_card(
    hotel: dict,
) -> None:

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

        # -------------------------------------------------
        # Hotel heading
        # -------------------------------------------------

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

            # Large score on right
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

        # -------------------------------------------------
        # Location distances
        # -------------------------------------------------

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
                        _distance_text(item),
                        icon='location_on',
                    ).props(
                        'color=purple-1 '
                        'text-color=purple-9'
                    )

        # -------------------------------------------------
        # Amenities
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Food + activities
        # -------------------------------------------------

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
                    _activity_text(
                        activity
                    )
                    for activity
                    in (
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

        # -------------------------------------------------
        # EXPANDABLE SCORE BREAKDOWN
        # -------------------------------------------------

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


def render_results(
    bundle: dict,
) -> None:

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

    # -------------------------------------------------
    # Search summary
    # -------------------------------------------------

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

        # -------------------------------------------------
        # ACTUAL scoring used by Logic Manager
        # -------------------------------------------------

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

    # -------------------------------------------------
    # Logic notes
    # -------------------------------------------------

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

    # -------------------------------------------------
    # No results
    # -------------------------------------------------

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

    # -------------------------------------------------
    # Top 3
    # -------------------------------------------------

    for hotel in top_hotels:

        hotel_card(
            hotel
        )

    # -------------------------------------------------
    # Rejected hotels
    # -------------------------------------------------

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

    # -------------------------------------------------
    # Saved confirmation
    # -------------------------------------------------

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


def render_saved_records(
    records,
) -> None:

    if not records:

        with ui.card().classes(
            'w-full items-center '
            'p-8 rounded-2xl'
        ):

            ui.icon(
                'history',
                size='3rem',
                color='grey',
            )

            ui.label(
                'No saved hotel records found.'
            ).classes(
                'text-lg font-semibold'
            )

        return

    for record in records:

        email = record.get(
            'email',
            'Saved traveller',
        )

        searches = record.get(
            'searches',
            [],
        )

        with ui.card().classes(
            'w-full rounded-2xl p-5'
        ):

            ui.label(
                email
            ).classes(
                'text-lg font-bold '
                'text-slate-900'
            )

            for index, hotels in enumerate(
                searches,
                start=1,
            ):

                with ui.expansion(
                    f'Search {index}',
                    icon='history',
                ).classes(
                    'w-full'
                ):

                    for hotel in hotels:

                        with ui.row().classes(
                            'w-full items-center '
                            'justify-between '
                            'border-b '
                            'border-slate-100 py-2'
                        ):

                            with ui.column().classes(
                                'gap-0'
                            ):

                                ui.label(
                                    hotel.get(
                                        'name',
                                        'Hotel',
                                    )
                                ).classes(
                                    'font-semibold'
                                )

                                ui.label(
                                    (
                                        f"{hotel.get('city', '')}, "
                                        f"{hotel.get('country', '')}"
                                    )
                                ).classes(
                                    'text-sm text-slate-500'
                                )

                            ui.label(
                                (
                                    f"S$"
                                    f"{hotel.get('price_per_night_sgd', 0):g}"
                                )
                            ).classes(
                                'font-semibold '
                                'text-purple-700'
                            )