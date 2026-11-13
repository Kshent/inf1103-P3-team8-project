from __future__ import annotations

from nicegui import ui

from .components import (
    menu_card,
    page_header,
    render_results,
    render_saved_records,
    setup_page,
)

from .gui_controller import GuiController


CUSTOM_WEIGHT_LABELS = {
    'rating': 'Customer review rating',
    'price': 'Price',
    'location': 'Location',
    'preferences': 'Preferences',
    'bonus': 'Bonus',
}


def register_pages(
    controller: GuiController,
) -> None:

    # =====================================================
    # HOME PAGE
    # =====================================================

    @ui.page('/')
    def home_page() -> None:

        setup_page()

        ui.page_title(
            'SmartStay'
        )

        with ui.column().classes(
            'w-full min-h-screen '
            'items-center justify-center px-6 '
            'bg-gradient-to-br '
            'from-purple-50 via-white '
            'to-indigo-50'
        ):

            with ui.card().classes(
                'w-full max-w-4xl p-12 '
                'items-center rounded-3xl '
                'shadow-xl border '
                'border-purple-100'
            ):

                with ui.element(
                    'div'
                ).classes(
                    'w-20 h-20 rounded-3xl '
                    'bg-purple-100 flex '
                    'items-center justify-center'
                ):

                    ui.icon(
                        'hotel',
                        size='3rem',
                        color='primary',
                    )

                ui.label(
                    'Welcome to SmartStay'
                ).classes(
                    'text-5xl font-bold '
                    'text-slate-900 '
                    'text-center mt-4'
                )

                ui.label(
                    'Find hotel recommendations '
                    'tailored to your budget, '
                    'preferences and traveller style.'
                ).classes(
                    'text-lg text-slate-500 '
                    'text-center max-w-2xl '
                    'leading-relaxed'
                )

                with ui.row().classes(
                    'gap-3 flex-wrap '
                    'justify-center mt-3'
                ):

                    ui.chip(
                        'AI-powered recommendations',
                        icon='auto_awesome',
                    )

                    ui.chip(
                        'Personalised scoring',
                        icon='tune',
                    )

                    ui.chip(
                        'Top 3 matches',
                        icon='workspace_premium',
                    )

                ui.button(
                    'Enter SmartStay',
                    icon='arrow_forward',
                    on_click=lambda:
                    ui.navigate.to('/menu'),
                ).props(
                    'unelevated rounded '
                    'color=primary size=lg'
                ).classes(
                    'mt-6 px-8'
                )

    # =====================================================
    # MAIN MENU
    # =====================================================

    @ui.page('/menu')
    def menu_page() -> None:

        setup_page()

        ui.page_title(
            'SmartStay - Main Menu'
        )

        page_header(
            'SmartStay',
            'Choose what you would like to do.',
            '/',
        )

        with ui.grid(
            columns=2
        ).classes(
            'w-full max-w-6xl mx-auto '
            'gap-6 p-6 max-md:grid-cols-1'
        ):

            menu_card(
                'travel_explore',
                'Find Hotels',
                (
                    'Search for hotels and '
                    'receive personalised '
                    'Top 3 recommendations.'
                ),
                'Start Search',
                '/search',
            )

            menu_card(
                'history',
                'Previous Records',
                (
                    'View hotel recommendations '
                    'saved under your email address.'
                ),
                'View Records',
                '/records',
            )

            menu_card(
                'admin_panel_settings',
                'Admin Login',
                (
                    'View all recommendation '
                    'records through the admin area.'
                ),
                'Admin Login',
                '/admin',
            )

            menu_card(
                'logout',
                'Exit',
                (
                    'Finish your SmartStay session '
                    'and return to the welcome screen.'
                ),
                'Exit SmartStay',
                '/goodbye',
            )

    # =====================================================
    # HOTEL SEARCH
    # =====================================================

    @ui.page('/search')
    def search_page() -> None:

        setup_page()

        ui.page_title(
            'SmartStay - Find Hotels'
        )

        page_header(
            'Find Your Hotel',
            (
                'Tell us what you need and '
                'we will rank the best matches.'
            ),
            '/menu',
        )

        # Results will later appear here.
        results_area = (
            ui.column().classes(
                'w-full max-w-6xl '
                'mx-auto gap-5 px-6 pb-10'
            )
        )

        # =================================================
        # SEARCH FORM
        # =================================================

        with ui.column().classes(
            'w-full max-w-5xl '
            'mx-auto px-6 pb-10'
        ) as search_form:

            # ---------------------------------------------
            # Basic details
            # ---------------------------------------------

            with ui.card().classes(
                'w-full rounded-3xl p-7 '
                'shadow-sm border '
                'border-slate-100'
            ):

                with ui.row().classes(
                    'items-center gap-3'
                ):

                    ui.icon(
                        'search',
                        size='2rem',
                        color='primary',
                    )

                    ui.label(
                        'Hotel Search Details'
                    ).classes(
                        'text-2xl font-bold '
                        'text-slate-900'
                    )

                with ui.grid(
                    columns=2
                ).classes(
                    'w-full gap-5 mt-4 '
                    'max-md:grid-cols-1'
                ):

                    destination = (
                        ui.input(
                            'Destination',
                            placeholder='e.g. Tokyo',
                        )
                        .props('outlined')
                        .classes('w-full')
                    )

                    email = (
                        ui.input(
                            'Email address',
                            placeholder='e.g. hasi@gmail.com',
                        )
                        .props('outlined')
                        .classes('w-full')
                    )

                    budget_min = (
                        ui.number(
                            'Minimum budget per night (SGD)',
                            value=100,
                            min=1,
                        )
                        .props('outlined')
                        .classes('w-full')
                    )

                    budget_max = (
                        ui.number(
                            'Maximum budget per night (SGD)',
                            value=300,
                            min=1,
                        )
                        .props('outlined')
                        .classes('w-full')
                    )

                preferences = (
                    ui.textarea(
                        'Hotel preferences (optional)',
                        placeholder=(
                            'e.g. Near Tokyo Tower, '
                            'close to shopping areas, '
                            'breakfast included'
                        ),
                    )
                    .props(
                        'outlined autogrow'
                    )
                    .classes(
                        'w-full mt-3'
                    )
                )

            # ---------------------------------------------
            # Traveller style
            # ---------------------------------------------

            with ui.card().classes(
                'w-full rounded-3xl p-7 '
                'shadow-sm border '
                'border-purple-100 mt-5'
            ):

                with ui.row().classes(
                    'items-center gap-3'
                ):

                    ui.icon(
                        'tune',
                        size='2rem',
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
                            'Choose how you want '
                            'hotels to be scored.'
                        ).classes(
                            'text-slate-500'
                        )

                profile = ui.radio(
                    {
                        '1': 'Balanced',
                        '2': 'Budget Focused',
                        '3': 'Quality Focused',
                        '4': 'Customisation',
                    },
                    value='1',
                ).props(
                    'inline'
                ).classes(
                    'mt-4'
                )

                # =========================================
                # CUSTOM SLIDERS
                # =========================================

                with ui.column().classes(
                    'w-full bg-purple-50 '
                    'rounded-2xl p-5 mt-3 gap-4'
                ) as custom_panel:

                    ui.label(
                        'Custom scoring weightages'
                    ).classes(
                        'text-lg font-bold '
                        'text-purple-900'
                    )

                    ui.label(
                        'Move the sliders until '
                        'the total is exactly 100.'
                    ).classes(
                        'text-sm text-purple-700'
                    )

                    sliders = {}

                    for (
                        key,
                        label,
                    ) in (
                        CUSTOM_WEIGHT_LABELS.items()
                    ):

                        with ui.column().classes(
                            'w-full gap-1'
                        ):

                            with ui.row().classes(
                                'w-full justify-between '
                                'items-center'
                            ):

                                ui.label(
                                    label
                                ).classes(
                                    'font-medium'
                                )

                                value_label = (
                                    ui.label(
                                        '0%'
                                    ).classes(
                                        'font-bold '
                                        'text-purple-700'
                                    )
                                )

                            slider = ui.slider(
                                min=0,
                                max=100,
                                step=5,
                                value=0,
                            ).props(
                                'label color=primary'
                            )

                            value_label.bind_text_from(
                                slider,
                                'value',
                                backward=lambda value:
                                f'{int(value)}%',
                            )

                            sliders[
                                key
                            ] = slider

                    total_label = ui.label(
                        'Total: 0 / 100'
                    ).classes(
                        'text-lg font-bold '
                        'text-purple-900'
                    )

                    def update_total() -> None:

                        total = sum(
                            int(
                                slider.value
                                or 0
                            )
                            for slider
                            in sliders.values()
                        )

                        total_label.set_text(
                            f'Total: {total} / 100'
                        )

                    for slider in sliders.values():

                        slider.on_value_change(
                            lambda _:
                            update_total()
                        )

                # Hide custom section by default
                custom_panel.set_visibility(
                    False
                )

                def profile_changed(
                    event,
                ) -> None:

                    custom_panel.set_visibility(
                        event.value == '4'
                    )

                profile.on_value_change(
                    profile_changed
                )

            # =============================================
            # LOADING DIALOG
            # =============================================

            with ui.dialog().props(
                'persistent'
            ) as loading_dialog:

                with ui.card().classes(
                    'items-center p-8 '
                    'rounded-3xl min-w-[340px]'
                ):

                    # Cute moving travel icon
                    ui.icon(
                        'flight_takeoff',
                        size='3.2rem',
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
                        'text-slate-900 text-center'
                    )

                    ui.label(
                        'We are comparing your '
                        'preferences and traveller '
                        'priorities.'
                    ).classes(
                        'text-sm text-slate-500 '
                        'text-center'
                    )

            # =============================================
            # SEARCH HANDLER
            # =============================================

            async def find_hotels() -> None:

                # Basic validation
                if not (
                    destination.value
                    or ''
                ).strip():

                    ui.notify(
                        'Please enter a destination.',
                        type='warning',
                    )

                    return

                if (
                    not (
                        email.value
                        or ''
                    ).strip()
                    or '@'
                    not in email.value
                ):

                    ui.notify(
                        'Please enter a valid '
                        'email address.',
                        type='warning',
                    )

                    return

                minimum = float(
                    budget_min.value
                    or 0
                )

                maximum = float(
                    budget_max.value
                    or 0
                )

                if (
                    minimum <= 0
                    or maximum <= 0
                    or minimum > maximum
                ):

                    ui.notify(
                        'Please enter a valid '
                        'budget range.',
                        type='warning',
                    )

                    return

                custom_weights = {
                    key:
                    int(
                        slider.value
                        or 0
                    )
                    for (
                        key,
                        slider,
                    )
                    in sliders.items()
                }

                if (
                    profile.value == '4'
                    and sum(
                        custom_weights.values()
                    )
                    != 100
                ):

                    ui.notify(
                        'Custom weightages must '
                        'add up to exactly 100.',
                        type='warning',
                    )

                    return

                # Show loading popup
                loading_dialog.open()

                try:

                    bundle = (
                        await controller.search_hotels(
                            destination=(
                                destination.value
                                or ''
                            ).strip(),

                            budget_min=minimum,

                            budget_max=maximum,

                            email=(
                                email.value
                                or ''
                            ).strip(),

                            preferences=(
                                preferences.value
                                or ''
                            ).strip(),

                            profile_choice=(
                                profile.value
                            ),

                            custom_weights=(
                                custom_weights
                            ),
                        )
                    )

                except ValueError as error:

                    ui.notify(
                        (
                            'Invalid scoring profile: '
                            f'{error}'
                        ),
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

                    loading_dialog.close()

                # Hide search form
                search_form.set_visibility(
                    False
                )

                # Clear previous results
                results_area.clear()

                # Render recommendations
                with results_area:

                    with ui.row().classes(
                        'w-full justify-between '
                        'items-center flex-wrap'
                    ):

                        ui.button(
                            'Edit Search',
                            icon='arrow_back',
                            on_click=lambda: (
                                results_area.clear(),
                                search_form.set_visibility(
                                    True
                                ),
                            ),
                        ).props(
                            'flat color=primary'
                        )

                        ui.button(
                            'Main Menu',
                            icon='home',
                            on_click=lambda:
                            ui.navigate.to(
                                '/menu'
                            ),
                        ).props(
                            'outline color=primary'
                        )

                    render_results(
                        bundle
                    )

            # Primary button
            ui.button(
                'Find My Hotels',
                icon='travel_explore',
                on_click=find_hotels,
            ).props(
                'unelevated rounded '
                'color=primary size=lg'
            ).classes(
                'mt-6 self-end px-8'
            )

    # =====================================================
    # PREVIOUS RECORDS
    # =====================================================

    @ui.page('/records')
    def records_page() -> None:

        setup_page()

        ui.page_title(
            'SmartStay - Previous Records'
        )

        page_header(
            'Previous Hotel Records',
            (
                'Search recommendations '
                'saved under your email.'
            ),
            '/menu',
        )

        with ui.column().classes(
            'w-full max-w-5xl '
            'mx-auto p-6 gap-4'
        ):

            with ui.card().classes(
                'w-full rounded-2xl p-5'
            ):

                email_input = (
                    ui.input(
                        'Email address',
                        placeholder='hasi@gmail.com',
                    )
                    .props('outlined')
                    .classes('w-full')
                )

                country_input = (
                    ui.input(
                        'Country filter (optional)',
                        placeholder='e.g. Japan',
                    )
                    .props('outlined')
                    .classes('w-full')
                )

                results = (
                    ui.column().classes(
                        'w-full gap-4'
                    )
                )

                def load_records() -> None:

                    email_value = (
                        email_input.value
                        or ''
                    ).strip()

                    if not email_value:

                        ui.notify(
                            'Please enter your email.',
                            type='warning',
                        )

                        return

                    records = (
                        controller.query_records(
                            email_value,
                            country_input.value
                            or '',
                        )
                    )

                    results.clear()

                    with results:

                        render_saved_records(
                            records
                        )

                ui.button(
                    'View Records',
                    icon='history',
                    on_click=load_records,
                ).props(
                    'unelevated color=primary'
                )

    # =====================================================
    # ADMIN
    # =====================================================

    @ui.page('/admin')
    def admin_page() -> None:

        setup_page()

        ui.page_title(
            'SmartStay - Admin'
        )

        page_header(
            'Admin Login',
            (
                'Restricted access to all '
                'saved recommendation records.'
            ),
            '/menu',
        )

        with ui.column().classes(
            'w-full max-w-xl '
            'mx-auto p-6 gap-4'
        ):

            with ui.card().classes(
                'w-full rounded-2xl p-6'
            ):

                username = (
                    ui.input(
                        'Username'
                    )
                    .props('outlined')
                    .classes('w-full')
                )

                password = (
                    ui.input(
                        'Password',
                        password=True,
                        password_toggle_button=True,
                    )
                    .props('outlined')
                    .classes('w-full')
                )

                admin_results = (
                    ui.column().classes(
                        'w-full gap-4 mt-4'
                    )
                )

                def login() -> None:

                    if not (
                        controller.admin_login(
                            username.value
                            or '',
                            password.value
                            or '',
                        )
                    ):

                        ui.notify(
                            'Incorrect username '
                            'or password.',
                            type='negative',
                        )

                        return

                    ui.notify(
                        'Login successful.',
                        type='positive',
                    )

                    records = (
                        controller.load_all_records()
                    )

                    admin_results.clear()

                    with admin_results:

                        render_saved_records(
                            records
                        )

                ui.button(
                    'Login',
                    icon='login',
                    on_click=login,
                ).props(
                    'unelevated color=primary'
                )

    # =====================================================
    # GOODBYE
    # =====================================================

    @ui.page('/goodbye')
    def goodbye_page() -> None:

        setup_page()

        ui.page_title(
            'SmartStay'
        )

        with ui.column().classes(
            'w-full min-h-screen '
            'items-center justify-center px-6 '
            'bg-gradient-to-br '
            'from-purple-50 to-indigo-50'
        ):

            ui.icon(
                'luggage',
                size='5rem',
                color='primary',
            )

            ui.label(
                'Thanks for using SmartStay!'
            ).classes(
                'text-4xl font-bold '
                'text-slate-900 text-center'
            )

            ui.label(
                'We hope your next stay '
                'is a great one.'
            ).classes(
                'text-lg text-slate-500'
            )

            ui.button(
                'Return Home',
                icon='home',
                on_click=lambda:
                ui.navigate.to('/'),
            ).props(
                'unelevated color=primary size=lg'
            )