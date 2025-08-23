# main.py
import flet as ft
from datetime import datetime, timedelta
import itertools
import database as db
import os
from calendar import month_name
from fpdf import FPDF
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt   
import traceback

# =============================================================================
# CONSTANTES E CONFIGURAÇÕES
# =============================================================================

APP_PASSWORD = "162408"

# =============================================================================
# FUNÇÕES AUXILIARES E UTILITÁRIOS
# =============================================================================

def criar_imagem_grafico(dados_categoria, titulo, caminho_arquivo, tipo):
    """Cria e salva um gráfico de pizza, usando cores específicas para o tipo."""
    if not dados_categoria:
        return False

    labels = dados_categoria.keys()
    sizes = dados_categoria.values()
    
    # Lógica das cores
    if tipo == 'Receita':
        cores = ['#4CAF50', '#8BC34A', '#CDDC39', '#C5E1A5', '#AED581']
    else:
        cores = ['#F44336', '#E57373', '#EF5350', '#FFCDD2', '#FF8A80']
    
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=cores)
    ax.axis('equal')
    plt.title(titulo)
    
    plt.savefig(caminho_arquivo, transparent=True)
    plt.close(fig)
    return True

# =============================================================================
# TELA DE LOGIN
# =============================================================================

def login_screen(page: ft.Page, on_success):
    page.clean()
    page.title = "Login - Meu App Financeiro"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    senha = ft.TextField(
        label="Digite a senha",
        password=True,
        can_reveal_password=True,
        width=250,
    )

    mensagem = ft.Text("", color="red")

    def verificar_login(e):
        if senha.value == APP_PASSWORD:
            on_success()
        else:
            mensagem.value = "Senha incorreta!"
            page.update()

    btn_login = ft.ElevatedButton("Entrar", on_click=verificar_login)

    page.add(
        ft.Column(
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("Meu App Financeiro", size=22, weight=ft.FontWeight.BOLD),
                senha,
                btn_login,
                mensagem,
            ],
        )
    )

# =============================================================================
# CLASSE PRINCIPAL DA APLICAÇÃO
# =============================================================================

class FinancialApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.todas_transacoes = []
        self.todas_metas = []
        self.mes_selecionado = datetime.now()
        self.id_em_edicao = ft.Text(value=None, visible=False)
        self.selecionando_data_para = ""
        
        # Inicializar componentes de UI
        self._init_ui_components()
        self._setup_page()
        self._init_data()

    def _init_ui_components(self):
        """Inicializa todos os componentes de UI"""
        self._init_text_components()
        self._init_form_components()
        self._init_cards()
        self._init_views()
        self._init_dialogs_and_pickers()

    def _init_text_components(self):
        """Inicializa componentes de texto"""
        # Resumo Início
        self.txt_total_receitas = ft.Text(size=16, weight=ft.FontWeight.BOLD, color="green")
        self.txt_total_despesas = ft.Text(size=16, weight=ft.FontWeight.BOLD, color="red")
        self.txt_saldo_final = ft.Text(size=20, weight=ft.FontWeight.BOLD)
        self.txt_ultima_atualizacao = ft.Text(size=11, color="grey", italic=True)
        
        # Cofre/Metas
        self.txt_cofre_total = ft.Text("R$ 0,00", size=24, weight=ft.FontWeight.BOLD)
        
        # Dashboard
        self.txt_mes_ano = ft.Text(size=18, weight=ft.FontWeight.BOLD)
        self.txt_total_gasto_mes = ft.Text(size=16, color="red")
        self.txt_total_ganho_mes = ft.Text(size=16, color="green")
        self.txt_lucro_mes = ft.Text(size=20, weight=ft.FontWeight.BOLD)
        self.txt_resumo_filtrado_titulo = ft.Text(weight=ft.FontWeight.BOLD, size=18)
        self.txt_resumo_filtrado_valor = ft.Text(size=20, weight=ft.FontWeight.BOLD)
        
        # Relatórios
        self.data_inicio_relatorio = ft.Text(value=None)
        self.data_fim_relatorio = ft.Text(value=None)

    def _init_form_components(self):
        """Inicializa componentes de formulário"""
        # Nova Transação
        self.card_title = ft.Text("Nova Transação", size=16, weight=ft.FontWeight.BOLD)
        self.txt_descricao = ft.TextField(label="Descrição")
        self.txt_valor = ft.TextField(label="Valor (R$)", keyboard_type=ft.KeyboardType.NUMBER)
        self.txt_data_selecionada = ft.Text("Selecione uma data...")
        self.dd_categoria = ft.Dropdown(label="Categoria", options=[], expand=True)
        
        # Campo de busca
        self.campo_busca = ft.TextField(
            label="Buscar transação (descrição)...",
            prefix_icon=ft.Icons.SEARCH,
            on_submit=lambda e: self.atualizar_views(),
        )
        
        # Filtros
        self._init_filters()
        
        # Botões
        self._init_buttons()

    def _init_filters(self):
        """Inicializa filtros e dropdowns"""
        self.filtro_dashboard = ft.Tabs(
            selected_index=0,
            on_change=self.atualizar_views,
            tabs=[ft.Tab("Visão Geral"), ft.Tab("Receitas"), ft.Tab("Despesas")],
        )
        
        self.filtro_subcategoria_dashboard = ft.Dropdown(
            label="Filtrar por Categoria",
            on_change=self.atualizar_views,
            value="Todas",
            visible=False,
        )
        
        self.filtro_tipo_relatorio = ft.Dropdown(
            label="Filtrar por Tipo",
            options=[
                ft.dropdown.Option("Todas"),
                ft.dropdown.Option("Receita"),
                ft.dropdown.Option("Despesa"),
            ],
            value="Todas",
            expand=True,
            on_change=self.tipo_relatorio_changed,
        )
        
        self.filtro_categoria_relatorio = ft.Dropdown(
            label="Filtrar por Categoria",
            options=[ft.dropdown.Option("Todas")],
            value="Todas",
            expand=True,
            disabled=True,
        )

    def _init_buttons(self):
        """Inicializa botões e grupos de botões"""
        self.btn_abrir_calendario = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH, 
            on_click=self.abrir_seletor_data
        )
        
        self.btn_add_receita = ft.ElevatedButton(
            "Adicionar Receita",
            on_click=self.adicionar_transacao,
            data="Receita",
            icon=ft.Icons.ADD,
            bgcolor="green",
            color="white",
        )
        
        self.btn_add_despesa = ft.ElevatedButton(
            "Adicionar Despesa",
            on_click=self.adicionar_transacao,
            data="Despesa",
            icon=ft.Icons.REMOVE,
            bgcolor="red",
            color="white",
        )
        
        self.linha_botoes_adicionar = ft.Row([self.btn_add_despesa, self.btn_add_receita], spacing=10)
        
        # Botões de edição
        self.btn_salvar = ft.ElevatedButton(
            "Salvar", on_click=self.salvar_edicao, icon=ft.Icons.SAVE, 
            bgcolor="blue", color="white"
        )
        
        self.btn_cancelar_edicao = ft.ElevatedButton(
            "Cancelar", on_click=self.cancelar_edicao, icon=ft.Icons.CANCEL,
            bgcolor="grey", color="white",
        )
        
        self.linha_botoes_edicao = ft.Row(
            [self.btn_salvar, self.btn_cancelar_edicao], spacing=10, visible=False
        )
        
        self.radio_group_tipo_edicao = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="Despesa", label="Despesa"), 
                ft.Radio(value="Receita", label="Receita")
            ]),
            value="Despesa",
            visible=False,
        )

    def _init_cards(self):
        """Inicializa cards da interface"""
        # Card Resumo
        self.card_resumo = ft.Card(
            elevation=5,
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Text("Resumo do Mês", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Icon(ft.Icons.ARROW_UPWARD, color="green"),
                        ft.Text("Receitas:"),
                        self.txt_total_receitas,
                    ]),
                    ft.Row([
                        ft.Icon(ft.Icons.ARROW_DOWNWARD, color="red"),
                        ft.Text("Despesas:"),
                        self.txt_total_despesas,
                    ]),
                    ft.Divider(),
                    ft.Row([
                        ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET),
                        ft.Text("Saldo:", size=18, weight=ft.FontWeight.BOLD),
                        self.txt_saldo_final,
                    ]),
                    self.txt_ultima_atualizacao,
                ]),
            ),
        )
        
        # Card Cofre
        self.card_cofre = ft.Card(
            elevation=5,
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Row([
                        ft.Text("Cofre (Metas)", size=16, weight=ft.FontWeight.BOLD),
                        ft.Icon(ft.Icons.SAVINGS_OUTLINED),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    self.txt_cofre_total,
                    ft.Text("Valor atual somado das suas metas"),
                    ft.OutlinedButton("Gerenciar Metas", on_click=lambda e: self.ir_para_carteira()),
                ]),
            ),
        )
        
        # Card Nova Transação
        self.card_nova_transacao = ft.Card(
            elevation=5,
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    self.card_title,
                    self.radio_group_tipo_edicao,
                    self.txt_descricao,
                    self.txt_valor,
                    ft.Row([self.txt_data_selecionada, self.btn_abrir_calendario]),
                    ft.Row(
                        controls=[
                            self.dd_categoria,
                            ft.IconButton(
                                icon=ft.Icons.SYNC,
                                tooltip="Atualizar Categorias",
                                on_click=self.atualizar_opcoes_categoria,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    self.linha_botoes_adicionar,
                    self.linha_botoes_edicao,
                ]),
            ),
        )
        
        # Cards Dashboard
        self._init_dashboard_cards()

    def _init_dashboard_cards(self):
        """Inicializa cards específicos do dashboard"""
        # Gráfico
        self.grafico_pizza = ft.PieChart(sections=[], center_space_radius=40, expand=1)
        self.grafico_legenda = ft.Column(spacing=5)
        self.card_grafico_titulo = ft.Text("Visão Geral do Mês", size=16, weight=ft.FontWeight.BOLD)
        
        self.card_grafico = ft.Card(
            elevation=5,
            visible=False,
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    self.card_grafico_titulo,
                    ft.Row(
                        controls=[self.grafico_pizza, self.grafico_legenda],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
        )
        
        # Histórico
        self.historico_container = ft.Column(spacing=10, visible=False)
        self.ver_transacoes_btn = ft.Container(
            content=ft.Row([
                ft.Text("Ver transações"), 
                ft.Icon(ft.Icons.CHEVRON_RIGHT)
            ], alignment=ft.MainAxisAlignment.CENTER),
            on_click=self.toggle_historico_visibility,
            border_radius=5,
            ink=True,
        )
        
        # Cards de resumo dashboard
        self.card_resumo_dashboard_geral = ft.Card(
            elevation=5,
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Row([ft.Text("Total Ganho:"), self.txt_total_ganho_mes],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("Total Gasto:"), self.txt_total_gasto_mes],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    ft.Row([ft.Text("Lucro do Mês:", weight=ft.FontWeight.BOLD, size=18), self.txt_lucro_mes],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ]),
            ),
        )
        
        self.card_resumo_dashboard_filtrado = ft.Card(
            elevation=5,
            visible=False,
            content=ft.Container(
                padding=15,
                content=ft.Row([
                    self.txt_resumo_filtrado_titulo, 
                    self.txt_resumo_filtrado_valor
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ),
        )

    def _init_views(self):
        """Inicializa as views principais"""
        # Seletor de mês
        self.mes_selector = ft.Row([
            ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=self.mudar_mes, data="prev"),
            self.txt_mes_ano,
            ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=self.mudar_mes, data="next"),
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        # Views principais
        self.inicio_view = ft.Column([
            self.card_cofre, 
            self.card_resumo, 
            self.card_nova_transacao
        ], spacing=15, scroll=ft.ScrollMode.AUTO, 
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        
        self.dashboard_view = ft.Column(
            controls=[],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            visible=False,
            expand=True,
        )
        
        self.carteira_view = ft.Column([
            ft.Text("Carteira", size=24, weight=ft.FontWeight.BOLD),
        ], spacing=15, scroll=ft.ScrollMode.AUTO, 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)
        
        # Views de configuração e relatórios
        self._init_config_views()

    def _init_config_views(self):
        """Inicializa views de configuração e relatórios"""
        self.lista_categorias_view = ft.ListView(expand=True, spacing=10)
        
        self.configuracoes_view = ft.Column([
            ft.Text("Ajustes", size=24, weight=ft.FontWeight.BOLD),
            ft.Card(
                elevation=4,
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Gerenciar Categorias", weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=self.lista_categorias_view,
                            height=200,
                            border=ft.border.all(1, ft.Colors.with_opacity(0.5, "white")),
                            border_radius=5,
                            padding=10
                        ),
                        ft.Row([
                            ft.ElevatedButton(
                                "Adicionar Categoria",
                                on_click=self.adicionar_nova_categoria,
                                icon=ft.Icons.ADD
                            ),
                        ], alignment=ft.MainAxisAlignment.END),
                    ])
                )
            ),
        ], spacing=15, scroll=ft.ScrollMode.AUTO, visible=False)
        
        self.relatorios_view = ft.Column([
            ft.Text("Relatórios", size=24, weight=ft.FontWeight.BOLD),
            ft.Card(
                elevation=4,
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Filtros do Relatório", weight=ft.FontWeight.BOLD),
                        ft.Row([self.filtro_tipo_relatorio, self.filtro_categoria_relatorio]),
                        ft.Divider(height=10),
                        ft.Text("Selecione um Período"),
                        ft.Row([
                            ft.Text("De:"), self.data_inicio_relatorio,
                            ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, 
                                        on_click=self.abrir_datepicker_relatorio, data="inicio"),
                            ft.Text("Até:"), self.data_fim_relatorio,
                            ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, 
                                        on_click=self.abrir_datepicker_relatorio, data="fim"),
                        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                        ft.Row([
                            ft.ElevatedButton("Mês Atual", on_click=self.definir_periodo_relatorio, 
                                            data="mes", expand=True),
                            ft.ElevatedButton("3 Meses", on_click=self.definir_periodo_relatorio, 
                                            data="3_meses", expand=True),
                        ]),
                        ft.Row([
                            ft.ElevatedButton("6 Meses", on_click=self.definir_periodo_relatorio, 
                                            data="6_meses", expand=True),
                            ft.ElevatedButton("1 Ano", on_click=self.definir_periodo_relatorio, 
                                            data="ano", expand=True),
                        ]),
                        ft.Divider(height=20),
                        ft.ElevatedButton(
                            "Gerar e Salvar PDF", icon=ft.Icons.PICTURE_AS_PDF,
                            bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE,
                            on_click=self.iniciar_salvamento_pdf,
                            expand=True
                        ),
                    ])
                )
            )
        ], spacing=15, scroll=ft.ScrollMode.AUTO, visible=False)

    def _init_dialogs_and_pickers(self):
        """Inicializa diálogos e seletores"""
        self.dialogo_confirmacao = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text("Você tem certeza que deseja apagar este registro?"),
            actions=[
                ft.TextButton("Cancelar", on_click=self.fechar_dialogo),
                ft.TextButton("Confirmar", on_click=self.confirmar_exclusao),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.seletor_data = ft.DatePicker(on_change=self.data_selecionada)
        self.seletor_data_relatorio = ft.DatePicker(on_change=self.data_relatorio_selecionada)
        self.file_picker_salvar_pdf = ft.FilePicker(on_result=self.salvar_pdf_result)

    def _setup_page(self):
        """Configura a página principal"""
        self.page.clean()
        self.page.title = "Meu App Financeiro"
        self.page.window_width = 450
        self.page.window_height = 700
        self.page.theme_mode = ft.ThemeMode.DARK
        
        # Configurar navegação
        self.page.navigation_bar = ft.NavigationBar(
            selected_index=0,
            on_change=self.navigate,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Início"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.PIE_CHART_OUTLINE,
                    selected_icon=ft.Icons.PIE_CHART,
                    label="Dashboard",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED,
                    selected_icon=ft.Icons.ACCOUNT_BALANCE_WALLET,
                    label="Carteira",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.ASSESSMENT_OUTLINED, 
                    selected_icon=ft.Icons.ASSESSMENT, 
                    label="Relatórios"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label="Ajustes",
                ),
            ],
        )
        
        # FAB
        self.page.floating_action_button = ft.FloatingActionButton(
            icon=ft.Icons.ADD, on_click=self.abrir_dialogo_nova_meta
        )
        
        # Overlay
        self.page.overlay.extend([
            self.file_picker_salvar_pdf, 
            self.seletor_data, 
            self.seletor_data_relatorio
        ])
        
        # Layout
        self.page.add(
            ft.Column(
                expand=True,
                controls=[
                    ft.Container(
                        expand=True,
                        padding=ft.padding.only(top=40, left=15, right=15, bottom=15),
                        content=ft.Stack([
                            self.inicio_view, 
                            self.dashboard_view, 
                            self.carteira_view, 
                            self.relatorios_view, 
                            self.configuracoes_view
                        ]),
                    )
                ],
            )
        )

    def _init_data(self):
        """Inicializa dados do banco"""
        db.criar_tabelas(self.page)
        self.carregar_dados_iniciais()
        self.carregar_metas()
        self.carregar_e_exibir_categorias()
        
        # Carregar timestamp salvo
        timestamp_salvo = db.get_config_value_db(self.page, 'ultima_alteracao')
        if timestamp_salvo:
            self.txt_ultima_atualizacao.value = timestamp_salvo
        else:
            self.txt_ultima_atualizacao.value = "Nenhuma alteração registrada."
        
        # Atualizar opções de categoria
        self.dd_categoria.options = [
            ft.dropdown.Option(cat['nome']) for cat in db.buscar_categorias_db(self.page)
        ]
        
        self.page.floating_action_button.visible = False
        self.page.update()

    # =============================================================================
    # MÉTODOS DE ATUALIZAÇÃO DE TIMESTAMP E DADOS
    # =============================================================================

    def atualizar_timestamp_permanente(self):
        """Atualiza o texto da UI e salva a data no banco de dados."""
        now_str = f"Última alteração: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}"
        self.txt_ultima_atualizacao.value = now_str
        db.set_config_value_db(self.page, 'ultima_alteracao', now_str)
        self.page.update()

    def carregar_dados_iniciais(self):
        self.todas_transacoes = db.buscar_transacoes_db(self.page)
        self.atualizar_views()

    def atualizar_views(self, e=None):
        """Carrega as transações do banco (com busca opcional), filtra por mês selecionado e atualiza UI."""
        termo = self.campo_busca.value.strip() if self.campo_busca.value else None
        transacoes = db.buscar_transacoes_db(self.page, termo_busca=termo)

        transacoes_do_mes = [
            t for t in transacoes
            if datetime.strptime(t["data"], "%d/%m/%Y").month == self.mes_selecionado.month
            and datetime.strptime(t["data"], "%d/%m/%Y").year == self.mes_selecionado.year
        ]

        self.atualizar_resumo_inicio(transacoes_do_mes)
        self.txt_mes_ano.value = f"{month_name[self.mes_selecionado.month].capitalize()} {self.mes_selecionado.year}"
        self.atualizar_dashboard_view(transacoes_do_mes)
        self.page.update()

    # =============================================================================
    # MÉTODOS DE INTERFACE - RESUMO E DASHBOARD
    # =============================================================================

    def atualizar_resumo_inicio(self, transacoes):
        total_receitas = sum(float(t["valor"]) for t in transacoes if t["tipo"] == "Receita")
        total_despesas = sum(float(t["valor"]) for t in transacoes if t["tipo"] == "Despesa")
        saldo = total_receitas - total_despesas

        self.txt_total_receitas.value = f"R$ {total_receitas:,.2f}"
        self.txt_total_despesas.value = f"R$ {total_despesas:,.2f}"

        cor_saldo = "green" if saldo >= 0 else "red"
        self.txt_saldo_final.value = f"R$ {saldo:,.2f}"
        self.txt_saldo_final.color = cor_saldo

    def mudar_mes(self, e):
        if e.control.data == "prev":
            self.mes_selecionado = self.mes_selecionado.replace(day=1) - timedelta(days=1)
        elif e.control.data == "next":
            proximo_mes = self.mes_selecionado.replace(day=1) + timedelta(days=32)
            self.mes_selecionado = proximo_mes.replace(day=1)

        self.filtro_dashboard.selected_index = 0
        self.filtro_subcategoria_dashboard.value = "Todas"
        self.atualizar_views()

    def atualizar_dashboard_view(self, transacoes):
        filtro_selecionado = self.filtro_dashboard.selected_index
        self.filtro_subcategoria_dashboard.visible = False

        if filtro_selecionado == 0:  # Visão Geral
            transacoes_para_exibir = transacoes
            self.gerar_grafico_geral(transacoes)
            self.card_resumo_dashboard_geral.visible = True
            self.card_resumo_dashboard_filtrado.visible = False
        else:  # Receitas ou Despesas
            tipo_filtro = "Receita" if filtro_selecionado == 1 else "Despesa"

            categorias_do_tipo = sorted(list(set([
                t["categoria"] for t in transacoes if t["tipo"] == tipo_filtro
            ])))
            
            if categorias_do_tipo:
                self.filtro_subcategoria_dashboard.visible = True
                opcoes_filtro = [ft.dropdown.Option("Todas")] + [
                    ft.dropdown.Option(c) for c in categorias_do_tipo
                ]
                self.filtro_subcategoria_dashboard.options = opcoes_filtro
                if self.filtro_subcategoria_dashboard.value not in [opt.key for opt in opcoes_filtro]:
                    self.filtro_subcategoria_dashboard.value = "Todas"

            transacoes_do_tipo = [t for t in transacoes if t["tipo"] == tipo_filtro]
            subcategoria_selecionada = self.filtro_subcategoria_dashboard.value

            if subcategoria_selecionada == "Todas":
                transacoes_para_exibir = transacoes_do_tipo
            else:
                transacoes_para_exibir = [
                    t for t in transacoes_do_tipo
                    if t["categoria"] == subcategoria_selecionada
                ]

            self.gerar_grafico_por_tipo(transacoes_do_tipo, tipo_filtro)
            self.card_resumo_dashboard_geral.visible = False
            self.card_resumo_dashboard_filtrado.visible = True

            total_filtrado = sum(float(t["valor"]) for t in transacoes_para_exibir)

            if subcategoria_selecionada == "Todas":
                self.txt_resumo_filtrado_titulo.value = f"Total de {tipo_filtro}s"
            else:
                self.txt_resumo_filtrado_titulo.value = f"Total em '{subcategoria_selecionada}'"

            self.txt_resumo_filtrado_valor.value = f"R$ {total_filtrado:,.2f}"
            self.txt_resumo_filtrado_valor.color = "green" if tipo_filtro == "Receita" else "red"

        self.atualizar_historico(transacoes_para_exibir)

        total_gasto = sum(float(t["valor"]) for t in transacoes if t["tipo"] == "Despesa")
        total_ganho = sum(float(t["valor"]) for t in transacoes if t["tipo"] == "Receita")
        lucro = total_ganho - total_gasto

        self.txt_total_gasto_mes.value = f"R$ {total_gasto:,.2f}"
        self.txt_total_ganho_mes.value = f"R$ {total_ganho:,.2f}"
        self.txt_lucro_mes.value = f"R$ {lucro:,.2f}"
        self.txt_lucro_mes.color = "green" if lucro >= 0 else "red"

        self.dashboard_view.controls.clear()
        self.dashboard_view.controls.extend([
            self.mes_selector,
            self.campo_busca,
            self.filtro_dashboard,
            self.filtro_subcategoria_dashboard,
            self.card_grafico,
            self.ver_transacoes_btn,
            self.historico_container,
            self.card_resumo_dashboard_geral,
            self.card_resumo_dashboard_filtrado,
        ])

    # =============================================================================
    # MÉTODOS DE GRÁFICOS
    # =============================================================================

    def gerar_grafico_geral(self, transacoes):
        self.card_grafico_titulo.value = "Receitas x Despesas"
        self.grafico_legenda.controls.clear()
        
        total_receitas = sum(float(t["valor"]) for t in transacoes if t["tipo"] == "Receita")
        total_despesas = sum(float(t["valor"]) for t in transacoes if t["tipo"] == "Despesa")

        soma_total = total_receitas + total_despesas
        if soma_total == 0:
            self.card_grafico.visible = False
            return

        self.card_grafico.visible = True

        porc_receitas = (total_receitas / soma_total * 100) if soma_total > 0 else 0
        porc_despesas = (total_despesas / soma_total * 100) if soma_total > 0 else 0

        self.grafico_pizza.sections = [
            ft.PieChartSection(
                value=total_receitas, title=f"{porc_receitas:.0f}%", color="green", radius=80
            ),
            ft.PieChartSection(
                value=total_despesas, title=f"{porc_despesas:.0f}%", color="red", radius=80
            ),
        ]

        if total_receitas > 0:
            self.grafico_legenda.controls.append(
                ft.Row([
                    ft.Container(width=15, height=15, bgcolor="green", border_radius=10),
                    ft.Text(f"Receitas ({porc_receitas:.1f}%)"),
                ])
            )
        if total_despesas > 0:
            self.grafico_legenda.controls.append(
                ft.Row([
                    ft.Container(width=15, height=15, bgcolor="red", border_radius=10),
                    ft.Text(f"Despesas ({porc_despesas:.1f}%)"),
                ])
            )

    def gerar_grafico_por_tipo(self, transacoes, tipo):
        self.card_grafico_titulo.value = f"Composição de {tipo}s"
        self.grafico_legenda.controls.clear()

        if not transacoes:
            self.card_grafico.visible = False
            return

        self.card_grafico.visible = True

        total_tipo = sum(float(t["valor"]) for t in transacoes)

        dados_por_categoria = {}
        for t in transacoes:
            dados_por_categoria[t["categoria"]] = dados_por_categoria.get(t["categoria"], 0) + float(t["valor"])

        if tipo == "Receita":
            cores = itertools.cycle(["green", "orange", "#36A2EB", "#4BC0C0", "#9966FF"])
        else:
            cores = itertools.cycle(["red", "orange", "#FFCE56", "#FF9F40", "#FF6384"])

        chart_sections = []
        for categoria, valor in dados_por_categoria.items():
            cor_atual = next(cores)
            porcentagem = (valor / total_tipo * 100) if total_tipo > 0 else 0

            chart_sections.append(
                ft.PieChartSection(
                    value=valor,
                    title=f"{porcentagem:.0f}%",
                    title_style=ft.TextStyle(size=12, color="white", weight=ft.FontWeight.BOLD),
                    color=cor_atual,
                    radius=80,
                )
            )

            self.grafico_legenda.controls.append(
                ft.Row([
                    ft.Container(width=15, height=15, bgcolor=cor_atual, border_radius=7),
                    ft.Text(f"{categoria} ({porcentagem:.1f}%)"),
                ])
            )

        self.grafico_pizza.sections = chart_sections

    def atualizar_historico(self, transacoes):
        self.historico_container.controls.clear()
        if not transacoes:
            self.historico_container.controls.append(
                ft.Text("Nenhuma transação encontrada para este filtro.", text_align=ft.TextAlign.CENTER)
            )
        for t in transacoes:
            self.historico_container.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(f"{t['descricao']} ({t['categoria']})", weight=ft.FontWeight.BOLD),
                                ft.Text(t["data"], color="grey", size=12),
                            ],
                            expand=True,
                            spacing=1,
                        ),
                        ft.Row(
                            spacing=0,
                            controls=[
                                ft.Text(
                                    f"{'+' if t['tipo'] == 'Receita' else '-'} R$ {float(t['valor']):,.2f}",
                                    color="green" if t["tipo"] == "Receita" else "red",
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_color="blue",
                                    on_click=lambda e, transacao=t: self.iniciar_edicao(transacao),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color="red",
                                    on_click=lambda e, transacao=t: self.abrir_dialogo_confirmacao(transacao),
                                ),
                            ],
                        ),
                    ],
                )
            )

    def toggle_historico_visibility(self, e):
        self.historico_container.visible = not self.historico_container.visible
        self.page.update()

    # =============================================================================
    # MÉTODOS DE TRANSAÇÃO
    # =============================================================================

    def adicionar_transacao(self, e):
        tipo = e.control.data  # "Receita" ou "Despesa"
        if not all([
            self.txt_descricao.value,
            self.txt_valor.value,
            self.dd_categoria.value,
            self.txt_data_selecionada.value != "Selecione uma data...",
        ]):
            self.page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        try:
            valor = float(self.txt_valor.value)
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("O valor deve ser um número!"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Validar categoria
        categorias_do_tipo = [cat['nome'] for cat in db.buscar_categorias_db(self.page, tipo=tipo)]
        if categorias_do_tipo and self.dd_categoria.value not in categorias_do_tipo:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"A categoria '{self.dd_categoria.value}' não pertence a {tipo}. Selecione outra ou crie em Ajustes."),
                bgcolor="orange",
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        db.adicionar_transacao_db(
            self.page, tipo, self.txt_descricao.value, valor, 
            self.dd_categoria.value, self.txt_data_selecionada.value
        )

        self.txt_descricao.value, self.txt_valor.value, self.dd_categoria.value = "", "", None
        self.txt_data_selecionada.value = "Selecione uma data..."
        self.atualizar_timestamp_permanente()
        self.carregar_dados_iniciais()

    def iniciar_edicao(self, transacao):
        self.card_title.value = "Editar Transação"
        self.id_em_edicao.value = transacao["id"]
        self.linha_botoes_adicionar.visible = False
        self.linha_botoes_edicao.visible = True
        self.radio_group_tipo_edicao.visible = True

        self.radio_group_tipo_edicao.value = transacao["tipo"]
        self.txt_descricao.value = transacao["descricao"]
        self.txt_valor.value = str(transacao["valor"])
        self.dd_categoria.value = transacao["categoria"]
        self.txt_data_selecionada.value = transacao["data"]
        self.page.update()

    def salvar_edicao(self, e):
        if not all([self.txt_descricao.value, self.txt_valor.value, self.dd_categoria.value]):
            self.page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        try:
            valor = float(self.txt_valor.value)
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("O valor deve ser um número!"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Validar categoria na edição
        tipo = self.radio_group_tipo_edicao.value
        categorias_do_tipo = [cat['nome'] for cat in db.buscar_categorias_db(self.page, tipo=tipo)]
        if categorias_do_tipo and self.dd_categoria.value not in categorias_do_tipo:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"A categoria '{self.dd_categoria.value}' não pertence a {tipo}. Selecione outra ou ajuste em Ajustes."),
                bgcolor="orange",
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        db.update_transacao_db(
            self.page, id=int(self.id_em_edicao.value), tipo=tipo,
            descricao=self.txt_descricao.value, valor=valor,
            categoria=self.dd_categoria.value, data=self.txt_data_selecionada.value
        )
        self.cancelar_edicao(None)
        self.carregar_dados_iniciais()

    def cancelar_edicao(self, e):
        self.card_title.value = "Nova Transação"
        self.id_em_edicao.value = None
        self.linha_botoes_adicionar.visible = True
        self.linha_botoes_edicao.visible = False
        self.radio_group_tipo_edicao.visible = False

        self.txt_descricao.value, self.txt_valor.value, self.dd_categoria.value = "", "", None
        self.txt_data_selecionada.value = "Selecione uma data..."
        self.page.update()

    def deletar_transacao(self, transacao_a_deletar):
        db.deletar_transacao_db(self.page, transacao_a_deletar["id"])
        self.carregar_dados_iniciais()

    def abrir_dialogo_confirmacao(self, transacao):
        self.dialogo_confirmacao.data = transacao
        self.page.open(self.dialogo_confirmacao)

    def fechar_dialogo(self, e):
        self.page.close(self.dialogo_confirmacao)

    def confirmar_exclusao(self, e):
        self.deletar_transacao(self.dialogo_confirmacao.data)
        self.page.close(self.dialogo_confirmacao)

    def atualizar_opcoes_categoria(self, e):
        """Força a atualização das opções do dropdown de categoria ao focar."""
        try:
            categorias_db = db.buscar_categorias_db(self.page)
            opcoes = [ft.dropdown.Option(cat['nome']) for cat in categorias_db]
            self.dd_categoria.options = opcoes
            self.page.update()
        except Exception as ex:
            print(f"ERRO AO ATUALIZAR OPÇÕES: {ex}")

    # =============================================================================
    # MÉTODOS DE DATA
    # =============================================================================

    def data_selecionada(self, e):
        self.txt_data_selecionada.value = e.control.value.strftime("%d/%m/%Y")
        self.page.close(self.seletor_data)
        self.page.update()

    def abrir_seletor_data(self, e):
        self.page.open(self.seletor_data)

    def data_relatorio_selecionada(self, e):
        """Chamada quando uma data é escolhida no DatePicker do relatório."""
        data_formatada = e.control.value.strftime('%d/%m/%Y')
        
        if self.selecionando_data_para == "inicio":
            self.data_inicio_relatorio.value = data_formatada
        elif self.selecionando_data_para == "fim":
            self.data_fim_relatorio.value = data_formatada
        
        self.page.close(self.seletor_data_relatorio)
        self.page.update()

    def abrir_datepicker_relatorio(self, e):
        """Abre o DatePicker e armazena se é para a data de início ou fim."""
        self.selecionando_data_para = e.control.data
        self.page.open(self.seletor_data_relatorio)

    def definir_periodo_relatorio(self, e):
        """Define as datas de início e fim com base nos botões de atalho."""
        hoje = datetime.now()
        periodo = e.control.data
        
        data_fim = hoje
        
        if periodo == "mes":
            data_inicio = hoje.replace(day=1)
        elif periodo == "3_meses":
            data_inicio = hoje - relativedelta(months=3)
        elif periodo == "6_meses":
            data_inicio = hoje - relativedelta(months=6)
        elif periodo == "ano":
            data_inicio = hoje - relativedelta(years=1)
        
        self.data_inicio_relatorio.value = data_inicio.strftime('%d/%m/%Y')
        self.data_fim_relatorio.value = data_fim.strftime('%d/%m/%Y')
        self.page.update()

    # =============================================================================
    # MÉTODOS DE CATEGORIAS
    # =============================================================================

    def carregar_e_exibir_categorias(self):
        self.lista_categorias_view.controls.clear()
        categorias_db = db.buscar_categorias_db(self.page)
        if not categorias_db:
            self.lista_categorias_view.controls.append(ft.Text("Nenhuma categoria cadastrada."))
        else:
            for categoria in categorias_db:
                self.lista_categorias_view.controls.append(
                    ft.ListTile(
                        title=ft.Text(categoria['nome']),
                        subtitle=ft.Text(
                            categoria['tipo'], 
                            color="green" if categoria['tipo'] == 'Receita' else 'orange'
                        ),
                        trailing=ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color="red",
                            data=categoria['id'],
                            on_click=self.confirmar_delecao_categoria,
                        )
                    )
                )
        self.page.update()

    def adicionar_nova_categoria(self, e):
        nome_field = ft.TextField(label="Nome da Categoria")
        tipo_dropdown = ft.Dropdown(
            label="Tipo",
            options=[ft.dropdown.Option("Receita"), ft.dropdown.Option("Despesa")]
        )

        def salvar_click(ev):
            nome = nome_field.value
            tipo = tipo_dropdown.value
            if not nome or not tipo:
                self.page.snack_bar = ft.SnackBar(ft.Text("Nome e tipo são obrigatórios!"), bgcolor="orange")
                self.page.snack_bar.open = True
                self.page.update()
                return
            try:
                db.adicionar_categoria_db(self.page, nome, tipo)
                self.page.close(dialogo)
                self.carregar_e_exibir_categorias()
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Categoria '{nome}' adicionada!"), bgcolor="green")
                self.page.snack_bar.open = True
                self.page.update()
            except Exception:
                self.page.snack_bar = ft.SnackBar(ft.Text("Erro: Categoria já existe."), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nova Categoria"),
            content=ft.Column([nome_field, tipo_dropdown], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.page.close(dialogo)),
                ft.TextButton("Salvar", on_click=salvar_click),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dialogo)

    def confirmar_delecao_categoria(self, e):
        categoria_id = e.control.data
        
        def deletar_click(ev):
            db.deletar_categoria_db(self.page, categoria_id)
            self.page.close(dlg_confirm)
            self.carregar_e_exibir_categorias()

        dlg_confirm = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text("Tem certeza? Isto não afetará transações já existentes."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.page.close(dlg_confirm)),
                ft.TextButton("Excluir", on_click=deletar_click)
            ]
        )
        self.page.open(dlg_confirm)

    def tipo_relatorio_changed(self, e):
        """Atualiza as opções de categoria na tela de relatórios."""
        tipo = self.filtro_tipo_relatorio.value
        if tipo == "Todas":
            categorias_db = db.buscar_categorias_db(self.page)
            self.filtro_categoria_relatorio.disabled = False
        else:
            categorias_db = db.buscar_categorias_db(self.page, tipo=tipo)
            self.filtro_categoria_relatorio.disabled = False

        opcoes = [ft.dropdown.Option("Todas")] + [ft.dropdown.Option(cat['nome']) for cat in categorias_db]
        self.filtro_categoria_relatorio.options = opcoes
        self.filtro_categoria_relatorio.value = "Todas"
        self.page.update()

    # =============================================================================
    # MÉTODOS DE METAS
    # =============================================================================

    def atualizar_cofre_inicio(self):
        total = sum(float(m["valor_atual"]) for m in self.todas_metas)
        self.txt_cofre_total.value = f"R$ {total:,.2f}"
        self.page.update()

    def atualizar_carteira(self):
        # Limpa cards antigos, preservando o título "Carteira"
        if len(self.carteira_view.controls) > 1:
            del self.carteira_view.controls[1:]

        if not self.todas_metas:
            self.carteira_view.controls.append(
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Nenhuma meta criada ainda.", size=16),
                        ft.Text("Toque no botão + para criar sua primeira meta.", size=12, color="grey"),
                    ],
                )
            )
        else:
            for meta in self.todas_metas:
                objetivo = float(meta["valor_objetivo"])
                atual = float(meta["valor_atual"])
                progresso = (atual / objetivo) if objetivo > 0 else 0.0
                progresso = max(0.0, min(1.0, progresso))

                self.carteira_view.controls.append(
                    ft.Card(
                        elevation=5,
                        content=ft.Container(
                            padding=12,
                            content=ft.Column(
                                spacing=10,
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.Text(meta["nome"], size=18, weight=ft.FontWeight.BOLD),
                                            ft.Text(f"{progresso*100:,.0f}%", size=14),
                                        ],
                                    ),
                                    ft.Text(
                                        f"Guardado: R$ {atual:,.2f} / R$ {objetivo:,.2f}",
                                        size=13, color="grey",
                                    ),
                                    ft.ProgressBar(value=progresso, width=320),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.ElevatedButton(
                                                "Depositar", icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                                on_click=lambda e, m=meta: self.abrir_dialogo_deposito(m),
                                            ),
                                            ft.OutlinedButton(
                                                "Retirar", icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                                                on_click=lambda e, m=meta: self.abrir_dialogo_retirada(m),
                                            ),
                                            ft.IconButton(
                                                icon=ft.Icons.DELETE_OUTLINE, icon_color="red",
                                                tooltip="Excluir meta",
                                                on_click=lambda e, m=meta: self.abrir_dialogo_excluir_meta(m),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                    )
                )
        self.page.update()

    def carregar_metas(self):
        self.todas_metas = db.buscar_metas_db(self.page)
        self.atualizar_carteira()
        self.atualizar_cofre_inicio()

    def abrir_dialogo_nova_meta(self, e):
        nome = ft.TextField(label="Nome da Meta")
        valor_objetivo = ft.TextField(label="Valor Objetivo (R$)", keyboard_type=ft.KeyboardType.NUMBER)

        def salvar_meta(ev):
            if not nome.value or not valor_objetivo.value:
                self.page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"), bgcolor="orange")
                self.page.snack_bar.open = True
                self.page.update()
                return
            try:
                alvo = float(valor_objetivo.value)
                if alvo <= 0:
                    raise ValueError
                db.adicionar_meta_db(self.page, nome.value, alvo)
                self.page.close(dialogo)
                self.carregar_metas()
            except ValueError:
                self.page.snack_bar = ft.SnackBar(ft.Text("Valor objetivo inválido."), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()
            except Exception:
                self.page.snack_bar = ft.SnackBar(ft.Text("Erro ao salvar meta."), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nova Meta"),
            content=ft.Column([nome, valor_objetivo], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: self.page.close(dialogo)),
                ft.TextButton("Salvar", on_click=salvar_meta),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dialogo)

    def abrir_dialogo_deposito(self, meta):
        valor = ft.TextField(label="Valor a depositar (R$)", keyboard_type=ft.KeyboardType.NUMBER)

        def confirmar(ev):
            try:
                v = float(valor.value)
                if v <= 0:
                    raise ValueError
                
                # --- Lógica principal ---
                
                # 1. Calcula o novo valor da meta
                novo_valor_meta = float(meta["valor_atual"]) + v
                objetivo = float(meta["valor_objetivo"])
                if objetivo > 0:
                    novo_valor_meta = min(novo_valor_meta, objetivo)
                
                # 2. Atualiza o valor na tabela de metas
                db.atualizar_valor_meta_db(self.page, meta["id"], novo_valor_meta)

                # 3. CRIA A TRANSAÇÃO DE DESPESA CORRESPONDENTE
                db.adicionar_transacao_db(
                    self.page,
                    tipo="Despesa",
                    descricao=f"Depósito na meta: {meta['nome']}",
                    valor=v,
                    categoria="Depósito em Meta",  # Certifique-se que essa categoria existe!
                    data=datetime.now().strftime("%d/%m/%Y")
                )
                
                # 4. Recarrega todos os dados para atualizar a UI
                self.atualizar_timestamp_permanente()
                self.page.close(dialogo)
                self.carregar_metas() # Recarrega as metas para a view 'Carteira'
                self.carregar_dados_iniciais() # Recarrega as transações e atualiza o SALDO PRINCIPAL

            except ValueError:
                self.page.snack_bar = ft.SnackBar(ft.Text("Informe um valor positivo válido."), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as e:
                print(f"Erro ao depositar: {e}")
                self.page.snack_bar = ft.SnackBar(ft.Text("Erro ao processar o depósito."), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Depositar em {meta['nome']}"),
            content=valor,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: self.page.close(dialogo)),
                ft.TextButton("Confirmar", on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dialogo)

    def abrir_dialogo_retirada(self, meta):
        valor = ft.TextField(label="Valor a retirar (R$)", keyboard_type=ft.KeyboardType.NUMBER)

        def confirmar(ev):
            try:
                v = float(valor.value)
                if v <= 0 or v > float(meta["valor_atual"]):
                    raise ValueError("Valor inválido ou maior que o saldo da meta.")

                # --- Lógica principal ---

                # 1. Calcula o novo valor da meta
                novo_valor_meta = max(0.0, float(meta["valor_atual"]) - v)
                
                # 2. Atualiza o valor na tabela de metas
                db.atualizar_valor_meta_db(self.page, meta["id"], novo_valor_meta)

                # 3. CRIA A TRANSAÇÃO DE RECEITA CORRESPONDENTE
                db.adicionar_transacao_db(
                    self.page,
                    tipo="Receita",
                    descricao=f"Retirada da meta: {meta['nome']}",
                    valor=v,
                    categoria="Retirada de Meta", # Certifique-se que essa categoria existe!
                    data=datetime.now().strftime("%d/%m/%Y")
                )

                # 4. Recarrega todos os dados para atualizar a UI
                self.atualizar_timestamp_permanente()
                self.page.close(dialogo)
                self.carregar_metas() # Recarrega as metas para a view 'Carteira'
                self.carregar_dados_iniciais() # Recarrega as transações e atualiza o SALDO PRINCIPAL

            except ValueError as e:
                error_message = str(e) if str(e) else "Informe um valor válido e menor que o saldo da meta."
                self.page.snack_bar = ft.SnackBar(ft.Text(error_message), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as e:
                print(f"Erro ao retirar: {e}")
                self.page.snack_bar = ft.SnackBar(ft.Text("Erro ao processar a retirada."), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Retirar de {meta['nome']}"),
            content=valor,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: self.page.close(dialogo)),
                ft.TextButton("Confirmar", on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dialogo)

    def abrir_dialogo_excluir_meta(self, meta):
        def confirmar(ev):
            try:
                db.deletar_meta_db(self.page, meta["id"])
            finally:
                self.page.close(dialogo)
                self.carregar_metas()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Excluir Meta"),
            content=ft.Text(f"Tem certeza que deseja excluir a meta '{meta['nome']}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: self.page.close(dialogo)),
                ft.TextButton("Excluir", on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dialogo)

    def ir_para_carteira(self):
        self.page.navigation_bar.selected_index = 2
        self.navigate(None)

    # =============================================================================
    # MÉTODOS DE RELATÓRIOS PDF
    # =============================================================================

    def salvar_pdf_result(self, e: ft.FilePickerResultEvent):
        """Função chamada quando o usuário seleciona um local para salvar o PDF."""
        if e.path:
            self.gerar_relatorio_pdf(e.path)

    def gerar_relatorio_pdf(self, caminho_final):
        """Gera um relatório PDF completo e dinâmico com base nos filtros da tela de Relatórios."""
        if not self.data_inicio_relatorio.value or not self.data_fim_relatorio.value:
            self.page.snack_bar = ft.SnackBar(ft.Text("Por favor, selecione um período de datas."), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Arquivos temporários de gráfico
        grafico_despesas_path = "grafico_despesas.png"
        grafico_receitas_path = "grafico_receitas.png"
        grafico_temp_path = "grafico_temp.png"
        
        try:
            # Filtragem dos dados
            data_inicio = datetime.strptime(self.data_inicio_relatorio.value, "%d/%m/%Y")
            data_fim = datetime.strptime(self.data_fim_relatorio.value, "%d/%m/%Y")
            tipo_filtro = self.filtro_tipo_relatorio.value
            cat_filtro = self.filtro_categoria_relatorio.value

            transacoes_no_periodo = [
                t for t in self.todas_transacoes 
                if data_inicio <= datetime.strptime(t['data'], "%d/%m/%Y") <= data_fim
            ]
            
            transacoes_relatorio = transacoes_no_periodo
            if tipo_filtro != "Todas":
                transacoes_relatorio = [t for t in transacoes_relatorio if t['tipo'] == tipo_filtro]
            if cat_filtro != "Todas":
                transacoes_relatorio = [t for t in transacoes_relatorio if t['categoria'] == cat_filtro]

            # Construção do PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)

            if not transacoes_relatorio:
                pdf.cell(0, 10, "Relatório Financeiro", 0, 1, "C")
                pdf.set_font("Arial", "", 12)
                pdf.cell(0, 10, f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}", 0, 1, "C")
                pdf.ln(20)
                pdf.set_font("Arial", "I", 12)
                pdf.cell(0, 10, "Nenhuma transação encontrada para os filtros selecionados.", 0, 1, "C")
            else:
                # Análise dos dados
                dados_despesas_cat = {
                    c: sum(float(t['valor']) for t in transacoes_relatorio 
                          if t['tipo'] == 'Despesa' and t['categoria'] == c) 
                    for c in set(t['categoria'] for t in transacoes_relatorio if t['tipo'] == 'Despesa')
                }
                
                dados_receitas_cat = {
                    c: sum(float(t['valor']) for t in transacoes_relatorio 
                          if t['tipo'] == 'Receita' and t['categoria'] == c) 
                    for c in set(t['categoria'] for t in transacoes_relatorio if t['tipo'] == 'Receita')
                }
                
                # Título dinâmico
                if cat_filtro != "Todas":
                    titulo_pdf = f"Relatório da Categoria: {cat_filtro}"
                elif tipo_filtro != "Todas":
                    titulo_pdf = f"Relatório de {tipo_filtro}s"
                else:
                    titulo_pdf = "Relatório Financeiro Geral"
                
                pdf.cell(0, 10, titulo_pdf, 0, 1, "C")
                pdf.set_font("Arial", "", 12)
                pdf.cell(0, 10, f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}", 0, 1, "C")
                pdf.ln(10)

                # Gerar gráficos e análises conforme o tipo de relatório
                if cat_filtro != "Todas":
                    self._gerar_relatorio_categoria(pdf, transacoes_relatorio, transacoes_no_periodo, cat_filtro, tipo_filtro)
                elif tipo_filtro != "Todas":
                    dados_para_resumo = dados_receitas_cat if tipo_filtro == "Receita" else dados_despesas_cat
                    self._gerar_relatorio_tipo(pdf, dados_para_resumo, tipo_filtro, grafico_temp_path)
                else:
                    self._gerar_relatorio_geral(pdf, dados_receitas_cat, dados_despesas_cat, grafico_despesas_path, grafico_receitas_path)

                # Tabela detalhada
                if cat_filtro == "Todas":
                    pdf.add_page()
                self._gerar_tabela_transacoes(pdf, transacoes_relatorio)
            
            # Salvar o arquivo PDF
            pdf.output(caminho_final)
            self.page.snack_bar = ft.SnackBar(ft.Text("Relatório PDF salvo com sucesso!"), bgcolor="green")
            self.page.snack_bar.open = True
        
        except Exception as ex:
            traceback_str = traceback.format_exc()
            print(f"ERRO CRÍTICO AO GERAR PDF: {traceback_str}")
            dlg_erro = ft.AlertDialog(
                modal=True, 
                title=ft.Text("Ocorreu um Erro ao Gerar o PDF"), 
                content=ft.Column([
                    ft.Text("Por favor, envie um print desta tela para o desenvolvedor."), 
                    ft.TextField(value=traceback_str, multiline=True, read_only=True, filled=True)
                ], tight=True, scroll=ft.ScrollMode.AUTO), 
                actions=[ft.TextButton("Fechar", on_click=lambda _: self.page.close(dlg_erro))]
            )
            self.page.open(dlg_erro)
        
        finally:
            # Limpeza dos arquivos temporários
            for arquivo in [grafico_despesas_path, grafico_receitas_path, grafico_temp_path]:
                if os.path.exists(arquivo):
                    os.remove(arquivo)

        self.page.update()

    def _gerar_relatorio_categoria(self, pdf, transacoes_relatorio, transacoes_no_periodo, cat_filtro, tipo_filtro):
        """Gera análise específica para uma categoria"""
        total_categoria = sum(float(t['valor']) for t in transacoes_relatorio)
        num_transacoes = len(transacoes_relatorio)
        media_transacao = total_categoria / num_transacoes
        maior_transacao = max(transacoes_relatorio, key=lambda x: float(x['valor']))
        menor_transacao = min(transacoes_relatorio, key=lambda x: float(x['valor']))
        
        total_do_tipo_no_periodo = sum(
            float(t['valor']) for t in transacoes_no_periodo if t['tipo'] == tipo_filtro
        )
        relevancia = (total_categoria / total_do_tipo_no_periodo * 100) if total_do_tipo_no_periodo > 0 else 0
        
        if tipo_filtro == "Receita":
            texto_total, texto_maior, texto_menor, texto_media, texto_relevancia = (
                "Total Ganho", "Maior Receita", "Menor Receita", "Ganho Médio", "receitas"
            )
        else:
            texto_total, texto_maior, texto_menor, texto_media, texto_relevancia = (
                "Total Gasto", "Maior Despesa", "Menor Despesa", "Gasto Médio", "despesas"
            )
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Análise da Categoria", 0, 1, "L")
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 7, f"- {texto_total} na Categoria: R$ {total_categoria:,.2f}", 0, 1, "L")
        pdf.cell(0, 7, f"- Número de Transações: {num_transacoes}", 0, 1, "L")
        pdf.cell(0, 7, f"- {texto_media} por Transação: R$ {media_transacao:,.2f}", 0, 1, "L")
        pdf.cell(0, 7, f"- {texto_maior}: R$ {float(maior_transacao['valor']):,.2f} ({maior_transacao['descricao'].encode('latin-1', 'replace').decode('latin-1')})", 0, 1, "L")
        pdf.cell(0, 7, f"- {texto_menor}: R$ {float(menor_transacao['valor']):,.2f} ({menor_transacao['descricao'].encode('latin-1', 'replace').decode('latin-1')})", 0, 1, "L")
        pdf.cell(0, 7, f"- Relevância: Esta categoria representa {relevancia:.1f}% do total de suas {texto_relevancia} no período.", 0, 1, "L")
        pdf.ln(10)

    def _gerar_relatorio_tipo(self, pdf, dados_para_resumo, tipo_filtro, grafico_temp_path):
        """Gera análise por tipo (Receita ou Despesa)"""
        total_geral = sum(dados_para_resumo.values())
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Resumo de {tipo_filtro}s por Categoria", 0, 1, "L")
        pdf.set_font("Arial", "", 11)
        
        for categoria, valor in sorted(dados_para_resumo.items()):
            pdf.cell(0, 7, f"- {categoria}: R$ {valor:,.2f}", 0, 1, "L")
        
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 7, f"Total de {tipo_filtro}s: R$ {total_geral:,.2f}", "T", 1, "L")
        pdf.ln(10)
        
        if criar_imagem_grafico(dados_para_resumo, f"Composição de {tipo_filtro}s", grafico_temp_path, tipo_filtro):
            pdf.image(grafico_temp_path, x=10, y=None, w=180)

    def _gerar_relatorio_geral(self, pdf, dados_receitas_cat, dados_despesas_cat, grafico_despesas_path, grafico_receitas_path):
        """Gera análise geral (Receitas + Despesas)"""
        receitas_total = sum(dados_receitas_cat.values())
        despesas_total = sum(dados_despesas_cat.values())
        saldo = receitas_total - despesas_total
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Resumo do Período", 0, 1, "L")
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 7, f"Total de Receitas: R$ {receitas_total:,.2f}", 0, 1, "L")
        pdf.cell(0, 7, f"Total de Despesas: R$ {despesas_total:,.2f}", 0, 1, "L")
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 7, f"Saldo Final: R$ {saldo:,.2f}", 0, 1, "L")
        pdf.ln(10)
        
        if criar_imagem_grafico(dados_despesas_cat, "Composição de Despesas", grafico_despesas_path, "Despesa"):
            pdf.image(grafico_despesas_path, x=10, y=None, w=180)
        
        if criar_imagem_grafico(dados_receitas_cat, "Composição de Receitas", grafico_receitas_path, "Receita"):
            pdf.image(grafico_receitas_path, x=10, y=None, w=180)

    def _gerar_tabela_transacoes(self, pdf, transacoes_relatorio):
        """Gera tabela detalhada das transações"""
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Detalhes das Transações", 0, 1, "L")
        pdf.set_font("Arial", "B", 10)
        pdf.cell(25, 8, "Data", 1)
        pdf.cell(85, 8, "Descrição", 1)
        pdf.cell(35, 8, "Categoria", 1)
        pdf.cell(40, 8, "Valor (R$)", 1)
        pdf.ln()
        
        pdf.set_font("Arial", "", 10)
        for t in sorted(transacoes_relatorio, key=lambda x: datetime.strptime(x['data'], "%d/%m/%Y")):
            descricao = t['descricao'].encode('latin-1', 'replace').decode('latin-1')
            categoria = t['categoria'].encode('latin-1', 'replace').decode('latin-1')
            
            if t['tipo'] == 'Receita':
                pdf.set_text_color(0, 128, 0)
                valor_str = f"+{float(t['valor']):,.2f}"
            else:
                pdf.set_text_color(255, 0, 0)
                valor_str = f"-{float(t['valor']):,.2f}"
            
            pdf.cell(25, 8, t['data'], 1)
            pdf.cell(85, 8, descricao, 1)
            pdf.cell(35, 8, categoria, 1)
            pdf.cell(40, 8, valor_str, 1)
            pdf.ln()
        
        pdf.set_text_color(0, 0, 0)

    def iniciar_salvamento_pdf(self, e):
        """Gera o nome dinâmico do arquivo e abre o diálogo para salvar."""
        if not self.data_inicio_relatorio.value or not self.data_fim_relatorio.value:
            self.page.snack_bar = ft.SnackBar(ft.Text("Por favor, selecione um período de datas primeiro."), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Lógica para gerar o nome do arquivo
        tipo_filtro = self.filtro_tipo_relatorio.value
        cat_filtro = self.filtro_categoria_relatorio.value
        data_inicio = datetime.strptime(self.data_inicio_relatorio.value, "%d/%m/%Y")
        data_fim = datetime.strptime(self.data_fim_relatorio.value, "%d/%m/%Y")
        
        nome_base = "relatorio"
        nome_tipo = f"_{tipo_filtro}" if tipo_filtro != "Todas" else "_Geral"
        nome_cat = f"_{cat_filtro.replace(' ', '_')}" if cat_filtro != "Todas" else ""
        nome_datas = f"_{data_inicio.strftime('%Y-%m-%d')}_a_{data_fim.strftime('%Y-%m-%d')}"
        nome_final_arquivo = f"{nome_base}{nome_tipo}{nome_cat}{nome_datas}.pdf"

        # Chama o FilePicker com o nome já preenchido
        self.file_picker_salvar_pdf.save_file(
            dialog_title="Salvar Relatório PDF Como...",
            file_name=nome_final_arquivo,
            allowed_extensions=["pdf"]
        )

    # =============================================================================
    # MÉTODO DE NAVEGAÇÃO
    # =============================================================================

    def navigate(self, e):
        """Controla a navegação entre as telas"""
        index = self.page.navigation_bar.selected_index
        
        # Controla visibilidade das views
        self.inicio_view.visible = (index == 0)
        self.dashboard_view.visible = (index == 1)
        self.carteira_view.visible = (index == 2)
        self.relatorios_view.visible = (index == 3)
        self.configuracoes_view.visible = (index == 4)

        # Ações específicas por tela
        if index == 1:  # Dashboard
            self.atualizar_views()
        elif index == 3:  # Relatórios
            self.tipo_relatorio_changed(None)
        elif index == 4:  # Ajustes
            self.carregar_e_exibir_categorias()

        # FAB só visível na Carteira
        self.page.floating_action_button.visible = (index == 2)
        self.page.update()

# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def main(page: ft.Page):
    def iniciar_app():
        page.clean()
        FinancialApp(page)

    # Começa mostrando a tela de login
    login_screen(page, on_success=iniciar_app)

if __name__ == "__main__":
    ft.app(target=main)