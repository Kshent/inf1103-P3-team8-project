from nicegui import ui

from .base_page import BasePage
from ..components.menu_card import MenuCard
from ..components.page_header import PageHeader


class MenuPage(BasePage):

    ROUTE = '/menu'
    TITLE = 'Hotel Recommendation System - Main Menu'

    def render(self) -> None:

        self._prepare_page()

        # -------------------------------------------------
        # PAGE ANIMATIONS
        # -------------------------------------------------

        ui.add_head_html(
            '''
            <style>
                @keyframes menuFadeUp {
                    from {
                        opacity: 0;
                        transform: translateY(18px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                @keyframes menuSoftPulse {
                    0%, 100% {
                        opacity: 0.25;
                        transform: scale(1);
                    }
                    50% {
                        opacity: 0.45;
                        transform: scale(1.08);
                    }
                }

                .menu-fade-1 {
                    animation: menuFadeUp 0.5s ease-out;
                }

                .menu-fade-2 {
                    animation: menuFadeUp 0.75s ease-out;
                }

                .menu-fade-3 {
                    animation: menuFadeUp 0.95s ease-out;
                }

                .menu-glow {
                    animation: menuSoftPulse 5s ease-in-out infinite;
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

            # Decorative glow - top right
            ui.element(
                'div'
            ).classes(
                'absolute -top-28 -right-24 '
                'w-72 h-72 rounded-full '
                'bg-purple-200 blur-3xl '
                'menu-glow'
            )

            # Decorative glow - bottom left
            ui.element(
                'div'
            ).classes(
                'absolute -bottom-28 -left-20 '
                'w-80 h-80 rounded-full '
                'bg-blue-200 blur-3xl '
                'menu-glow'
            )

            # -------------------------------------------------
            # HEADER
            # -------------------------------------------------

            with ui.element(
                'div'
            ).classes(
                'relative z-10 w-full menu-fade-1'
            ):

                PageHeader(
                    'Hotel Recommendation System',
                    'Choose what you would like to do.',
                    '/',
                ).render()

                # Admin is intentionally a secondary action
                ui.button(
                    'Admin',
                    icon='admin_panel_settings',
                    on_click=lambda:
                    ui.navigate.to('/admin'),
                ).props(
                    'flat color=primary'
                ).classes(
                    'absolute top-6 right-8 '
                    'max-md:top-4 max-md:right-4'
                )

            # -------------------------------------------------
            # INTRO SECTION
            # -------------------------------------------------

            with ui.column().classes(
                'relative z-10 '
                'w-full max-w-6xl mx-auto '
                'px-6 pt-8 items-center '
                'menu-fade-1'
            ):

                with ui.element(
                    'div'
                ).classes(
                    'w-16 h-16 rounded-2xl '
                    'bg-gradient-to-br '
                    'from-purple-100 to-blue-100 '
                    'flex items-center justify-center '
                    'shadow-sm'
                ):

                    ui.icon(
                        'travel_explore',
                        size='2.3rem',
                        color='primary',
                    )

                ui.label(
                    'What would you like to do?'
                ).classes(
                    'text-3xl font-bold '
                    'text-slate-900 text-center mt-3'
                )

                ui.label(
                    'Start a new hotel search or '
                    'revisit your previous recommendations.'
                ).classes(
                    'text-base text-slate-500 '
                    'text-center max-w-2xl '
                    'leading-relaxed'
                )

            # -------------------------------------------------
            # MAIN USER ACTIONS
            # -------------------------------------------------

            with ui.grid(
                columns=2
            ).classes(
                'relative z-10 '
                'w-full max-w-4xl mx-auto '
                'gap-6 px-6 pt-10 '
                'max-md:grid-cols-1 '
                'menu-fade-2'
            ):

                MenuCard(
                    'travel_explore',
                    'Find Hotels',
                    (
                        'Search for hotels based on your '
                        'budget, preferences and traveller '
                        'priorities.'
                    ),
                    'Start Search',
                    '/search',
                ).render()

                MenuCard(
                    'history',
                    'Previous Records',
                    (
                        'View hotel recommendations '
                        'previously saved under your '
                        'email address.'
                    ),
                    'View Records',
                    '/records',
                ).render()

            # -------------------------------------------------
            # SECONDARY ACTIONS
            # -------------------------------------------------

            with ui.column().classes(
                'relative z-10 '
                'w-full items-center '
                'pt-8 pb-12 '
                'menu-fade-3'
            ):

                ui.separator().classes(
                    'w-full max-w-xl mb-5'
                )

                ui.button(
                    'Exit Session',
                    icon='logout',
                    on_click=lambda:
                    ui.navigate.to('/goodbye'),
                ).props(
                    'flat color=grey-7'
                )

                ui.label(
                    'You can return to the welcome page at any time.'
                ).classes(
                    'text-xs text-slate-400 mt-1'
                )