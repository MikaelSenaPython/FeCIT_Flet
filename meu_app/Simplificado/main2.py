import flet as ft
from datetime import datetime

# ==============================================================================
# 1. DADOS GLOBAIS
# ==============================================================================
QUIZ_QUESTIONS = [
    {
        "question": "1. Qual destas áreas NÃO é um benefício significativo da IA para o meio ambiente?",
        "options": [
            {"text": "Otimização de redes de energia", "correct": False},
            {"text": "Monitoramento de espécies ameaçadas", "correct": False},
            {"text": "Redução do lixo eletrônico", "correct": True},
            {"text": "Agricultura de precisão", "correct": False}
        ]
    },
    {
        "question": "2. Qual porcentagem de tarefas administrativas pode ser automatizada por IA?",
        "options": [
            {"text": "25-40%", "correct": False},
            {"text": "40-60%", "correct": True},
            {"text": "60-80%", "correct": False},
            {"text": "Mais de 80%", "correct": False}
        ]
    },
    {
        "question": "3. Qual destas habilidades será MAIS valorizada na era da IA?",
        "options": [
            {"text": "Digitação rápida", "correct": False},
            {"text": "Cálculo manual", "correct": False},
            {"text": "Pensamento crítico", "correct": True},
            {"text": "Memorização de informações", "correct": False}
        ]
    }
]

# ==============================================================================
# 2. CLASSE DE ESTADO
# ==============================================================================
class AppState:
    def __init__(self):
        self.dark_mode = False

# ==============================================================================
# 3. FUNÇÃO PRINCIPAL
# ==============================================================================
def main(page: ft.Page):

    # --- CONFIGURAÇÃO INICIAL DA PÁGINA E ESTADO ---
    page.title = "IA: Revolução e Impacto"
    # Descomente para simular o tamanho de um celular
    # page.window_width = 400
    # page.window_height = 850
    # page.window_resizable = False
    
    state = AppState()

    page.theme = ft.Theme(font_family="Roboto", color_scheme=ft.ColorScheme(primary=ft.Colors.BLUE_700))
    page.dark_theme = ft.Theme(font_family="Roboto", color_scheme=ft.ColorScheme(primary=ft.Colors.BLUE_700, brightness=ft.Brightness.DARK))
    page.theme_mode = ft.ThemeMode.LIGHT

    page.padding = 0
    page.scroll = None

    # --- FUNÇÕES AUXILIARES DE CRIAÇÃO DE COMPONENTES ---
    def create_card(title, content, footer_text, icon=None, image_url=None):
        # ... (seu código de create_card aqui, sem alterações)
        pass # Substitua este 'pass' pelo seu código original

    def create_fact(icon, value, description):
        # ... (seu código de create_fact aqui, sem alterações)
        pass # Substitua este 'pass' pelo seu código original

    # --- LÓGICA DE EVENTOS ---
    def toggle_theme(e):
        state.dark_mode = not state.dark_mode
        page.theme_mode = ft.ThemeMode.DARK if state.dark_mode else ft.ThemeMode.LIGHT
        
        page.appbar.actions[4].icon = ft.icons.LIGHT_MODE if state.dark_mode else ft.icons.DARK_MODE
        
        # Atualiza as cores das seções que dependem do tema
        intro_section.bgcolor = ft.colors.with_opacity(0.1, ft.colors.ON_SURFACE) if state.dark_mode else ft.colors.with_opacity(0.05, ft.colors.ON_SURFACE)
        interactive_section.bgcolor = ft.colors.with_opacity(0.1, ft.colors.ON_SURFACE) if state.dark_mode else ft.colors.with_opacity(0.05, ft.colors.ON_SURFACE)
        
        page.update()

    # --- MONTAGEM DA UI ---

    # 1. Cria a coluna principal vazia.
    main_layout = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.ADAPTIVE,
        spacing=0
    )

    # 2. Cria as seções que farão parte do layout
    hero_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Inteligência Artificial: Revolução e Impacto", size=36, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE),
                ft.Text("Explore como a IA está transformando o mundo...", size=18, text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE70),
                ft.Row(
                    [
                        ft.ElevatedButton("Explorar Ferramentas", icon="explore", on_click=lambda _: main_layout.scroll_to(key="intro")),
                        ft.OutlinedButton("Saiba Mais", icon="info", on_click=lambda _: main_layout.scroll_to(key="impact"))
                    ],
                    alignment=ft.MainAxisAlignment.CENTER, spacing=20,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=30,
        ),
        padding=ft.padding.symmetric(vertical=100, horizontal=20), bgcolor=ft.Colors.BLUE_900, alignment=ft.alignment.center,
    )
    
    # ... (código para criar intro_section, impact_section, interactive_section, future_section, e footer aqui)
    # Lembre-se de usar `main_layout.scroll_to` nos botões do footer
    intro_section = ft.Container(key="intro", height=300, content=ft.Text("Seção de Introdução")) # Exemplo
    impact_section = ft.Container(key="impact", height=300, content=ft.Text("Seção de Impacto")) # Exemplo
    interactive_section = ft.Container(key="interactive", expand=True, content=ft.Text("Seção Interativa")) # Exemplo
    future_section = ft.Container(key="future", height=300, content=ft.Text("Seção Futuro")) # Exemplo
    footer = ft.Container(height=200, content=ft.Text("Rodapé"), bgcolor=ft.Colors.BLUE_900) # Exemplo

    # 3. Define o AppBar (cabeçalho fixo)
    page.appbar = ft.AppBar(
        title=ft.Text("IA Revolução", color=ft.Colors.WHITE),
        bgcolor=ft.Colors.BLUE_700,
        actions=[
            ft.TextButton("Introdução", on_click=lambda _: main_layout.scroll_to(key="intro")),
            ft.TextButton("Impactos", on_click=lambda _: main_layout.scroll_to(key="impact")),
            ft.TextButton("Interativo", on_click=lambda _: main_layout.scroll_to(key="interactive")),
            ft.TextButton("Futuro", on_click=lambda _: main_layout.scroll_to(key="future")),
            ft.IconButton(icon="dark_mode", on_click=toggle_theme),
        ],
    )

    # 4. Preenche a coluna principal com todas as seções
    main_layout.controls = [
        hero_section,
        intro_section,
        impact_section,
        interactive_section,
        future_section,
        footer,
    ]
    
    # 5. Adiciona o layout final à página
    page.add(main_layout)
    page.update()

# --- PONTO DE ENTRADA DO APLICATIVO ---
ft.app(target=main)