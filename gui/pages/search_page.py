from nicegui import ui

from .base_page import BasePage
from ..components.page_header import PageHeader
from ..components.results_renderer import ResultsRenderer

# Reuse the SAME validators used by the terminal IO Manager.
from io_manager_part2.location_validator import LocationValidator
from io_manager_part2.price_range_validator import PriceRangeValidator
from io_manager_part2.email_validator import EmailValidator
from io_manager_part2.weight_validator import WeightValidator


class SearchPage(BasePage):

    ROUTE = '/search'
    TITLE = 'Hotel Recommendation System - Find Hotels'

    PROFILE_TOTAL_POINTS = 100

    # Same order and keys as ConsoleView.
    WEIGHT_CRITERIA = (
        ('rating', 'Customer review rating'),
        ('price', 'Price'),
        ('location', 'Location'),
        ('amenities', 'Preferences'),
        ('bonus', 'Top-match bonus'),
    )

    def __init__(
        self,
        controller,
    ) -> None:

        super().__init__(controller)

        # -------------------------------------------------
        # Existing validators used by terminal
        # -------------------------------------------------

        self._location_validator = LocationValidator()
        self._price_validator = PriceRangeValidator()
        self._email_validator = EmailValidator()

        # -------------------------------------------------
        # Page areas
        # -------------------------------------------------

        self._search_form = None
        self._results_area = None

        self._details_stage = None
        self._profile_stage = None

        # -------------------------------------------------
        # Step indicator
        # -------------------------------------------------

        self._step_one = None
        self._step_two = None

        # -------------------------------------------------
        # Search input components
        # -------------------------------------------------

        self._destination = None
        self._email = None
        self._budget_min = None
        self._budget_max = None
        self._preferences = None

        # Validated Step 1 data
        self._search_details = {}

        # -------------------------------------------------
        # Profile
        # -------------------------------------------------

        self._profile = None
        self._custom_panel = None

        self._allowed_keys = set()
        self._active_criteria = []

        # Custom weight inputs
        self._weight_inputs = {}
        self._weight_sliders = {}
        self._criterion_status = {}
        self._syncing_weight = False

        self._total_label = None
        self._remaining_label = None
        self._not_applicable_label = None

        # Search summary shown in Step 2
        self._summary_area = None

        # Loading
        self._loading_dialog = None

    # =====================================================
    # RENDER PAGE
    # =====================================================

    def render(self) -> None:

        self._prepare_page()
        self._add_styles()

        with ui.column().classes(
            'relative w-full min-h-screen '
            'overflow-hidden '
            'bg-gradient-to-br '
            'from-purple-50 via-white to-blue-50'
        ):

            # -------------------------------------------------
            # Decorative background
            # -------------------------------------------------

            ui.element('div').classes(
                'absolute -top-28 -right-24 '
                'w-72 h-72 rounded-full '
                'bg-purple-200 blur-3xl '
                'search-glow'
            )

            ui.element('div').classes(
                'absolute -bottom-28 -left-20 '
                'w-80 h-80 rounded-full '
                'bg-blue-200 blur-3xl '
                'search-glow'
            )

            # -------------------------------------------------
            # Header
            # -------------------------------------------------

            with ui.element('div').classes(
                'relative z-10 w-full '
                'search-fade-1'
            ):

                PageHeader(
                    'Find Your Hotel',
                    (
                        'Tell us what you need and '
                        'we will rank the best matches.'
                    ),
                    '/menu',
                ).render()

            # -------------------------------------------------
            # Results area
            # -------------------------------------------------

            self._results_area = (
                ui.column().classes(
                    'relative z-10 '
                    'w-full max-w-6xl '
                    'mx-auto gap-5 px-6 pb-10'
                )
            )

            # -------------------------------------------------
            # Main search flow
            # -------------------------------------------------

            with ui.column().classes(
                'relative z-10 '
                'w-full max-w-5xl '
                'mx-auto px-6 pt-5 pb-12 '
                'gap-6'
            ) as self._search_form:

                self._build_step_indicator()

                # STEP 1
                with ui.column().classes(
                    'w-full gap-5 search-fade-2'
                ) as self._details_stage:

                    self._build_search_details()

                # STEP 2
                with ui.column().classes(
                    'w-full gap-5 search-fade-2'
                ) as self._profile_stage:

                    self._build_traveller_priorities()

                # Hide Step 2 initially.
                self._profile_stage.set_visibility(
                    False
                )

                self._build_loading_dialog()

    # =====================================================
    # STYLES
    # =====================================================

    def _add_styles(self) -> None:

        ui.add_head_html(
            '''
            <style>

                @keyframes searchFadeUp {
                    from {
                        opacity: 0;
                        transform: translateY(18px);
                    }

                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                @keyframes searchSoftPulse {
                    0%, 100% {
                        opacity: 0.20;
                        transform: scale(1);
                    }

                    50% {
                        opacity: 0.40;
                        transform: scale(1.08);
                    }
                }

                .search-fade-1 {
                    animation: searchFadeUp 0.5s ease-out;
                }

                .search-fade-2 {
                    animation: searchFadeUp 0.7s ease-out;
                }

                .search-glow {
                    animation:
                        searchSoftPulse
                        5s ease-in-out infinite;
                }

            </style>
            '''
        )

    # =====================================================
    # STEP INDICATOR
    # =====================================================

    def _build_step_indicator(self) -> None:

        with ui.row().classes(
            'w-full justify-center '
            'items-center gap-3 mb-1'
        ):

            self._step_one = (
                ui.badge(
                    'Search Details'
                )
                .props(
                    'color=primary'
                )
                .classes(
                    'px-4 py-2 text-sm'
                )
            )

            ui.icon(
                'arrow_forward',
                color='grey',
                size='1.1rem',
            )

            self._step_two = (
                ui.badge(
                    'Traveller Priorities'
                )
                .props(
                    'color=grey-4 '
                    'text-color=grey-7'
                )
                .classes(
                    'px-4 py-2 text-sm'
                )
            )

            ui.icon(
                'arrow_forward',
                color='grey',
                size='1.1rem',
            )

            ui.badge(
                'Recommendations'
            ).props(
                'color=grey-3 '
                'text-color=grey-6'
            ).classes(
                'px-4 py-2 text-sm'
            )

    # =====================================================
    # STEP 1 — HOTEL DETAILS
    # =====================================================

    def _build_search_details(self) -> None:

        with ui.card().classes(
            'w-full rounded-3xl p-7 '
            'shadow-sm '
            'border border-slate-100 '
            'bg-white/95'
        ):

            # -------------------------------------------------
            # Header
            # -------------------------------------------------

            with ui.row().classes(
                'items-center gap-4'
            ):

                with ui.element('div').classes(
                    'w-12 h-12 rounded-xl '
                    'bg-purple-50 '
                    'flex items-center justify-center'
                ):

                    ui.icon(
                        'search',
                        size='1.8rem',
                        color='primary',
                    )

                with ui.column().classes(
                    'gap-0'
                ):

                    ui.label(
                        'Hotel Search Details'
                    ).classes(
                        'text-2xl font-bold '
                        'text-slate-900'
                    )

                    ui.label(
                        'First, tell us about your stay.'
                    ).classes(
                        'text-sm text-slate-500'
                    )

            # -------------------------------------------------
            # Main inputs
            # -------------------------------------------------

            with ui.grid(
                columns=2
            ).classes(
                'w-full gap-5 mt-6 '
                'max-md:grid-cols-1'
            ):

                self._destination = (
                    ui.input(
                        'Destination country or city',
                        placeholder='e.g. Singapore',
                    )
                    .props('outlined')
                    .classes('w-full')
                )

                self._email = (
                    ui.input(
                        'Email address',
                        placeholder='e.g. hasi@gmail.com',
                    )
                    .props('outlined')
                    .classes('w-full')
                )

                self._budget_min = (
                    ui.number(
                        'Minimum budget per night (SGD)',
                        value=100,
                        min=1,
                    )
                    .props('outlined')
                    .classes('w-full')
                )

                self._budget_max = (
                    ui.number(
                        'Maximum budget per night (SGD)',
                        value=300,
                        min=1,
                    )
                    .props('outlined')
                    .classes('w-full')
                )

            # -------------------------------------------------
            # Preferences
            # -------------------------------------------------

            ui.label(
                'Describe your hotel preferences'
            ).classes(
                'font-semibold '
                'text-slate-800 mt-5'
            )

            ui.label(
                'For example: near public transport, '
                'breakfast included, quiet room '
                'and swimming pool.'
            ).classes(
                'text-sm text-slate-500'
            )

            self._preferences = (
                ui.textarea(
                    'Your preferences (optional)',
                    placeholder=(
                        'e.g. near Marina Bay Sands, '
                        'breakfast included and swimming pool'
                    ),
                )
                .props(
                    'outlined autogrow'
                )
                .classes(
                    'w-full mt-2'
                )
            )

            # -------------------------------------------------
            # Continue
            # -------------------------------------------------

            with ui.row().classes(
                'w-full justify-end mt-5'
            ):

                ui.button(
                    'Continue to Traveller Priorities',
                    icon='arrow_forward',
                    on_click=self._continue_to_profiles,
                ).props(
                    'unelevated rounded '
                    'color=primary size=lg'
                ).classes(
                    'px-7 shadow-sm '
                    'transition-all duration-300 '
                    'hover:-translate-y-1 '
                    'hover:shadow-md'
                )

    # =====================================================
    # COMPLETE STEP 1
    # =====================================================

    def _continue_to_profiles(self) -> None:

        # -------------------------------------------------
        # LOCATION
        # Uses SAME LocationValidator as terminal.
        # -------------------------------------------------

        destination = (
            self._destination.value
            or ''
        ).strip()

        (
            is_valid,
            error,
        ) = self._location_validator.validate(
            destination
        )

        if not is_valid:

            ui.notify(
                error,
                type='warning',
            )

            return

        # -------------------------------------------------
        # PRICE RANGE
        #
        # GUI has two boxes for nicer presentation,
        # but validation is still performed by the SAME
        # PriceRangeValidator as the terminal.
        # -------------------------------------------------

        minimum = (
            self._budget_min.value
        )

        maximum = (
            self._budget_max.value
        )

        price_text = (
            f'{minimum}-{maximum}'
        )

        (
            is_valid,
            error,
            price_range,
        ) = self._price_validator.validate(
            price_text
        )

        if not is_valid:

            ui.notify(
                error,
                type='warning',
            )

            return

        # -------------------------------------------------
        # EMAIL
        # Same EmailValidator as terminal.
        # -------------------------------------------------

        email = (
            self._email.value
            or ''
        ).strip()

        (
            is_valid,
            error,
        ) = self._email_validator.validate(
            email
        )

        if not is_valid:

            ui.notify(
                error,
                type='warning',
            )

            return

        # -------------------------------------------------
        # PREFERENCES
        # Same terminal rule.
        # -------------------------------------------------

        preferences = (
            self._preferences.value
            or ''
        ).strip()

        if len(
            preferences
        ) > 2000:

            ui.notify(
                'Preferences must not exceed '
                '2,000 characters.',
                type='warning',
            )

            return

        # -------------------------------------------------
        # Store the validated Step 1 result.
        #
        # NO AI CALL OCCURS HERE.
        # -------------------------------------------------

        self._search_details = {
            'destination': destination,
            'budget_min': price_range['min'],
            'budget_max': price_range['max'],
            'email': email,
            'preferences': preferences,
        }

        # -------------------------------------------------
        # SAME flow as app.py:
        #
        # user_prefs = ...
        # allowed_keys =
        #     logic_manager.available_weight_keys(user_prefs)
        # -------------------------------------------------

        self._allowed_keys = set(
            self._controller.logic_manager
            .available_weight_keys(
                preferences
            )
        )

        # ConsoleView performs this same mapping.
        if (
            'preferences'
            in self._allowed_keys
        ):

            self._allowed_keys.add(
                'amenities'
            )

        # Prepare custom fields BEFORE showing profiles.
        self._configure_custom_criteria()

        # Reset to terminal default:
        # press Enter = Balanced.
        self._profile.set_value(
            '1'
        )

        self._custom_panel.set_visibility(
            False
        )

        # Render submitted search summary.
        self._render_search_summary()

        # Move to Step 2.
        self._details_stage.set_visibility(
            False
        )

        self._profile_stage.set_visibility(
            True
        )

        self._set_step_two_active()

    # =====================================================
    # STEP 2 — TRAVELLER PRIORITIES
    # =====================================================

    def _build_traveller_priorities(self) -> None:

        # -------------------------------------------------
        # Submitted search summary
        # -------------------------------------------------

        self._summary_area = (
            ui.column().classes(
                'w-full'
            )
        )

        # -------------------------------------------------
        # Traveller profile card
        # -------------------------------------------------

        with ui.card().classes(
            'w-full rounded-3xl p-7 '
            'shadow-sm '
            'border border-purple-100 '
            'bg-white/95'
        ):

            with ui.row().classes(
                'items-center gap-4'
            ):

                with ui.element('div').classes(
                    'w-12 h-12 rounded-xl '
                    'bg-purple-50 '
                    'flex items-center justify-center'
                ):

                    ui.icon(
                        'tune',
                        size='1.8rem',
                        color='primary',
                    )

                with ui.column().classes(
                    'gap-0'
                ):

                    ui.label(
                        'Traveller Priorities'
                    ).classes(
                        'text-2xl font-bold '
                        'text-slate-900'
                    )

                    ui.label(
                        'Choose how hotels should '
                        'be scored. Every option '
                        'adds up to 100 points.'
                    ).classes(
                        'text-sm text-slate-500'
                    )

            # -------------------------------------------------
            # Profiles
            # -------------------------------------------------

            self._profile = (
                ui.radio(
                    {
                        '1': 'Balanced',
                        '2': 'Budget Focused',
                        '3': 'Quality Focused',
                        '4': 'Customisation',
                    },
                    value='1',
                )
                .props(
                    'inline'
                )
                .classes(
                    'mt-6'
                )
            )

            self._profile.on_value_change(
                self._profile_changed
            )

            # -------------------------------------------------
            # Custom profile
            # -------------------------------------------------

            with ui.column().classes(
                'w-full mt-5 '
                'rounded-2xl '
                'bg-gradient-to-br '
                'from-purple-50 to-blue-50 '
                'border border-purple-100 '
                'p-6 gap-4'
            ) as self._custom_panel:

                self._build_customisation()

            self._custom_panel.set_visibility(
                False
            )

            # -------------------------------------------------
            # Actions
            # -------------------------------------------------

            with ui.row().classes(
                'w-full justify-between '
                'items-center mt-6 '
                'flex-wrap gap-3'
            ):

                ui.button(
                    'Back to Search Details',
                    icon='arrow_back',
                    on_click=self._back_to_details,
                ).props(
                    'flat color=primary'
                )

                ui.button(
                    'Find My Hotels',
                    icon='travel_explore',
                    on_click=self._find_hotels,
                ).props(
                    'unelevated rounded '
                    'color=primary size=lg'
                ).classes(
                    'px-8 shadow-md '
                    'transition-all duration-300 '
                    'hover:-translate-y-1 '
                    'hover:shadow-lg'
                )

    # =====================================================
    # SEARCH SUMMARY
    # =====================================================

    def _render_search_summary(self) -> None:

        self._summary_area.clear()

        data = self._search_details

        with self._summary_area:

            with ui.card().classes(
                'w-full rounded-2xl p-5 '
                'shadow-none '
                'border border-slate-100 '
                'bg-white/80'
            ):

                with ui.row().classes(
                    'w-full justify-between '
                    'items-start flex-wrap gap-4'
                ):

                    with ui.column().classes(
                        'gap-1'
                    ):

                        with ui.row().classes(
                            'items-center gap-2'
                        ):

                            ui.icon(
                                'check_circle',
                                color='positive',
                            )

                            ui.label(
                                'Search details saved'
                            ).classes(
                                'font-bold '
                                'text-slate-900'
                            )

                        ui.label(
                            (
                                f"{data['destination']}  •  "
                                f"S${data['budget_min']:g}"
                                f"–S${data['budget_max']:g}"
                                " per night"
                            )
                        ).classes(
                            'text-sm text-slate-600'
                        )

                        ui.label(
                            data['email']
                        ).classes(
                            'text-sm text-slate-500'
                        )

                        if data[
                            'preferences'
                        ]:

                            ui.label(
                                (
                                    'Preferences: '
                                    + data[
                                        'preferences'
                                    ]
                                )
                            ).classes(
                                'text-sm text-slate-500'
                            )

                    ui.button(
                        'Edit',
                        icon='edit',
                        on_click=self._back_to_details,
                    ).props(
                        'flat color=primary'
                    )

    # =====================================================
    # CUSTOMISATION UI
    # =====================================================

    def _build_customisation(self) -> None:

        with ui.row().classes(
            'w-full justify-between '
            'items-start gap-4 flex-wrap'
        ):

            with ui.column().classes(
                'gap-1'
            ):

                ui.label(
                    'Customise Your Scoring'
                ).classes(
                    'text-xl font-bold '
                    'text-slate-900'
                )

                ui.label(
                    'Assign points to each applicable '
                    'criterion. They must add up '
                    'to exactly 100.'
                ).classes(
                    'text-sm text-slate-500'
                )

            with ui.column().classes(
                'items-end gap-0 '
                'bg-white rounded-xl '
                'px-4 py-2 '
                'border border-purple-100'
            ):

                self._total_label = (
                    ui.label(
                        'Total: 0 / 100'
                    ).classes(
                        'font-bold '
                        'text-purple-700'
                    )
                )

                self._remaining_label = (
                    ui.label(
                        '100 points left'
                    ).classes(
                        'text-xs text-slate-400'
                    )
                )

        # Same five criteria as terminal.
        for (
            key,
            label,
        ) in self.WEIGHT_CRITERIA:

            self._build_weight_input(
                key,
                label,
            )

        self._not_applicable_label = (
            ui.label('')
            .classes(
                'w-full '
                'bg-slate-100 '
                'text-slate-600 '
                'rounded-xl p-3 '
                'text-sm'
            )
        )

        self._not_applicable_label.set_visibility(
            False
        )

    # =====================================================
    # WEIGHT INPUT
    # =====================================================

    def _build_weight_input(
        self,
        key: str,
        label: str,
    ) -> None:

        with ui.card().classes(
            'w-full p-4 '
            'rounded-xl shadow-none '
            'border border-slate-100 '
            'bg-white'
        ):

            # -------------------------------------------------
            # Criterion name + explanation
            # -------------------------------------------------

            with ui.row().classes(
                'w-full justify-between '
                'items-start gap-4'
            ):

                with ui.column().classes(
                    'gap-1'
                ):

                    ui.label(
                        label
                    ).classes(
                        'font-semibold '
                        'text-slate-800'
                    )

                    status = (
                        ui.label(
                            'Available for this search'
                        ).classes(
                            'text-xs '
                            'text-emerald-600'
                        )
                    )

                    self._criterion_status[
                        key
                    ] = status

                ui.icon(
                    self._criterion_icon(
                        key
                    ),
                    color='primary',
                    size='1.3rem',
                )

            # -------------------------------------------------
            # Slider + number input
            # -------------------------------------------------

            with ui.row().classes(
                'w-full items-center '
                'gap-3 mt-3'
            ):

                ui.label(
                    '0'
                ).classes(
                    'text-xs text-slate-400'
                )

                slider = (
                    ui.slider(
                        min=0,
                        max=100,
                        step=1,
                        value=0,
                    )
                    .props(
                        'color=primary'
                    )
                    .classes(
                        'flex-grow'
                    )
                )

                ui.label(
                    '100'
                ).classes(
                    'text-xs text-slate-400'
                )

                weight_input = (
                    ui.number(
                        'Points',
                        value=0,
                        min=0,
                        max=100,
                        step=1,
                    )
                    .props(
                        'outlined dense'
                    )
                    .classes(
                        'w-28'
                    )
                )

            self._weight_sliders[
                key
            ] = slider

            self._weight_inputs[
                key
            ] = weight_input

            # Slider -> number box
            slider.on_value_change(
                lambda event, criterion=key:
                self._sync_weight(
                    criterion,
                    event.value,
                    'slider',
                )
            )

            # Number box -> slider
            weight_input.on_value_change(
                lambda event, criterion=key:
                self._sync_weight(
                    criterion,
                    event.value,
                    'input',
                )
            )

    def _criterion_icon(
        self,
        key: str,
    ) -> str:

        icons = {
            'rating': 'star',
            'price': 'payments',
            'location': 'location_on',
            'amenities': 'hotel_class',
            'bonus': 'workspace_premium',
        }

        return icons.get(
            key,
            'tune',
        )

    def _sync_weight(
        self,
        key: str,
        value,
        source: str,
    ) -> None:

        if self._syncing_weight:
            return

        self._syncing_weight = True

        try:

            try:

                points = int(
                    value
                    or 0
                )

            except (
                TypeError,
                ValueError,
            ):

                points = 0

            points = max(
                0,
                min(
                    100,
                    points,
                ),
            )

            slider = (
                self._weight_sliders[
                    key
                ]
            )

            number_input = (
                self._weight_inputs[
                    key
                ]
            )

            if source == 'slider':

                number_input.set_value(
                    points
                )

            else:

                slider.set_value(
                    points
                )

            self._update_total()

        finally:

            self._syncing_weight = False

    def _applicable_message(
        self,
        key: str,
    ) -> str:

        messages = {
            'rating': (
                'Available — customer review '
                'ratings can be scored.'
            ),
            'price': (
                'Available — hotel prices can be '
                'compared with your budget.'
            ),
            'location': (
                'Available — your request includes '
                'a location or proximity preference.'
            ),
            'amenities': (
                'Available — your request includes '
                'hotel preferences that can be '
                'checked against hotel data.'
            ),
            'bonus': (
                'Available — the top-match bonus '
                'can be evaluated for this search.'
            ),
        }

        return messages.get(
            key,
            'Available for this search.'
        )

    def _not_applicable_message(
        self,
        key: str,
    ) -> str:

        messages = {
            'location': (
                'Not used — no specific nearby '
                'place was identified in your request.'
            ),
            'amenities': (
                'Not used — no checkable hotel '
                'amenities were identified in your request.'
            ),
            'rating': (
                'Not used for this search.'
            ),
            'price': (
                'Not used for this search.'
            ),
            'bonus': (
                'Not used for this search.'
            ),
        }

        return messages.get(
            key,
            'Not used for this search.'
        )

    def _configure_custom_criteria(
        self,
    ) -> None:

        skipped = []

        self._active_criteria = []

        for (
            key,
            label,
        ) in self.WEIGHT_CRITERIA:

            field = (
                self._weight_inputs[
                    key
                ]
            )

            slider = (
                self._weight_sliders[
                    key
                ]
            )

            status = (
                self._criterion_status[
                    key
                ]
            )

            # Always initialise every criterion to 0.
            field.set_value(
                0
            )

            slider.set_value(
                0
            )

            if (
                key in self._allowed_keys
            ):

                self._active_criteria.append(
                    (
                        key,
                        label,
                    )
                )

                field.enable()
                slider.enable()

                status.set_text(
                    self._applicable_message(
                        key
                    )
                )

                status.classes(
                    replace=(
                        'text-xs '
                        'text-emerald-600'
                    )
                )

            else:

                # Exact terminal behaviour:
                # not applicable = automatically 0.
                field.disable()
                slider.disable()

                status.set_text(
                    self._not_applicable_message(
                        key
                    )
                )

                status.classes(
                    replace=(
                        'text-xs '
                        'text-slate-400'
                    )
                )

                skipped.append(
                    label.lower()
                )

        if skipped:

            self._not_applicable_label.set_text(
                (
                    'Automatically set to 0 because '
                    'they cannot be scored for this search: '
                    + ', '.join(
                        skipped
                    )
                    + '.'
                )
            )

            self._not_applicable_label.set_visibility(
                True
            )

        else:

            self._not_applicable_label.set_visibility(
                False
            )

        self._update_total()

    def _profile_changed(
        self,
        event,
    ) -> None:

        self._custom_panel.set_visibility(
            event.value == '4'
        )

    # =====================================================
    # CUSTOM TOTAL
    # =====================================================

    def _update_total(self) -> None:

        total = sum(
            int(
                field.value
                or 0
            )
            for field
            in self._weight_inputs.values()
        )

        remaining = (
            self.PROFILE_TOTAL_POINTS
            - total
        )

        self._total_label.set_text(
            f'Total: {total} / 100'
        )

        if remaining >= 0:

            self._remaining_label.set_text(
                f'{remaining} points left'
            )

        else:

            self._remaining_label.set_text(
                f'{abs(remaining)} points over'
            )

        if total == 100:

            self._total_label.classes(
                replace=(
                    'font-bold '
                    'text-emerald-600'
                )
            )

        elif total > 100:

            self._total_label.classes(
                replace=(
                    'font-bold '
                    'text-red-600'
                )
            )

        else:

            self._total_label.classes(
                replace=(
                    'font-bold '
                    'text-purple-700'
                )
            )

    # =====================================================
    # VALIDATE CUSTOM WEIGHTS
    # =====================================================

    def _get_custom_weights(
        self,
    ):

        # Terminal initialises all five to zero.
        weights = {
            key: 0
            for (
                key,
                _label,
            )
            in self.WEIGHT_CRITERIA
        }

        running = 0

        # Follow the exact same criterion order
        # as ConsoleView.
        for (
            key,
            label,
        ) in self._active_criteria:

            remaining = (
                self.PROFILE_TOTAL_POINTS
                - running
            )

            # Same validator used by terminal.
            validator = WeightValidator(
                remaining
            )

            value = int(
                self._weight_inputs[
                    key
                ].value
                or 0
            )

            (
                is_valid,
                error,
                points,
            ) = validator.validate(
                str(value)
            )

            if not is_valid:

                ui.notify(
                    f'{label}: {error}',
                    type='warning',
                )

                return None

            weights[
                key
            ] = points

            running += points

        # Same terminal rule.
        if (
            running
            != self.PROFILE_TOTAL_POINTS
        ):

            ui.notify(
                (
                    'Your weightages add up to '
                    f'{running}, not 100. '
                    f'{100 - running} point(s) '
                    'are still unassigned.'
                ),
                type='warning',
            )

            return None

        return weights

    # =====================================================
    # BACK TO STEP 1
    # =====================================================

    def _back_to_details(self) -> None:

        self._profile_stage.set_visibility(
            False
        )

        self._details_stage.set_visibility(
            True
        )

        self._set_step_one_active()

    # =====================================================
    # STEP STYLE
    # =====================================================

    def _set_step_one_active(self) -> None:

        self._step_one.props(
            'color=primary'
        )

        self._step_two.props(
            'color=grey-4 '
            'text-color=grey-7'
        )

    def _set_step_two_active(self) -> None:

        self._step_one.props(
            'color=positive'
        )

        self._step_two.props(
            'color=primary '
            'text-color=white'
        )

    # =====================================================
    # LOADING DIALOG
    # =====================================================

    def _build_loading_dialog(self) -> None:

        self._loading_dialog = (
            ui.dialog().props(
                'persistent'
            )
        )

        with self._loading_dialog:

            with ui.card().classes(
                'items-center p-8 '
                'rounded-3xl '
                'min-w-[360px]'
            ):

                with ui.element('div').classes(
                    'w-16 h-16 '
                    'rounded-2xl '
                    'bg-purple-50 '
                    'flex items-center '
                    'justify-center'
                ):

                    ui.icon(
                        'flight_takeoff',
                        size='2.6rem',
                        color='primary',
                    ).classes(
                        'animate-bounce'
                    )

                ui.spinner(
                    type='dots',
                    size='xl',
                    color='primary',
                )

                ui.label(
                    'Finding the best hotels '
                    'for you...'
                ).classes(
                    'text-xl font-bold '
                    'text-slate-900 '
                    'text-center'
                )

                ui.label(
                    'We are comparing your '
                    'preferences and traveller '
                    'priorities.'
                ).classes(
                    'text-sm text-slate-500 '
                    'text-center'
                )

    # =====================================================
    # FINAL SEARCH
    # =====================================================

    async def _find_hotels(self) -> None:

        # -------------------------------------------------
        # Determine weights.
        # -------------------------------------------------

        if (
            self._profile.value == '4'
        ):

            custom_weights = (
                self._get_custom_weights()
            )

            if (
                custom_weights
                is None
            ):

                return

        else:

            # Preset profiles do not use
            # custom weights.
            custom_weights = {
                key: 0
                for (
                    key,
                    _label,
                )
                in self.WEIGHT_CRITERIA
            }

        # -------------------------------------------------
        # Only NOW do we call the application search.
        #
        # This matches the terminal:
        #
        # mandatory inputs
        # → preferences
        # → profile
        # → AI
        # -------------------------------------------------

        self._loading_dialog.open()

        try:

            bundle = (
                await self._controller.search_hotels(

                    destination=(
                        self._search_details[
                            'destination'
                        ]
                    ),

                    budget_min=(
                        self._search_details[
                            'budget_min'
                        ]
                    ),

                    budget_max=(
                        self._search_details[
                            'budget_max'
                        ]
                    ),

                    email=(
                        self._search_details[
                            'email'
                        ]
                    ),

                    preferences=(
                        self._search_details[
                            'preferences'
                        ]
                    ),

                    profile_choice=(
                        self._profile.value
                    ),

                    custom_weights=(
                        custom_weights
                    ),
                )
            )

        except ValueError as error:

            ui.notify(
                str(error),
                type='negative',
            )

            return

        except Exception as error:

            ui.notify(
                str(error),
                type='negative',
            )

            return

        finally:

            self._loading_dialog.close()

        self._show_results(
            bundle
        )

    # =====================================================
    # RESULTS
    # =====================================================

    def _show_results(
        self,
        bundle: dict,
    ) -> None:

        self._search_form.set_visibility(
            False
        )

        self._results_area.clear()

        with self._results_area:

            with ui.row().classes(
                'w-full justify-between '
                'items-center flex-wrap '
                'pt-5'
            ):

                ui.button(
                    'Edit Search',
                    icon='arrow_back',
                    on_click=self._edit_search,
                ).props(
                    'flat color=primary'
                )

                ui.button(
                    'Main Menu',
                    icon='home',
                    on_click=lambda:
                    ui.navigate.to('/menu'),
                ).props(
                    'outline color=primary'
                )

            ResultsRenderer(
                bundle
            ).render()

    # =====================================================
    # EDIT SEARCH
    # =====================================================

    def _edit_search(self) -> None:

        self._results_area.clear()

        self._search_form.set_visibility(
            True
        )

        self._profile_stage.set_visibility(
            False
        )

        self._details_stage.set_visibility(
            True
        )

        self._set_step_one_active()
