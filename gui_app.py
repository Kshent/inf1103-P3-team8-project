from nicegui import ui

from gui.gui_controller import GuiController
from gui.pages import register_pages


# Create manager/controller objects.
# This is NOT UI, so it is okay at global scope.
controller = GuiController()


# Register all @ui.page routes.
register_pages(controller)


if __name__ in {'__main__', '__mp_main__'}:

    ui.run(
        title='Hotel Recommendation System',
        favicon='🏨',
        port=8080,
        reload=False,
    )