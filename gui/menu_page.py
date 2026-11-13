# from nicegui import ui  # type: ignore[reportMissingImports]


# @ui.page('/menu')
# def menu_page():

#     ui.page_title('SmartStay - Main Menu')

#     ui.query('body').classes(
#         'bg-gray-50'
#     )

#     with ui.column().classes(
#         'w-full min-h-screen items-center px-6 py-12'
#     ):

#         # Header
#         with ui.row().classes(
#             'w-full max-w-5xl items-center'
#         ):

#             with ui.row().classes(
#                 'items-center gap-3'
#             ):
#                 ui.icon(
#                     'hotel',
#                     size='40px',
#                     color='deep-purple-5'
#                 )

#                 ui.label(
#                     'SmartStay'
#                 ).classes(
#                     'text-2xl font-bold text-purple-900'
#                 )

#             ui.space()

#             ui.button(
#                 'Home',
#                 icon='home',
#                 on_click=lambda: ui.navigate.to('/')
#             ).props('flat')

#         ui.separator().classes(
#             'w-full max-w-5xl my-6'
#         )

#         # Page heading
#         with ui.column().classes(
#             'w-full max-w-5xl'
#         ):

#             ui.label(
#                 'What would you like to do?'
#             ).classes(
#                 'text-3xl font-bold text-gray-800'
#             )

#             ui.label(
#                 'Choose an option below to continue.'
#             ).classes(
#                 'text-gray-500 text-lg'
#             )

#         # Menu cards
#         with ui.grid(columns=2).classes(
#             'w-full max-w-5xl gap-6 mt-8'
#         ):

#             create_menu_card(
#                 icon='travel_explore',
#                 title='Find Hotels',
#                 description=(
#                     'Get personalised hotel recommendations '
#                     'based on your budget and preferences.'
#                 ),
#                 button_text='Start Search',
#                 destination='/search'
#             )

#             create_menu_card(
#                 icon='history',
#                 title='Previous Searches',
#                 description=(
#                     'View hotel recommendations from '
#                     'your previous searches.'
#                 ),
#                 button_text='View Records',
#                 destination='/records'
#             )

#             create_menu_card(
#                 icon='admin_panel_settings',
#                 title='Admin Login',
#                 description=(
#                     'Access the administrative view '
#                     'for stored recommendation records.'
#                 ),
#                 button_text='Admin Login',
#                 destination='/admin'
#             )

#             create_menu_card(
#                 icon='logout',
#                 title='Exit',
#                 description=(
#                     'Finish your SmartStay session.'
#                 ),
#                 button_text='Exit',
#                 destination='/goodbye'
#             )


# def create_menu_card(
#     icon: str,
#     title: str,
#     description: str,
#     button_text: str,
#     destination: str
# ):

#     with ui.card().classes(
#         'w-full p-6 rounded-2xl shadow-sm '
#         'hover:shadow-lg transition-shadow'
#     ):

#         ui.icon(
#             icon,
#             size='45px',
#             color='deep-purple-5'
#         )

#         ui.label(
#             title
#         ).classes(
#             'text-xl font-bold text-gray-800 mt-2'
#         )

#         ui.label(
#             description
#         ).classes(
#             'text-gray-500 min-h-[55px]'
#         )

#         ui.button(
#             button_text,
#             on_click=lambda: ui.navigate.to(destination)
#         ).props(
#             'unelevated'
#         ).classes(
#             'mt-4 bg-purple-600 text-white'
#         )


# # Temporary pages.
# # We will replace these with the real functionality later.

# @ui.page('/search')
# def search_placeholder():

#     with ui.column().classes(
#         'absolute-center items-center gap-4'
#     ):

#         ui.icon(
#             'travel_explore',
#             size='60px',
#             color='deep-purple-5'
#         )

#         ui.label(
#             'Hotel Search'
#         ).classes(
#             'text-3xl font-bold'
#         )

#         ui.label(
#             'Traveller input screen will go here.'
#         )

#         ui.button(
#             'Back to Menu',
#             on_click=lambda: ui.navigate.to('/menu')
#         )


# @ui.page('/records')
# def records_placeholder():

#     with ui.column().classes(
#         'absolute-center items-center gap-4'
#     ):

#         ui.label(
#             'Previous Hotel Records'
#         ).classes(
#             'text-3xl font-bold'
#         )

#         ui.label(
#             'Saved recommendations will be shown here.'
#         )

#         ui.button(
#             'Back to Menu',
#             on_click=lambda: ui.navigate.to('/menu')
#         )


# @ui.page('/admin')
# def admin_placeholder():

#     with ui.column().classes(
#         'absolute-center items-center gap-4'
#     ):

#         ui.label(
#             'Admin Login'
#         ).classes(
#             'text-3xl font-bold'
#         )

#         ui.label(
#             'Admin login screen will go here.'
#         )

#         ui.button(
#             'Back to Menu',
#             on_click=lambda: ui.navigate.to('/menu')
#         )


# @ui.page('/goodbye')
# def goodbye_page():

#     with ui.column().classes(
#         'absolute-center items-center gap-5'
#     ):

#         ui.icon(
#             'hotel',
#             size='60px',
#             color='deep-purple-5'
#         )

#         ui.label(
#             'Thanks for using SmartStay!'
#         ).classes(
#             'text-3xl font-bold text-purple-900'
#         )

#         ui.label(
#             'We hope you find the perfect stay.'
#         ).classes(
#             'text-gray-500'
#         )

#         ui.button(
#             'Return Home',
#             on_click=lambda: ui.navigate.to('/')
#         )