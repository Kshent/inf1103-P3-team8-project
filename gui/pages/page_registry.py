from __future__ import annotations

from collections.abc import Sequence

from .base_page import BasePage
from ..gui_controller import GuiController


class PageRegistry:
    """
    Registers page classes without depending on any specific page implementation.

    New BasePage subclasses can be supplied by the application without changing
    this class.
    """

    def __init__(
        self,
        controller: GuiController,
        page_types: Sequence[type[BasePage]],
    ) -> None:
        self._controller = controller
        self._page_types = tuple(page_types)

    def register_all(self) -> None:
        for page_type in self._page_types:
            page_type.register(self._controller)
