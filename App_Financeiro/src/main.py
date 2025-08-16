# main.py
import flet as ft
from datetime import datetime
import itertools
# Importamos as nossas novas funções do banco de dados
import database as db

def main(page: ft.Page):
    page.title = "Meu App Financeiro"
    page.window_width = 450
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK
    page.locale = "pt_BR" 
    page.scroll = ft.ScrollMode.ADAPTIVE

    todas_transacoes = [] # Esta lista agora será um cache dos dados do DB

    categorias_despesa = [
        ft.dropdown.Option("Alimentação"), ft.dropdown.Option("Transporte"),
        ft.dropdown.Option("Lazer"), ft.dropdown.Option("Moradia"), ft.dropdown.Option("Outros"),
    ]
    categorias_receita = [
        ft.dropdown.Option("Salário"), ft.dropdown.Option("Vendas"),
        ft.dropdown.Option("Bônus"), ft.dropdown.Option("Outros"),
    ]
    todas_categorias = categorias_despesa + categorias_receita

    def carregar_dados_iniciais():
        """Carrega os dados do banco de dados para a lista em memória."""
        nonlocal todas_transacoes
        todas_transacoes = db.buscar_transacoes_db()
        atualizar_saldo()
        atualizar_historico()
        gerar_grafico()

    def deletar_transacao(transacao_a_deletar):
        # O primeiro elemento da tupla da transação é o ID
        transacao_id = transacao_a_deletar[0]
        db.deletar_transacao_db(transacao_id)
        
        # --- CORREÇÃO AQUI ---
        # ATUALIZA TIMESTAMP
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        txt_ultima_atualizacao.value = f"Última atualização: {timestamp}"

        # Recarrega todos os dados da UI para refletir a mudança
        carregar_dados_iniciais()
        page.update()

    def atualizar_saldo():
        saldo = 0.0
        for t in todas_transacoes:
            # Índices mudaram por causa do ID: valor agora é t[3] e tipo é t[1]
            valor = float(t[3])
            if t[1] == "Receita":
                saldo += valor
            else:
                saldo -= valor
        
        cor_saldo = "green" if saldo >= 0 else "red"
        txt_saldo.value = f"Saldo Atual: R$ {saldo:,.2f}"
        txt_saldo.color = cor_saldo
    
    def fechar_dialogo(e):
        page.close(dialogo_confirmacao)

    def confirmar_exclusao(e):
        deletar_transacao(dialogo_confirmacao.data)
        page.close(dialogo_confirmacao)
    
    def abrir_dialogo_confirmacao(transacao):
        dialogo_confirmacao.data = transacao
        page.open(dialogo_confirmacao)

    def atualizar_historico():
        historico_container.controls.clear()
        
        for t in todas_transacoes:
            # Desempacotamento com os novos índices
            id_t, tipo, descricao, valor, categoria, data = t
            item = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(f"{descricao} ({categoria})", weight=ft.FontWeight.BOLD),
                            ft.Text(data, color="grey", size=12),
                        ],
                        expand=True, spacing=1,
                    ),
                    ft.Row(
                       spacing=0,
                       controls=[
                            ft.Text(
                                f"{'+' if tipo == 'Receita' else '-'} R$ {float(valor):,.2f}", 
                                color="green" if tipo == 'Receita' else "red", 
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE, icon_color="red",
                                tooltip="Deletar Transação",
                                on_click=lambda _, transacao=t: abrir_dialogo_confirmacao(transacao),
                            )
                        ]
                    )
                ]
            )
            historico_container.controls.append(item)
    
    def adicionar_transacao(e):
        data_escolhida = txt_data_selecionada.value
        if data_escolhida == "Selecione uma data...":
             page.snack_bar = ft.SnackBar(ft.Text("Por favor, selecione uma data!"), bgcolor="orange")
             page.snack_bar.open = True
             page.update()
             return

        tipo = e.control.data
        descricao = txt_descricao.value
        valor_str = txt_valor.value
        categoria = dd_categoria.value

        if not all([descricao, valor_str, categoria]):
            page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return
        
        try:
            valor = float(valor_str)
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("O valor deve ser um número!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return
        
        db.adicionar_transacao_db(tipo, descricao, valor, categoria, data_escolhida)
        
        # --- CORREÇÃO AQUI ---
        # ATUALIZA TIMESTAMP
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        txt_ultima_atualizacao.value = f"Última atualização: {timestamp}"

        # Limpa os campos e recarrega a UI
        txt_descricao.value = ""
        txt_valor.value = ""
        dd_categoria.value = None
        txt_data_selecionada.value = "Selecione uma data..."
        carregar_dados_iniciais()
        page.update()

    def data_selecionada(e):
        data = seletor_data.value.strftime("%d/%m/%Y")
        txt_data_selecionada.value = data
        seletor_data.open = False
        page.update()

    def abrir_seletor_data(e):
        seletor_data.open = True
        page.update()
        
    def gerar_grafico():
        gastos_por_categoria = {}
        for t in todas_transacoes:
            if t[1] == 'Despesa': # t[1] agora é o tipo
                categoria = t[4] # t[4] agora é a categoria
                valor = float(t[3]) # t[3] agora é o valor
                if categoria in gastos_por_categoria:
                    gastos_por_categoria[categoria] += valor
                else:
                    gastos_por_categoria[categoria] = valor
        
        if not gastos_por_categoria:
            card_grafico.visible = False
            return

        cores = itertools.cycle([
            ft.Colors.RED, ft.Colors.ORANGE, ft.Colors.YELLOW,
            ft.Colors.GREEN, ft.Colors.BLUE, ft.Colors.PURPLE, ft.Colors.PINK
        ])
        
        total_despesas = sum(gastos_por_categoria.values())
        fatias = []
        for categoria, total in gastos_por_categoria.items():
            cor_atual = next(cores)
            fatias.append(
                ft.PieChartSection(
                    value=total,
                    title=f"{(total/total_despesas):.0%}",
                    title_style=ft.TextStyle(size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    color=cor_atual,
                    radius=80,
                )
            )
        
        grafico_pizza.sections = fatias
        card_grafico.visible = True

    # --- Componentes da Interface ---
    dialogo_confirmacao = ft.AlertDialog(
        modal=True, title=ft.Text("Confirmar Exclusão"),
        content=ft.Text("Você tem certeza que deseja apagar este registro?"),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_dialogo),
            ft.TextButton("Confirmar", on_click=confirmar_exclusao),
        ], actions_alignment=ft.MainAxisAlignment.END,
    )
    page.dialog = dialogo_confirmacao
    txt_saldo = ft.Text("Saldo Atual: R$ 0,00", size=24, weight=ft.FontWeight.BOLD)
    txt_ultima_atualizacao = ft.Text("Última atualização: -", size=12, italic=True, color="grey")
    seletor_data = ft.DatePicker(
        on_change=data_selecionada, first_date=datetime(2020, 1, 1),
        last_date=datetime(2030, 12, 31), help_text="Selecione a data da transação",
        cancel_text="Cancelar", confirm_text="Confirmar"
    )
    page.overlay.append(seletor_data)
    txt_descricao = ft.TextField(label="Descrição")
    txt_valor = ft.TextField(label="Valor (R$)", keyboard_type=ft.KeyboardType.NUMBER)
    txt_data_selecionada = ft.Text("Selecione uma data...", color="grey")
    btn_abrir_calendario = ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, on_click=abrir_seletor_data, tooltip="Escolher Data")
    dd_categoria = ft.Dropdown(label="Categoria", options=todas_categorias)
    btn_add_receita = ft.ElevatedButton(text="Adicionar Receita", on_click=adicionar_transacao, data="Receita", icon=ft.Icons.ADD, bgcolor="green", color="white")
    btn_add_despesa = ft.ElevatedButton(text="Adicionar Despesa", on_click=adicionar_transacao, data="Despesa", icon=ft.Icons.REMOVE, bgcolor="red", color="white")
    card_nova_transacao = ft.Card(
        elevation=10,
        content=ft.Container(
            padding=ft.padding.all(15),
            content=ft.Column(
                controls=[
                    ft.Text("Nova Transação", size=18, weight=ft.FontWeight.BOLD),
                    txt_descricao, txt_valor,
                    ft.Row([txt_data_selecionada, btn_abrir_calendario]),
                    dd_categoria,
                    ft.Row([btn_add_despesa, btn_add_receita], spacing=10),
                ]
            )
        )
    )
    grafico_pizza = ft.PieChart(sections=[], center_space_radius=40)
    card_grafico = ft.Card(
        elevation=10, visible=False,
        content=ft.Container(
            padding=ft.padding.all(15),
            content=ft.Column(
                controls=[
                    ft.Text("Gastos por Categoria", size=18, weight=ft.FontWeight.BOLD),
                    grafico_pizza,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
    )
    historico_container = ft.Column(spacing=10)
    
    # Adiciona tudo à página
    page.add(
        ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE, expand=True,
            controls=[
                txt_saldo, txt_ultima_atualizacao, ft.Divider(),
                card_nova_transacao, ft.Divider(),
                card_grafico, ft.Text("Histórico", size=18),
                historico_container
            ]
        )
    )

    # Carregamento inicial dos dados do DB
    carregar_dados_iniciais()
    page.update()

ft.app(target=main)