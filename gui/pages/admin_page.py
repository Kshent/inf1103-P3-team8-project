from nicegui import ui

from .base_page import BasePage
from ..components.page_header import PageHeader
from ..components.saved_records_renderer import SavedRecordsRenderer


class AdminPage(BasePage):

    ROUTE = '/admin'
    TITLE = 'Hotel Recommendation System - Admin'

    def __init__(self, controller) -> None:
        super().__init__(controller)

        self._login_section = None
        self._dashboard_section = None

        self._username = None
        self._password = None

    def render(self) -> None:

        self._prepare_page()

        # -------------------------------------------------
        # ANIMATIONS
        # -------------------------------------------------

        ui.add_head_html(
            '''
            <style>
                @keyframes adminFadeUp {
                    from {
                        opacity: 0;
                        transform: translateY(18px);
                    }

                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                @keyframes adminGlow {
                    0%, 100% {
                        opacity: 0.20;
                        transform: scale(1);
                    }

                    50% {
                        opacity: 0.40;
                        transform: scale(1.08);
                    }
                }

                .admin-fade {
                    animation: adminFadeUp 0.6s ease-out;
                }

                .admin-glow {
                    animation: adminGlow 5s ease-in-out infinite;
                }
            </style>
            '''
        )

        # -------------------------------------------------
        # PAGE BACKGROUND
        # -------------------------------------------------

        with ui.column().classes(
            'relative w-full min-h-screen '
            'overflow-hidden '
            'bg-gradient-to-br '
            'from-purple-50 via-white to-blue-50'
        ):

            ui.element(
                'div'
            ).classes(
                'absolute -top-28 -right-24 '
                'w-72 h-72 rounded-full '
                'bg-purple-200 blur-3xl '
                'admin-glow'
            )

            ui.element(
                'div'
            ).classes(
                'absolute -bottom-28 -left-20 '
                'w-80 h-80 rounded-full '
                'bg-blue-200 blur-3xl '
                'admin-glow'
            )

            # -------------------------------------------------
            # HEADER
            # -------------------------------------------------

            with ui.element(
                'div'
            ).classes(
                'relative z-10 w-full'
            ):

                PageHeader(
                    'Admin Page',
                    (
                        'Secure access to all saved '
                        'hotel recommendation records.'
                    ),
                    '/menu',
                ).render()

            # -------------------------------------------------
            # LOGIN SECTION
            # -------------------------------------------------

            self._login_section = (
                ui.column().classes(
                    'relative z-10 '
                    'w-full items-center '
                    'px-6 pt-10 pb-12 '
                    'admin-fade'
                )
            )

            with self._login_section:

                with ui.card().classes(
                    'w-full max-w-lg '
                    'rounded-3xl p-8 '
                    'border border-purple-100 '
                    'shadow-lg bg-white'
                ):

                    # Login icon
                    with ui.element(
                        'div'
                    ).classes(
                        'w-16 h-16 rounded-2xl '
                        'bg-gradient-to-br '
                        'from-purple-100 to-blue-100 '
                        'flex items-center justify-center '
                        'mx-auto'
                    ):

                        ui.icon(
                            'admin_panel_settings',
                            size='2.3rem',
                            color='primary',
                        )

                    ui.label(
                        'Administrator Login'
                    ).classes(
                        'text-2xl font-bold '
                        'text-slate-900 '
                        'text-center mt-4'
                    )

                    ui.label(
                        'Sign in to view all recommendation '
                        'records stored by the system.'
                    ).classes(
                        'text-sm text-slate-500 '
                        'text-center leading-relaxed mb-5'
                    )

                    # Username
                    self._username = (
                        ui.input(
                            'Username',
                            placeholder='Enter admin username',
                        )
                        .props(
                            'outlined'
                        )
                        .classes(
                            'w-full'
                        )
                    )

                    # Password
                    self._password = (
                        ui.input(
                            'Password',
                            placeholder='Enter admin password',
                            password=True,
                            password_toggle_button=True,
                        )
                        .props(
                            'outlined'
                        )
                        .classes(
                            'w-full'
                        )
                    )

                    ui.button(
                        'Sign In',
                        icon='login',
                        on_click=self._login,
                    ).props(
                        'unelevated rounded '
                        'color=primary size=lg'
                    ).classes(
                        'w-full mt-4'
                    )

                    with ui.row().classes(
                        'w-full items-center '
                        'justify-center gap-2 mt-3'
                    ):

                        ui.icon(
                            'lock',
                            size='1rem',
                            color='grey',
                        )

                        ui.label(
                            'Restricted administrator access'
                        ).classes(
                            'text-xs text-slate-400'
                        )

            # -------------------------------------------------
            # DASHBOARD SECTION
            # -------------------------------------------------

            self._dashboard_section = (
                ui.column().classes(
                    'relative z-10 '
                    'w-full max-w-6xl mx-auto '
                    'px-6 pt-6 pb-12 gap-5 '
                    'admin-fade'
                )
            )

            self._dashboard_section.set_visibility(
                False
            )

    # =====================================================
    # LOGIN
    # =====================================================

    def _login(self) -> None:

        username = (
            self._username.value
            or ''
        ).strip()

        password = (
            self._password.value
            or ''
        )

        if not username:

            ui.notify(
                'Please enter your username.',
                type='warning',
            )

            return

        if not password:

            ui.notify(
                'Please enter your password.',
                type='warning',
            )

            return

        if not self._controller.admin_login(
            username,
            password,
        ):

            ui.notify(
                'Incorrect username or password.',
                type='negative',
            )

            return

        ui.notify(
            'Login successful.',
            type='positive',
        )

        self._show_dashboard()

    # =====================================================
    # ADMIN DASHBOARD
    # =====================================================

    def _show_dashboard(self) -> None:

        self._login_section.set_visibility(
            False
        )

        self._dashboard_section.set_visibility(
            True
        )

        records = (
            self._controller.load_all_records()
        )

        self._dashboard_section.clear()

        with self._dashboard_section:

            # -------------------------------------------------
            # DASHBOARD HEADER
            # -------------------------------------------------

            with ui.row().classes(
                'w-full justify-between '
                'items-center flex-wrap gap-4'
            ):

                with ui.column().classes(
                    'gap-1'
                ):

                    ui.label(
                        'Stored Recommendation Records'
                    ).classes(
                        'text-3xl font-bold '
                        'text-slate-900'
                    )

                    ui.label(
                        'View recommendation searches '
                        'saved by all users.'
                    ).classes(
                        'text-slate-500'
                    )

                ui.button(
                    'Sign Out',
                    icon='logout',
                    on_click=self._logout,
                ).props(
                    'outline color=primary'
                )

            # -------------------------------------------------
            # SUMMARY
            # -------------------------------------------------

            user_count = len(
                records
            )

            search_count = sum(
                len(
                    record.get(
                        'searches',
                        [],
                    )
                )
                for record in records
            )

            hotel_count = sum(
                len(
                    hotels
                )
                for record in records
                for hotels in record.get(
                    'searches',
                    [],
                )
            )

            with ui.grid(
                columns=3
            ).classes(
                'w-full gap-4 '
                'max-md:grid-cols-1'
            ):

                self._summary_card(
                    'people',
                    'Users',
                    user_count,
                )

                self._summary_card(
                    'history',
                    'Searches',
                    search_count,
                )

                self._summary_card(
                    'hotel',
                    'Hotels Saved',
                    hotel_count,
                )

            # -------------------------------------------------
            # RECORDS
            # -------------------------------------------------

            ui.label(
                'Saved Records'
            ).classes(
                'text-xl font-bold '
                'text-slate-900 mt-3'
            )

            SavedRecordsRenderer(
                records
            ).render()

    def _summary_card(
        self,
        icon: str,
        label: str,
        value: int,
    ) -> None:

        with ui.card().classes(
            'w-full p-5 rounded-2xl '
            'shadow-none '
            'border border-purple-100 '
            'bg-white'
        ):

            with ui.row().classes(
                'items-center gap-4'
            ):

                with ui.element(
                    'div'
                ).classes(
                    'w-12 h-12 rounded-xl '
                    'bg-purple-50 '
                    'flex items-center justify-center'
                ):

                    ui.icon(
                        icon,
                        size='1.7rem',
                        color='primary',
                    )

                with ui.column().classes(
                    'gap-0'
                ):

                    ui.label(
                        str(value)
                    ).classes(
                        'text-2xl font-bold '
                        'text-slate-900'
                    )

                    ui.label(
                        label
                    ).classes(
                        'text-sm text-slate-500'
                    )

    # =====================================================
    # LOGOUT
    # =====================================================

    def _logout(self) -> None:

        self._username.value = ''
        self._password.value = ''

        self._dashboard_section.set_visibility(
            False
        )

        self._login_section.set_visibility(
            True
        )

        ui.notify(
            'Signed out successfully.',
            type='info',
        )