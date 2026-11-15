from nicegui import ui


class MenuCard:
    """Reusable card used by the main menu."""

    def __init__(
        self,
        icon: str,
        title: str,
        description: str,
        button_text: str,
        destination: str,
    ) -> None:
        self._icon = icon
        self._title = title
        self._description = description
        self._button_text = button_text
        self._destination = destination

    def render(self) -> None:
        with ui.card().classes(
            'w-full p-6 rounded-2xl shadow-sm '
            'border border-slate-100 '
            'hover:shadow-lg transition-all'
        ):
            with ui.row().classes(
                'items-center gap-3'
            ):
                ui.icon(
                    self._icon,
                    size='2.4rem',
                    color='primary',
                )

                ui.label(
                    self._title
                ).classes(
                    'text-xl font-bold text-slate-900'
                )

            ui.label(
                self._description
            ).classes(
                'text-slate-500 leading-relaxed '
                'min-h-[48px]'
            )

            ui.button(
                self._button_text,
                icon='arrow_forward',
                on_click=lambda:
                ui.navigate.to(self._destination),
            ).props(
                'unelevated rounded color=primary'
            ).classes(
                'mt-2'
            )
