import flet as ft
import random
import math
from datetime import datetime
# ==============================================================================
# 1. CLASSE DE ESTADO E DADOS GLOBAIS
# ==============================================================================
# teste
# Dados do Quiz (pode ficar aqui ou dentro da classe, como preferir)
quiz_questions = [
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

# Estado do aplicativo
class AppState:
    def __init__(self):
        self.current_question = 0
        self.quiz_score = 0
        self.selected_option = None
        self.co2_amount = 0
        self.calculator_result = None
        self.dark_mode = False

    def next_question(self):
        """Avança para a próxima pergunta se não for a última. Retorna True se avançou, False caso contrário."""
        if self.current_question < len(quiz_questions) - 1:
            self.current_question += 1
            self.selected_option = None
            return True
        return False

    def check_answer(self, option_index):
        
        if option_index is None:
            return False
        return quiz_questions[self.current_question]["options"][option_index]["correct"]

    def calculate_footprint(self, model_size, training_time, hardware, energy_source):
        """Calcula a pegada de carbono com base nos parâmetros."""
        size_factors = {
            "Pequeno (até 100 milhões)": 1,
            "Médio (100m-1 bilhão)": 10,
            "Grande (1-10 bilhões)": 50,
            "Muito Grande (10+ bilhões)": 200
        }
        hardware_factors = {
            "CPUs Padrão": 1.5,
            "GPUs Especializadas": 1.0,
            "TPUs (Tensor Processing Units)": 0.7
        }
        energy_factors = {
            "Combustíveis Fósseis": 1.5,
            "Mista": 1.0,
            "Renovável": 0.3
        }
        
        size_factor = size_factors.get(model_size, 1)
        hardware_factor = hardware_factors.get(hardware, 1)
        energy_factor = energy_factors.get(energy_source, 1)
        
        self.co2_amount = size_factor * training_time * hardware_factor * energy_factor
        self.calculator_result = {
            "co2": self.co2_amount,
            "cars": round(self.co2_amount / 4.6),
            "suggestions": self.get_suggestions()
        }

    def get_suggestions(self):
        """Gera sugestões com base na pegada de carbono calculada."""
        suggestions = [
            "Otimize arquiteturas de modelos",
            "Use hardware eficiente",
            "Priorize data centers com energia renovável"
        ]
        if self.co2_amount > 50:
            suggestions.insert(0, "Considere reduzir o tamanho do modelo")
        return suggestions

    def toggle_dark_mode(self):
        """Alterna o estado do modo escuro."""
        self.dark_mode = not self.dark_mode


# NOVA FUNÇÃO OTIMIZADA (fora da main)
def next_question(e, page, state, quiz_content, show_results_func, update_quiz_func):
    """
    Verifica a resposta, atualiza o placar e avança para a próxima pergunta ou mostra o resultado.
    """
    # Verifica a resposta da pergunta atual e atualiza a pontuação
    if state.check_answer(state.selected_option):
        state.quiz_score += 1

    # Tenta avançar para a próxima pergunta.
    # state.next_question() retorna False se for a última pergunta.
    is_last_question = not state.next_question()

    # Decide se mostra os resultados ou a próxima pergunta
    if is_last_question:
        quiz_content.content = show_results_func(page, state, quiz_content, show_results_func, update_quiz_func) # Passa os argumentos necessários
    else:
        update_quiz_func(page, state, quiz_content, show_results_func, update_quiz_func) # Passa os argumentos necessários
    
    page.update()

def main(page: ft.Page):
    # Configurações iniciais da página
    page.title = "IA: Revolução e Impacto"
    page.fonts = {
        "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap",
        "Montserrat": "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap",
        "MaterialIcons": "https://fonts.googleapis.com/css2?family=Material+Icons"
    }
    page.theme = ft.Theme(
        font_family="Roboto",
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.BLUE_700,
            primary_container=ft.Colors.BLUE_200,
            secondary=ft.Colors.CYAN_600,
            tertiary=ft.Colors.TEAL_400,
        )
    )
    page.scroll = "adaptive"
    page.padding = 0

    # Inicializa o estado do aplicativo
    state = AppState()
    page.theme_mode = ft.ThemeMode.DARK if state.dark_mode else ft.ThemeMode.LIGHT


    # Paleta de cores
    colors = {
        "primary": "#4361ee",
        "secondary": "#3f37c9",
        "accent": "#4895ef",
        "dark": "#1d3557",
        "light": "#f8f9fa",
        "success": "#4cc9f0",
        "warning": "#f72585"
    }

    # Dados para os gráficos
    automation_data = [
        {"setor": "Administrativo", "percent": 55, "icon": "description"},
        {"setor": "Manufatura", "percent": 45, "icon": "factory"},
        {"setor": "Varejo", "percent": 38, "icon": "shopping_cart"},
        {"setor": "Transporte", "percent": 30, "icon": "local_shipping"},
        {"setor": "Saúde", "percent": 20, "icon": "medical_services"},
        {"setor": "Educação", "percent": 15, "icon": "school"},
        {"setor": "TI", "percent": 40, "icon": "computer"},
    ]
    
    energy_data = [
        {"tipo": "Treinamento", "percent": 45, "color": ft.Colors.RED_400},
        {"tipo": "Inferência", "percent": 35, "color": ft.Colors.BLUE_400},
        {"tipo": "Armazenamento", "percent": 10, "color": ft.Colors.GREEN_400},
        {"tipo": "Refrigeração", "percent": 10, "color": ft.Colors.YELLOW_400},
    ]
    
    # Componentes personalizados
    def create_card(title, content, footer_text, icon=None, image_url=None):
        card_content = [
            ft.ListTile(
                leading=ft.Icon(icon) if icon else None,
                title=ft.Text(title, weight=ft.FontWeight.BOLD, size=18),
                subtitle=ft.Text(content, size=14),
            ),
            ft.Row(
                [ft.Text(footer_text, color=ft.Colors.GREY_600)],
                alignment=ft.MainAxisAlignment.END,
            ),
        ]
        
        if image_url:
            card_content.insert(0, ft.Image(
                src=image_url,
                width=300,
                height=150,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.only(top_left=10, top_right=10),
            ))
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column(card_content),
                width=300,
                padding=10,
                ink=True,
            ),
            elevation=8,
            shadow_color=ft.Colors.BLUE_100,
            shape=ft.RoundedRectangleBorder(radius=10),
        )

    def create_fact(icon, value, description):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=40, color=ft.Colors.WHITE),
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text(description, text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=20,
            bgcolor=ft.Colors.BLUE_700,
            border_radius=10,
            width=250,
            height=180,
            animate=ft.animation.Animation(500, "easeOut"),
        )

    def create_bar_chart(data, title, height=200):
        max_value = max(item["percent"] for item in data)
        bars = []
        
        for i, item in enumerate(data):
            bar_height = (item["percent"] / max_value) * (height - 40)
            bars.append(
                ft.Column(
                    [
                        ft.Text(f"{item['percent']}%", size=12),
                        ft.Container(
                            width=40,
                            height=bar_height,
                            bgcolor=ft.Colors.BLUE_400 if i % 2 == 0 else ft.Colors.CYAN_400,
                            border_radius=ft.border_radius.vertical(top=5),
                            animate=ft.animation.Animation(800, "easeOut"),
                        ),
                        ft.Text(item["setor"], size=12, text_align=ft.TextAlign.CENTER),
                        ft.Icon(item["icon"], size=20)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5,
                )
            )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        bars,
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        height=height,
                    )
                ],
                spacing=10,
            ),
            padding=20,
            border_radius=10,
            bgcolor=ft.Colors.GREY_100 if not state.dark_mode else ft.Colors.GREY_800,
        )

    def create_pie_chart(data, title, container_size=200):
        sections = []
        
        for item in data:
            sections.append(
                ft.PieChartSection(
                    item["percent"],
                    color=item["color"],
                )
            )
        
        chart = ft.PieChart(
            sections=sections,
            sections_space=0,
            center_space_radius=40,  # Tamanho do espaço central
        )
        
        # Criar a legenda
        legend_items = []
        for item in data:
            legend_items.append(
                ft.Row(
                    [
                        ft.Container(
                            width=15,
                            height=15,
                            bgcolor=item["color"],
                            border_radius=5,
                        ),
                        ft.Text(f"{item['tipo']} ({item['percent']}%)", size=12)
                    ],
                    spacing=5,
                )
            )
        
        legend = ft.Column(legend_items, spacing=5)
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.Container(
                                content=chart,
                                width=container_size,
                                height=container_size,
                            ),
                            legend
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            padding=20,
            border_radius=10,
            bgcolor=ft.Colors.GREY_100 if not state.dark_mode else ft.Colors.GREY_800,
        )

    # Elementos de UI
    # NOVA FUNÇÃO (fora da main)
    # NOVA FUNÇÃO (fora da main)
    # NOVA FUNÇÃO (fora da main)
    def toggle_theme(e, page, state, create_ui_func):
        """
        Alterna o tema entre claro e escuro e recria a interface.
        """
        state.toggle_dark_mode()
        page.theme_mode = ft.ThemeMode.DARK if state.dark_mode else ft.ThemeMode.LIGHT
        
        # Recria a UI para aplicar as novas cores
        page.controls.clear()
        create_ui_func(page, state)
        page.update()

    def create_ui(page, state):
        # Hero Section
        hero_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Inteligência Artificial: Revolução e Impacto",
                        size=36,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        "Explore como a IA está transformando o mundo do trabalho e o meio ambiente, e descubra como se preparar para o futuro.",
                        size=18,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.WHITE70,
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Explorar Ferramentas", 
                                icon="explore",
                                on_click=lambda _: page.scroll_to("intro")
                            ),
                            ft.OutlinedButton(
                                "Saiba Mais", 
                                icon="info",
                                on_click=lambda _: page.scroll_to("impact")
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=30,
            ),
            padding=ft.padding.symmetric(vertical=100, horizontal=20),
            bgcolor=ft.Colors.BLUE_900,
            alignment=ft.alignment.center,
        )
        
        # Seção de Introdução
        intro_cards = ft.Row(
            scroll=ft.ScrollMode.ADAPTIVE,
            controls=[
                create_card(
                    "Conceitos Básicos",
                    "Inteligência Artificial é o campo da ciência da computação que busca criar sistemas capazes de realizar tarefas que normalmente exigem inteligência humana.",
                    "Fundamentos",
                    icon="psychology",
                    image_url="https://images.unsplash.com/photo-1677442135133-33d364e7d1e5?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80"
                ),
                create_card(
                    "Como Funciona",
                    "Os sistemas de IA funcionam através de redes neurais artificiais que simulam o funcionamento do cérebro humano.",
                    "Tecnologia",
                    icon="settings",
                    image_url="https://images.unsplash.com/photo-1677442135130-33d364e7d1e5?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80"
                ),
                create_card(
                    "Aplicações Práticas",
                    "A IA já está presente em diversos aspectos do nosso dia a dia: assistentes virtuais, recomendações personalizadas, diagnósticos médicos.",
                    "Aplicações",
                    icon="apps",
                    image_url="https://images.unsplash.com/photo-1677442135133-33d364e7d1e5?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80"
                ),
            ],
            spacing=20,
        )

        intro_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "O que é Inteligência Artificial?",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    intro_cards,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=40,
            ),
            padding=40,
            bgcolor=ft.Colors.GREY_100 if not state.dark_mode else ft.Colors.GREY_900,
        )
        intro_section.id = "intro"

        # Seção de Impactos
        impact_cards = ft.Row(
            scroll=ft.ScrollMode.ADAPTIVE,
            controls=[
                create_card(
                    "Futuro do Trabalho",
                    "A IA está transformando radicalmente o mercado de trabalho. Enquanto algumas profissões podem ser automatizadas, outras surgirão, exigindo novas habilidades.",
                    "Oportunidades e Desafios",
                    icon="work",
                    image_url="https://images.unsplash.com/photo-1553877522-43269d4ea984?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80"
                ),
                create_card(
                    "Meio Ambiente",
                    "A IA pode ser uma poderosa aliada na preservação ambiental, otimizando o uso de recursos, monitorando ecossistemas.",
                    "Benefícios e Riscos",
                    icon="eco",
                    image_url="https://images.unsplash.com/photo-1469474968028-56623f02e42e?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80"
                ),
                create_card(
                    "Preparação para o Futuro",
                    "Para prosperar na era da IA, é essencial desenvolver habilidades que complementem a tecnologia: pensamento crítico, criatividade.",
                    "Educação e Sociedade",
                    icon="school",
                    image_url="https://images.unsplash.com/photo-1506784983877-45594efa4cbe?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80"
                ),
            ],
            spacing=20,
        )

        impact_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Impactos da Inteligência Artificial",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    impact_cards,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=40,
            ),
            padding=40,
        )
        impact_section.id = "impact"

        # Seção Interativa
        # Gráficos
        tab_graphs = ft.Column(
            [
                create_bar_chart(automation_data, "Impacto da IA no Mercado de Trabalho"),
                create_pie_chart(energy_data, "Consumo de Energia na IA"),
            ],
            spacing=40,
        )

        # Quiz
        def update_quiz():
            question = quiz_questions[state.current_question]
            options = []
            
            for idx, option in enumerate(question["options"]):
                options.append(
                    ft.ElevatedButton(
                        option["text"],
                        on_click=lambda e, i=idx: select_option(i),
                        width=400,
                        style=ft.ButtonStyle(
                            bgcolor=(
                                ft.Colors.GREEN_400 if state.selected_option == idx and option["correct"] else
                                ft.Colors.RED_400 if state.selected_option == idx and not option["correct"] else
                                ft.Colors.BLUE_50 if not state.dark_mode else ft.Colors.GREY_800
                            ),
                            color=ft.Colors.BLACK if state.selected_option != idx else ft.Colors.WHITE,
                        ),
                    )
                )
            
            quiz_content.content = ft.Column(
                [
                    ft.Text(question["question"], size=18, weight=ft.FontWeight.BOLD),
                    ft.Column(options, spacing=10),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Próxima Pergunta" if state.current_question < len(quiz_questions) - 1 else "Ver Resultado",
                                on_click=next_question,
                                disabled=state.selected_option is None,
                                icon="arrow_forward"
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                ],
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            page.update()

        def select_option(option_index):
            state.selected_option = option_index
            update_quiz()

        def next_question(e):
            if state.current_question < len(quiz_questions) - 1:
                if state.check_answer(state.selected_option):
                    state.quiz_score += 1
                state.next_question()
                update_quiz()
            else:
                if state.check_answer(state.selected_option):
                    state.quiz_score += 1
                quiz_content.content = show_results()
                page.update()

        def show_results():
            feedback = ""
            if state.quiz_score == 3:
                feedback = "Parabéns! Você domina os conceitos fundamentais sobre IA."
            elif state.quiz_score == 2:
                feedback = "Bom trabalho! Você tem um bom entendimento sobre IA."
            elif state.quiz_score == 1:
                feedback = "Você está no caminho certo, mas pode aprender mais sobre IA."
            else:
                feedback = "Continue explorando para entender melhor o impacto da IA."
            
            return ft.Column(
                [
                    ft.Text("Resultado do Quiz", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Você acertou {state.quiz_score} de {len(quiz_questions)} perguntas!", size=20),
                    ft.Text(feedback, size=18, text_align=ft.TextAlign.CENTER),
                    ft.ElevatedButton("Tentar Novamente", on_click=reset_quiz, icon="replay"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            )

        def reset_quiz(e):
            state.current_question = 0
            state.quiz_score = 0
            state.selected_option = None
            update_quiz()

        quiz_content = ft.Container(
            padding=20,
            content=ft.Column()
        )
        update_quiz()

        tab_quiz = ft.Container(
            content=quiz_content
        )

        # Calculadora
        model_size = ft.Dropdown(
            label="Tamanho do Modelo",
            options=[
                ft.dropdown.Option("Pequeno (até 100 milhões)"),
                ft.dropdown.Option("Médio (100m-1 bilhão)"),
                ft.dropdown.Option("Grande (1-10 bilhões)"),
                ft.dropdown.Option("Muito Grande (10+ bilhões)"),
            ],
            value="Médio (100m-1 bilhão)",
            width=400,
        )

        training_time = ft.TextField(
            label="Tempo de Treinamento (dias)",
            value="7",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=400,
        )

        hardware = ft.Dropdown(
            label="Hardware Utilizado",
            options=[
                ft.dropdown.Option("CPUs Padrão"),
                ft.dropdown.Option("GPUs Especializadas"),
                ft.dropdown.Option("TPUs (Tensor Processing Units)"),
            ],
            value="GPUs Especializadas",
            width=400,
        )

        energy_source = ft.Dropdown(
            label="Fonte de Energia",
            options=[
                ft.dropdown.Option("Combustíveis Fósseis"),
                ft.dropdown.Option("Mista"),
                ft.dropdown.Option("Renovável"),
            ],
            value="Mista",
            width=400,
        )

        calculator_result = ft.Column(visible=False)

        def calculate_footprint(e):
            try:
                days = int(training_time.value)
                state.calculate_footprint(
                    model_size.value,
                    days,
                    hardware.value,
                    energy_source.value
                )
                
                result = state.calculator_result
                
                progress_width = min(100, (result["co2"] / 300) * 100) * 3
                
                calculator_result.controls = [
                    ft.Text("Sua Pegada de Carbono Estimada", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"O modelo de IA geraria aproximadamente:", size=16),
                    ft.Text(f"{result['co2']:.1f} toneladas", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                    ft.Text("de CO2 equivalente", size=16),
                    
                    ft.Container(
                        content=ft.Container(
                            width=progress_width,
                            height=20,
                            bgcolor=ft.Colors.RED_400,
                            border_radius=ft.border_radius.all(10),
                        ),
                        width=300,
                        height=20,
                        bgcolor=ft.Colors.GREY_300,
                        border_radius=10,
                        padding=0,
                    ),
                    
                    ft.Text(f"Isso equivale a {result['cars']} carros na estrada por um ano", size=16),
                    
                    ft.Text("Sugestões para Reduzir o Impacto:", size=18, weight=ft.FontWeight.BOLD, top=20),
                    ft.Column(
                        [ft.Text(f"• {suggestion}") for suggestion in result["suggestions"]],
                        spacing=5,
                    )
                ]
                
                calculator_result.visible = True
                page.update()
                
            except ValueError:
                page.snack_bar = ft.SnackBar(ft.Text("Por favor, insira um número válido para dias de treinamento"))
                page.snack_bar.open = True
                page.update()

        tab_calculator = ft.Column(
            [
                ft.Text("Calculadora de Pegada de Carbono em IA", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Esta calculadora estima o impacto ambiental de modelos de IA", size=16),
                model_size,
                training_time,
                hardware,
                energy_source,
                ft.ElevatedButton("Calcular Pegada", on_click=calculate_footprint, icon="calculate"),
                calculator_result,
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Tabs container
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Gráficos", icon="bar_chart", content=tab_graphs),
                ft.Tab(text="Quiz", icon="quiz", content=tab_quiz),
                ft.Tab(text="Calculadora", icon="calculate", content=tab_calculator),
            ],
            expand=1,
        )

        interactive_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Explore Interativamente", size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    tabs,
                ],
                spacing=40,
            ),
            padding=40,
            bgcolor=ft.Colors.GREY_100 if not state.dark_mode else ft.Colors.GREY_900,
        )
        interactive_section.id = "interactive"

        # Seção Futuro
        facts = ft.Row(
            scroll=ft.ScrollMode.ADAPTIVE,
            controls=[
                create_fact("trending_up", "+65%", "dos empregos sofrerão mudanças com a IA até 2030"),
                create_fact("eco", "15-20%", "redução no desperdício agrícola com IA e sensores"),
                create_fact("school", "120 milhões", "de trabalhadores precisarão de requalificação"),
                create_fact("bolt", "3.5%", "das emissões globais podem vir de tecnologia até 2030"),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        future_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Preparando-se para o Futuro", size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    facts,
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Como se Preparar para a Era da IA", size=22, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    "O futuro com IA exige desenvolvimento de habilidades complementares como pensamento crítico, criatividade, "
                                    "inteligência emocional e capacidade de aprendizado contínuo.",
                                    size=16,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.ElevatedButton("Baixe o Guia Completo", icon="download"),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=20,
                        ),
                        padding=40,
                        width=800,
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=40,
            ),
            padding=40,
        )
        future_section.id = "future"

        # Footer
        footer = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon("psychology", size=40, color=ft.Colors.CYAN_300),
                            ft.Text("IA Revolução", size=24, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    ft.Text("Explorando os impactos e oportunidades da Inteligência Artificial", size=16, text_align=ft.TextAlign.CENTER),
                    ft.Row(
                        [
                            ft.TextButton("Introdução", on_click=lambda _: page.scroll_to("intro")),
                            ft.TextButton("Impactos", on_click=lambda _: page.scroll_to("impact")),
                            ft.TextButton("Interativo", on_click=lambda _: page.scroll_to("interactive")),
                            ft.TextButton("Futuro", on_click=lambda _: page.scroll_to("future")),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Text("Projeto desenvolvido para Feira de Ciências e Tecnologia - FeCIT 2025", size=14),
                    ft.Text(f"© {datetime.now().year} IA Revolução. Todos os direitos reservados.", size=12, color=ft.Colors.GREY_500),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            padding=40,
            bgcolor=ft.Colors.BLUE_900,
        )
        
        # Header
        header = ft.AppBar(
            title=ft.Row(
                [
                    ft.Icon("psychology", color=ft.Colors.CYAN_300),
                    ft.Text("IA Revolução", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                ],
                spacing=10,
            ),
            bgcolor=ft.Colors.BLUE_700,
            actions=[
                ft.TextButton("Introdução", on_click=lambda _: page.scroll_to("intro")),
                ft.TextButton("Impactos", on_click=lambda _: page.scroll_to("impact")),
                ft.TextButton("Interativo", on_click=lambda _: page.scroll_to("interactive")),
                ft.TextButton("Futuro", on_click=lambda _: page.scroll_to("future")),
                ft.IconButton(icon="dark_mode" if not state.dark_mode else "light_mode", on_click=lambda e: toggle_theme(e, page, state, create_ui)),
            ],
        )

        # Adicionar tudo à página
        page.add(
            header,
            hero_section,
            intro_section,
            impact_section,
            interactive_section,
            future_section,
            footer,
        )
    
    # Criar a UI inicial
    create_ui(page, state)
    page.update()

# Iniciar o aplicativo
ft.app(target=main, view=ft.WEB_BROWSER)