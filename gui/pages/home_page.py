from nicegui import ui

from .base_page import BasePage


class HomePage(BasePage):

    ROUTE = '/'
    TITLE = 'Hotel Recommendation System'

    def render(self) -> None:

        self._prepare_page()

        # Small custom animations used only by this page.
        ui.add_head_html(
            '''
            <style>
                @keyframes fadeUp {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                @keyframes floatIcon {
                    0%, 100% {
                        transform: translateY(0px);
                    }
                    50% {
                        transform: translateY(-8px);
                    }
                }

                @keyframes softPulse {
                    0%, 100% {
                        opacity: 0.35;
                        transform: scale(1);
                    }
                    50% {
                        opacity: 0.55;
                        transform: scale(1.08);
                    }
                }

                .home-fade-1 {
                    animation: fadeUp 0.6s ease-out;
                }

                .home-fade-2 {
                    animation: fadeUp 0.8s ease-out;
                }

                .home-fade-3 {
                    animation: fadeUp 1s ease-out;
                }

                .home-float {
                    animation: floatIcon 3s ease-in-out infinite;
                }

                .home-glow {
                    animation: softPulse 5s ease-in-out infinite;
                }
            </style>
            '''
        )

        with ui.column().classes(
            'relative w-full min-h-screen '
            'items-center justify-center '
            'overflow-hidden px-6 py-10 '
            'bg-gradient-to-br '
            'from-purple-50 via-white to-blue-50'
        ):

            # -------------------------------------------------
            # Decorative background
            # -------------------------------------------------

            ui.element('div').classes(
                'absolute -top-24 -left-24 '
                'w-72 h-72 rounded-full '
                'bg-purple-200 blur-3xl '
                'home-glow'
            )

            ui.element('div').classes(
                'absolute -bottom-24 -right-24 '
                'w-80 h-80 rounded-full '
                'bg-blue-200 blur-3xl '
                'home-glow'
            )

            # -------------------------------------------------
            # Main hero card
            # -------------------------------------------------

            with ui.card().classes(
                'relative z-10 '
                'w-full max-w-5xl '
                'rounded-[32px] '
                'px-10 py-12 '
                'items-center '
                'border border-purple-100 '
                'shadow-xl bg-white/95'
            ):

                # Small top label
                with ui.row().classes(
                    'items-center gap-2 '
                    'px-4 py-2 rounded-full '
                    'bg-purple-50 '
                    'home-fade-1'
                ):

                    ui.icon(
                        'auto_awesome',
                        size='1.1rem',
                        color='primary',
                    )

                    ui.label(
                        'AI-powered hotel discovery'
                    ).classes(
                        'text-sm font-semibold '
                        'text-purple-700'
                    )

                # -------------------------------------------------
                # Logo icon
                # -------------------------------------------------

                with ui.element(
                    'div'
                ).classes(
                    'w-24 h-24 mt-5 '
                    'rounded-3xl '
                    'bg-gradient-to-br '
                    'from-purple-100 to-blue-100 '
                    'flex items-center justify-center '
                    'shadow-sm home-float'
                ):

                    ui.icon(
                        'hotel',
                        size='3.4rem',
                        color='primary',
                    )

                # -------------------------------------------------
                # Main heading
                # -------------------------------------------------

                ui.label(
                    'Hotel Recommendation System'
                ).classes(
                    'text-5xl max-md:text-4xl '
                    'font-bold text-slate-900 '
                    'text-center mt-5 '
                    'home-fade-1'
                )

                ui.label(
                    'Find hotels that match your budget, '
                    'preferences and travel priorities.'
                ).classes(
                    'text-lg text-slate-500 '
                    'text-center max-w-2xl '
                    'leading-relaxed mt-2 '
                    'home-fade-2'
                )

                # -------------------------------------------------
                # Feature cards
                # -------------------------------------------------

                with ui.grid(
                    columns=3
                ).classes(
                    'w-full max-w-3xl '
                    'gap-4 mt-8 '
                    'max-md:grid-cols-1 '
                    'home-fade-2'
                ):

                    self._feature_card(
                        icon='auto_awesome',
                        title='AI Powered',
                        description=(
                            'Smart hotel recommendations '
                            'based on your needs.'
                        ),
                    )

                    self._feature_card(
                        icon='tune',
                        title='Personalised',
                        description=(
                            'Choose how important price, '
                            'rating and location are.'
                        ),
                    )

                    self._feature_card(
                        icon='workspace_premium',
                        title='Top 3 Matches',
                        description=(
                            'See the strongest matches '
                            'without overwhelming results.'
                        ),
                    )

                # -------------------------------------------------
                # CTA
                # -------------------------------------------------

                ui.button(
                    'Find My Hotel',
                    icon='travel_explore',
                    on_click=lambda:
                    ui.navigate.to('/menu'),
                ).props(
                    'unelevated rounded '
                    'color=primary size=lg'
                ).classes(
                    'mt-9 px-10 py-2 '
                    'shadow-md '
                    'transition-all duration-300 '
                    'hover:shadow-xl '
                    'hover:-translate-y-1 '
                    'home-fade-3'
                )

                ui.label(
                    'Start by telling us where you want to stay.'
                ).classes(
                    'text-xs text-slate-400 '
                    'mt-3 home-fade-3'
                )

    def _feature_card(
        self,
        icon: str,
        title: str,
        description: str,
    ) -> None:

        with ui.card().classes(
            'w-full p-5 rounded-2xl '
            'shadow-none '
            'border border-slate-100 '
            'bg-slate-50/70 '
            'items-center text-center '
            'transition-all duration-300 '
            'hover:-translate-y-1 '
            'hover:shadow-md '
            'hover:border-purple-200'
        ):

            with ui.element(
                'div'
            ).classes(
                'w-11 h-11 rounded-xl '
                'bg-purple-100 '
                'flex items-center justify-center'
            ):

                ui.icon(
                    icon,
                    size='1.6rem',
                    color='primary',
                )

            ui.label(
                title
            ).classes(
                'font-bold text-slate-800 '
                'mt-2'
            )

            ui.label(
                description
            ).classes(
                'text-sm text-slate-500 '
                'leading-relaxed'
            )