from nicegui import ui


class SavedRecordsRenderer:
    """Render saved hotel recommendation records."""

    def __init__(
        self,
        records,
    ) -> None:

        self._records = records
        self._expansions = []

    # =====================================================
    # RENDER
    # =====================================================

    def render(self) -> None:

        self._expansions = []

        if not self._records:

            self._render_no_records()
            return

        for record in self._records:

            self._render_record(
                record
            )

    # =====================================================
    # NO RECORDS
    # =====================================================

    def _render_no_records(self) -> None:

        with ui.card().classes(
            'w-full items-center '
            'p-8 rounded-2xl '
            'shadow-none '
            'border border-slate-100 '
            'bg-white'
        ):

            ui.icon(
                'history',
                size='3rem',
                color='grey',
            )

            ui.label(
                'No saved hotel records found.'
            ).classes(
                'text-lg font-semibold '
                'text-slate-700'
            )

            ui.label(
                'Try another email address '
                'or country filter.'
            ).classes(
                'text-sm text-slate-500'
            )

    # =====================================================
    # ONE USER RECORD
    # =====================================================

    def _render_record(
        self,
        record: dict,
    ) -> None:

        email = record.get(
            'email',
            'Saved traveller',
        )

        searches = record.get(
            'searches',
            [],
        )

        with ui.card().classes(
            'w-full rounded-3xl p-6 '
            'shadow-sm '
            'border border-slate-100 '
            'bg-white/95'
        ):

            # -------------------------------------------------
            # Email heading
            # -------------------------------------------------

            with ui.row().classes(
                'w-full justify-between '
                'items-center flex-wrap gap-3'
            ):

                with ui.row().classes(
                    'items-center gap-3'
                ):

                    with ui.element(
                        'div'
                    ).classes(
                        'w-10 h-10 rounded-xl '
                        'bg-purple-50 '
                        'flex items-center '
                        'justify-center'
                    ):

                        ui.icon(
                            'person',
                            color='primary',
                        )

                    with ui.column().classes(
                        'gap-0'
                    ):

                        ui.label(
                            email
                        ).classes(
                            'text-lg font-bold '
                            'text-slate-900'
                        )

                        ui.label(
                            (
                                f'{len(searches)} '
                                f'saved search'
                                f'{"es" if len(searches) != 1 else ""}'
                            )
                        ).classes(
                            'text-sm text-slate-500'
                        )

            ui.separator().classes(
                'my-3'
            )

            # -------------------------------------------------
            # Searches
            # -------------------------------------------------

            for index, hotels in enumerate(
                searches,
                start=1,
            ):

                self._render_search(
                    index,
                    hotels,
                )

    # =====================================================
    # ONE SEARCH
    # =====================================================

    def _render_search(
        self,
        index: int,
        hotels,
    ) -> None:

        expansion = (
            ui.expansion(
                (
                    f'Search {index} '
                    f'• {len(hotels)} '
                    f'hotel'
                    f'{"s" if len(hotels) != 1 else ""}'
                ),
                icon='history',
            )
            .classes(
                'w-full '
                'rounded-2xl '
                'border border-slate-100 '
                'bg-slate-50 mb-3'
            )
        )

        self._expansions.append(
            expansion
        )

        with expansion:

            with ui.column().classes(
                'w-full gap-4 py-2'
            ):

                for number, hotel in enumerate(
                    hotels,
                    start=1,
                ):

                    self._render_hotel(
                        number,
                        hotel,
                    )

    # =====================================================
    # ONE HOTEL
    # =====================================================

    def _render_hotel(
        self,
        number: int,
        hotel: dict,
    ) -> None:

        name = hotel.get(
            'name',
            'Hotel',
        )

        city = hotel.get(
            'city',
            '',
        )

        country = hotel.get(
            'country',
            '',
        )

        price = hotel.get(
            'price_per_night_sgd',
        )

        rating = hotel.get(
            'rating',
        )

        amenities = (
            hotel.get(
                'amenities'
            )
            or []
        )

        distances = (
            hotel.get(
                'distance_to_preferences'
            )
            or []
        )

        nearby_food = (
            hotel.get(
                'nearby_food'
            )
            or []
        )

        activities = (
            hotel.get(
                'nearby_activities'
            )
            or []
        )

        with ui.card().classes(
            'w-full rounded-2xl p-5 '
            'shadow-none '
            'border border-slate-200 '
            'bg-white'
        ):

            # -------------------------------------------------
            # Hotel heading
            # -------------------------------------------------

            with ui.row().classes(
                'w-full justify-between '
                'items-start gap-4 flex-wrap'
            ):

                with ui.row().classes(
                    'items-start gap-3'
                ):

                    with ui.element(
                        'div'
                    ).classes(
                        'w-9 h-9 rounded-full '
                        'bg-purple-100 '
                        'text-purple-700 '
                        'flex items-center '
                        'justify-center '
                        'font-bold'
                    ):

                        ui.label(
                            str(number)
                        )

                    with ui.column().classes(
                        'gap-1'
                    ):

                        ui.label(
                            name
                        ).classes(
                            'text-lg font-bold '
                            'text-slate-900'
                        )

                        with ui.row().classes(
                            'items-center gap-1'
                        ):

                            ui.icon(
                                'location_on',
                                size='1rem',
                                color='grey',
                            )

                            ui.label(
                                self._location_text(
                                    city,
                                    country,
                                )
                            ).classes(
                                'text-sm '
                                'text-slate-500'
                            )

                # Price + rating
                with ui.row().classes(
                    'items-center gap-2 '
                    'flex-wrap'
                ):

                    if price is not None:

                        ui.chip(
                            (
                                f'S${price:g} '
                                'per night'
                            ),
                            icon='payments',
                        ).props(
                            'color=purple-1 '
                            'text-color=purple-9'
                        )

                    if rating is not None:

                        ui.chip(
                            f'{rating} / 5',
                            icon='star',
                        ).props(
                            'color=amber-1 '
                            'text-color=amber-9'
                        )

            # -------------------------------------------------
            # Distance to requested places
            # -------------------------------------------------

            if distances:

                ui.separator().classes(
                    'my-2'
                )

                self._section_title(
                    'Distance to Requested Places',
                    'location_on',
                )

                with ui.row().classes(
                    'w-full gap-2 '
                    'flex-wrap'
                ):

                    for distance in distances:

                        ui.chip(
                            self._distance_text(
                                distance
                            ),
                            icon='near_me',
                        ).props(
                            'outline color=primary'
                        )

            # -------------------------------------------------
            # Amenities
            # -------------------------------------------------

            if amenities:

                ui.separator().classes(
                    'my-2'
                )

                self._section_title(
                    'Amenities',
                    'hotel_class',
                )

                with ui.row().classes(
                    'w-full gap-2 '
                    'flex-wrap'
                ):

                    for amenity in amenities:

                        ui.chip(
                            str(
                                amenity
                            )
                        ).props(
                            'color=grey-2 '
                            'text-color=grey-9'
                        )

            # -------------------------------------------------
            # Nearby information
            # -------------------------------------------------

            ui.separator().classes(
                'my-2'
            )

            with ui.grid(
                columns=2
            ).classes(
                'w-full gap-4 '
                'max-md:grid-cols-1'
            ):

                # ---------------------------------------------
                # Nearby food
                # ---------------------------------------------

                with ui.card().classes(
                    'w-full rounded-xl '
                    'shadow-none '
                    'bg-slate-50 p-4'
                ):

                    self._section_title(
                        'Nearby Food',
                        'restaurant',
                    )

                    if nearby_food:

                        with ui.column().classes(
                            'gap-2 mt-2'
                        ):

                            for food in nearby_food:

                                with ui.row().classes(
                                    'items-start gap-2'
                                ):

                                    ui.icon(
                                        'circle',
                                        size='0.4rem',
                                        color='primary',
                                    ).classes(
                                        'mt-2'
                                    )

                                    ui.label(
                                        str(
                                            food
                                        )
                                    ).classes(
                                        'text-sm '
                                        'text-slate-600'
                                    )

                    else:

                        ui.label(
                            'Not listed'
                        ).classes(
                            'text-sm '
                            'text-slate-400 mt-2'
                        )

                # ---------------------------------------------
                # Nearby activities
                # ---------------------------------------------

                with ui.card().classes(
                    'w-full rounded-xl '
                    'shadow-none '
                    'bg-slate-50 p-4'
                ):

                    self._section_title(
                        'Nearby Activities',
                        'local_activity',
                    )

                    if activities:

                        with ui.column().classes(
                            'gap-2 mt-2'
                        ):

                            for activity in activities:

                                with ui.row().classes(
                                    'items-start gap-2'
                                ):

                                    ui.icon(
                                        'circle',
                                        size='0.4rem',
                                        color='primary',
                                    ).classes(
                                        'mt-2'
                                    )

                                    ui.label(
                                        self._activity_text(
                                            activity
                                        )
                                    ).classes(
                                        'text-sm '
                                        'text-slate-600'
                                    )

                    else:

                        ui.label(
                            'Not listed'
                        ).classes(
                            'text-sm '
                            'text-slate-400 mt-2'
                        )

    # =====================================================
    # SECTION HEADING
    # =====================================================

    def _section_title(
        self,
        title: str,
        icon: str,
    ) -> None:

        with ui.row().classes(
            'items-center gap-2'
        ):

            ui.icon(
                icon,
                size='1.1rem',
                color='primary',
            )

            ui.label(
                title
            ).classes(
                'font-semibold '
                'text-slate-700'
            )

    # =====================================================
    # LOCATION FORMAT
    # =====================================================

    def _location_text(
        self,
        city,
        country,
    ) -> str:

        parts = [
            str(value)
            for value in (
                city,
                country,
            )
            if value
        ]

        if not parts:
            return 'Location not listed'

        return ', '.join(
            parts
        )

    # =====================================================
    # DISTANCE FORMAT
    # =====================================================

    def _distance_text(
        self,
        distance,
    ) -> str:

        if isinstance(
            distance,
            dict,
        ):

            target = distance.get(
                'target',
                'Requested place',
            )

            metres = distance.get(
                'distance_m'
            )

            if metres is not None:

                return (
                    f'{target}: '
                    f'{metres:g} m'
                )

            return str(
                target
            )

        # Supports older saved records.
        return str(
            distance
        )

    # =====================================================
    # ACTIVITY FORMAT
    # =====================================================

    def _activity_text(
        self,
        activity,
    ) -> str:

        if isinstance(
            activity,
            dict,
        ):

            name = activity.get(
                'name',
                'Activity',
            )

            distance = activity.get(
                'distance_m'
            )

            if distance is not None:

                return (
                    f'{name} '
                    f'({distance:g} m)'
                )

            return str(
                name
            )

        # Supports older saved records.
        return str(
            activity
        )

    # =====================================================
    # EXPAND ALL
    # =====================================================

    def expand_all(self) -> None:

        for expansion in self._expansions:

            expansion.set_value(
                True
            )

    # =====================================================
    # COLLAPSE ALL
    # =====================================================

    def collapse_all(self) -> None:

        for expansion in self._expansions:

            expansion.set_value(
                False
            )