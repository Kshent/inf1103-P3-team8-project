from nicegui import ui

from .base_page import BasePage


class GoodbyePage(BasePage):
    ROUTE = '/goodbye'
    TITLE = 'Hotel Recommendation System'

    def render(self) -> None:
        self._prepare_page()

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
                'Thanks for using Hotel Recommendation System!'
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
