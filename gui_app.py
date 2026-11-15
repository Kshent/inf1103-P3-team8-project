from nicegui import ui

from gui.gui_controller import GuiController

from gui.pages.page_registry import PageRegistry
from gui.pages.home_page import HomePage
from gui.pages.menu_page import MenuPage
from gui.pages.search_page import SearchPage
from gui.pages.records_page import RecordsPage
from gui.pages.admin_page import AdminPage
from gui.pages.goodbye_page import GoodbyePage


class HotelRecommendationApplication:
    """
    Main GUI application.

    Responsible for:
    - Creating the GUI controller
    - Creating the page registry
    - Registering application pages
    - Starting the NiceGUI application
    """

    TITLE = 'Hotel Recommendation System'
    FAVICON = '🏨'
    PORT = 8080

    def __init__(self) -> None:
        self._controller = GuiController()

        self._page_registry = PageRegistry(
            self._controller,
            (
                HomePage,
                MenuPage,
                SearchPage,
                RecordsPage,
                AdminPage,
                GoodbyePage,
            ),
        )

        self._register_pages()

    def _register_pages(self) -> None:
        """Register all NiceGUI page routes."""
        self._page_registry.register_all()

    def run(self) -> None:
        """Start the NiceGUI web application."""
        ui.run(
            title=self.TITLE,
            favicon=self.FAVICON,
            port=self.PORT,
            reload=False,
        )


def main() -> None:
    """Application entry point."""
    application = HotelRecommendationApplication()
    application.run()


if __name__ in {'__main__', '__mp_main__'}:
    main()