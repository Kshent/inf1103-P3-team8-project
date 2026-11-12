from nicegui import ui

import gui.homepage
import gui.menu_page


def main():

    ui.run(
        title='SmartStay',
        port=8080,
        reload=False
    )


if __name__ in {'__main__', '__mp_main__'}:
    main()