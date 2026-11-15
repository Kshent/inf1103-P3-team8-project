from nicegui import ui


class PageSetup:
    """Applies common styling to every GUI page."""

    @staticmethod
    def apply() -> None:
        ui.query('body').classes(
            'bg-slate-50 text-slate-800'
        )

        ui.query('.nicegui-content').classes(
            'w-full'
        )
