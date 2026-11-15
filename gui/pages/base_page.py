from __future__ import annotations

from abc import ABC, abstractmethod

from nicegui import ui

from ..components.page_setup import PageSetup
from ..gui_controller import GuiController


class BasePage(ABC):
    """
    Abstract base class for every GUI page.

    Shared responsibility:
    - Store the GUI controller
    - Register a NiceGUI route
    - Apply shared page setup
    - Require every concrete page to implement render()
    """

    ROUTE = '/'
    TITLE = 'Hotel Recommendation System'

    def __init__(
        self,
        controller: GuiController,
    ) -> None:
        self._controller = controller

    @classmethod
    def register(
        cls,
        controller: GuiController,
    ) -> None:
        """Register the page route with NiceGUI."""

        def page_handler() -> None:
            page = cls(controller)
            page.render()

        ui.page(cls.ROUTE)(page_handler)

    def _prepare_page(self) -> None:
        """Apply common styling and the browser page title."""
        PageSetup.apply()
        ui.page_title(self.TITLE)

    @abstractmethod
    def render(self) -> None:
        """Render the concrete page."""
        raise NotImplementedError
