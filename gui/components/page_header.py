from nicegui import ui


class PageHeader:
    """Reusable page heading with optional back navigation."""

    def __init__(
        self,
        title: str,
        subtitle: str = '',
        back_to: str | None = None,
    ) -> None:
        self._title = title
        self._subtitle = subtitle
        self._back_to = back_to

    def render(self) -> None:
        with ui.row().classes(
            'w-full max-w-6xl mx-auto '
            'items-center gap-4 px-6 pt-6'
        ):
            if self._back_to:
                ui.button(
                    icon='arrow_back',
                    on_click=lambda:
                    ui.navigate.to(self._back_to),
                ).props(
                    'flat round color=primary'
                )

            with ui.column().classes('gap-0'):
                ui.label(
                    self._title
                ).classes(
                    'text-3xl font-bold text-slate-900'
                )

                if self._subtitle:
                    ui.label(
                        self._subtitle
                    ).classes(
                        'text-slate-500 text-base'
                    )
