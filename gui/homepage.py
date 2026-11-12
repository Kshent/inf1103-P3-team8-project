from nicegui import ui


@ui.page('/')
def home_page():

    ui.page_title('SmartStay')

    ui.query('body').classes(
        'bg-gradient-to-br from-purple-50 via-white to-indigo-100'
    )

    with ui.column().classes(
        'w-full min-h-screen items-center justify-center px-6'
    ):

        with ui.card().classes(
            'w-full max-w-3xl items-center '
            'p-12 rounded-3xl shadow-xl'
        ):

            ui.icon(
                'hotel',
                size='70px',
                color='deep-purple-5'
            )

            ui.label(
                'Welcome to SmartStay'
            ).classes(
                'text-4xl font-bold text-purple-900 text-center'
            )

            ui.label(
                'Find hotel recommendations tailored '
                'to your travel needs.'
            ).classes(
                'text-lg text-gray-600 text-center max-w-xl'
            )

            ui.separator().classes('my-5')

            ui.label(
                'Smart recommendations. '
                'Personalised scoring. Better stays.'
            ).classes(
                'text-base text-gray-500 text-center'
            )

            ui.button(
                'Enter SmartStay',
                icon='arrow_forward',
                on_click=lambda: ui.navigate.to('/menu')
            ).props(
                'unelevated rounded'
            ).classes(
                'mt-6 px-8 py-3 text-lg '
                'bg-purple-600 text-white'
            )