from nicegui import ui

from .base_page import BasePage
from ..components.page_header import PageHeader
from ..components.saved_records_renderer import SavedRecordsRenderer
from io_manager_part2.email_validator import EmailValidator
from io_manager_part2.country_search_validator import CountrySearchValidator


class RecordsPage(BasePage):

    ROUTE = '/records'
    TITLE = 'Hotel Recommendation System - Previous Records'

    def __init__(
        self,
        controller,
    ) -> None:

        super().__init__(controller)

        self._email_input = None
        self._country_input = None
        self._results_area = None
        self._email_validator = EmailValidator()
        self._country_validator = CountrySearchValidator()

    # =====================================================
    # RENDER
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
                'records-glow'
            )

            ui.element('div').classes(
                'absolute -bottom-28 -left-20 '
                'w-80 h-80 rounded-full '
                'bg-blue-200 blur-3xl '
                'records-glow'
            )

            # -------------------------------------------------
            # Header
            # -------------------------------------------------

            with ui.element('div').classes(
                'relative z-10 w-full '
                'records-fade-1'
            ):

                PageHeader(
                    'Previous Hotel Records',
                    (
                        'View recommendations previously '
                        'saved under your email.'
                    ),
                    '/menu',
                ).render()

            # -------------------------------------------------
            # Main content
            # -------------------------------------------------

            with ui.column().classes(
                'relative z-10 '
                'w-full max-w-5xl '
                'mx-auto px-6 pt-6 pb-12 '
                'gap-6 records-fade-2'
            ):

                self._build_search_card()

                self._results_area = (
                    ui.column().classes(
                        'w-full gap-5'
                    )
                )

    # =====================================================
    # STYLES
    # =====================================================

    def _add_styles(self) -> None:

        ui.add_head_html(
            '''
            <style>

                @keyframes recordsFadeUp {
                    from {
                        opacity: 0;
                        transform: translateY(18px);
                    }

                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                @keyframes recordsSoftPulse {
                    0%, 100% {
                        opacity: 0.20;
                        transform: scale(1);
                    }

                    50% {
                        opacity: 0.40;
                        transform: scale(1.08);
                    }
                }

                .records-fade-1 {
                    animation:
                        recordsFadeUp 0.5s ease-out;
                }

                .records-fade-2 {
                    animation:
                        recordsFadeUp 0.7s ease-out;
                }

                .records-glow {
                    animation:
                        recordsSoftPulse
                        5s ease-in-out infinite;
                }

            </style>
            '''
        )

    # =====================================================
    # SEARCH CARD
    # =====================================================

    def _build_search_card(self) -> None:

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
                        'history',
                        size='1.8rem',
                        color='primary',
                    )

                with ui.column().classes(
                    'gap-0'
                ):

                    ui.label(
                        'Find Your Saved Recommendations'
                    ).classes(
                        'text-2xl font-bold '
                        'text-slate-900'
                    )

                    ui.label(
                        'Enter the email used for your '
                        'hotel search.'
                    ).classes(
                        'text-sm text-slate-500'
                    )

            # -------------------------------------------------
            # Information box
            # -------------------------------------------------

            with ui.row().classes(
                'w-full items-start gap-3 '
                'bg-purple-50 '
                'border border-purple-100 '
                'rounded-2xl p-4 mt-6'
            ):

                ui.icon(
                    'info',
                    color='primary',
                    size='1.2rem',
                )

                with ui.column().classes(
                    'gap-1'
                ):

                    ui.label(
                        'Looking for a specific trip?'
                    ).classes(
                        'text-sm font-semibold '
                        'text-slate-700'
                    )

                    ui.label(
                        'Leave the country filter empty '
                        'to view all recommendations, '
                        'or enter a country to narrow '
                        'the results.'
                    ).classes(
                        'text-sm text-slate-500 '
                        'leading-relaxed'
                    )

            # -------------------------------------------------
            # Inputs
            # -------------------------------------------------

            with ui.grid(
                columns=2
            ).classes(
                'w-full gap-5 mt-6 '
                'max-md:grid-cols-1'
            ):

                self._email_input = (
                    ui.input(
                        'Email address',
                        placeholder='e.g. hasi@gmail.com',
                    )
                    .props(
                        'outlined'
                    )
                    .classes(
                        'w-full'
                    )
                )

                self._country_input = (
                    ui.input(
                        'Country filter (optional)',
                        placeholder='e.g. Japan',
                    )
                    .props(
                        'outlined clearable'
                    )
                    .classes(
                        'w-full'
                    )
                )

            # -------------------------------------------------
            # Action
            # -------------------------------------------------

            with ui.row().classes(
                'w-full justify-end mt-5'
            ):

                ui.button(
                    'View Records',
                    icon='history',
                    on_click=self._load_records,
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
    # LOAD RECORDS
    # =====================================================

    def _load_records(self) -> None:

        email_value = (
            self._email_input.value
            or ''
        ).strip()

        country_value = (
            self._country_input.value
            or ''
        ).strip()

        # -------------------------------------------------
        # EMAIL VALIDATION
        # Same validator as terminal
        # -------------------------------------------------

        is_valid, error = (
            self._email_validator.validate(
                email_value
            )
        )

        if not is_valid:

            ui.notify(
                error,
                type='warning',
            )

            return

        # -------------------------------------------------
        # COUNTRY VALIDATION
        # Optional in GUI
        # -------------------------------------------------

        if country_value:

            is_valid, error = (
                self._country_validator.validate(
                    country_value
                )
            )

            if not is_valid:

                ui.notify(
                    error,
                    type='warning',
                )

                return

        # -------------------------------------------------
        # EXISTING RECORD QUERY
        # -------------------------------------------------

        records = (
            self._controller.query_records(
                email_value,
                country_value,
            )
        )

        self._results_area.clear()

        # -------------------------------------------------
        # RENDER RESULTS
        # -------------------------------------------------

        with self._results_area:

            with ui.row().classes(
                'w-full justify-between '
                'items-center flex-wrap gap-3'
            ):

                with ui.column().classes(
                    'gap-0'
                ):

                    ui.label(
                        'Saved Recommendations'
                    ).classes(
                        'text-2xl font-bold '
                        'text-slate-900'
                    )

                    if country_value:

                        ui.label(
                            (
                                'Showing records matching '
                                f'"{country_value}".'
                            )
                        ).classes(
                            'text-sm text-slate-500'
                        )

                    else:

                        ui.label(
                            'Showing all saved searches '
                            'for this email.'
                        ).classes(
                            'text-sm text-slate-500'
                        )

                ui.button(
                    'Clear',
                    icon='edit',
                    on_click=self._clear_results,
                ).props(
                    'flat color=primary'
                )

            # -------------------------------------------------
            # FULL RECORDS RENDERER
            # -------------------------------------------------

            renderer = SavedRecordsRenderer(
                records
            )

            # -------------------------------------------------
            # EXPAND / COLLAPSE
            # -------------------------------------------------

            if records:

                with ui.row().classes(
                    'w-full justify-end '
                    'items-center gap-2'
                ):

                    ui.button(
                        'Expand All',
                        icon='unfold_more',
                        on_click=renderer.expand_all,
                    ).props(
                        'outline color=primary'
                    )

                    ui.button(
                        'Collapse All',
                        icon='unfold_less',
                        on_click=renderer.collapse_all,
                    ).props(
                        'flat color=primary'
                    )

            renderer.render()

    # =====================================================
    # CLEAR RESULTS
    # =====================================================

    def _clear_results(self) -> None:

        self._results_area.clear()