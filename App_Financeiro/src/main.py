# main.py
import flet as ft
from datetime import datetime
import itertools
import database as db

def main(page: ft.Page):
    page.title = "Meu App Financeiro"
    page.window_width = 450
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK
    page.locale = "pt_BR" 
    page.scroll = ft.ScrollMode.ADAPTIVE

    todas_transacoes = []
    id_em_edicao = ft.Text(value=None, visible=False)

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
        nonlocal todas_transacoes
        todas_transacoes = db.buscar_transacoes_db()
        atualizar_saldo()
        atualizar_historico()
        gerar_grafico()

    def deletar_transacao(transacao_a_deletar):
        transacao_id = transacao_a_deletar['id']
        db.deletar_transacao_db(transacao_id)
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        txt_ultima_atualizacao.value = f"Última atualização: {timestamp}"
        carregar_dados_iniciais()
        page.update()

    def iniciar_edicao(transacao):
        id_em_edicao.value = transacao['id']
        linha_botoes_adicionar.visible = False
        btn_salvar.visible = True
        
        radio_group_tipo_edicao.value = transacao['tipo']
        txt_descricao.value = transacao['descricao']
        txt_valor.value = transacao['valor']
        dd_categoria.value = transacao['categoria']
        txt_data_selecionada.value = transacao['data']
        
        page.update()

    def salvar_edicao(e):
        if not all([txt_descricao.value, txt_valor.value, dd_categoria.value]):
            page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        try:
            valor = float(txt_valor.value)
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("O valor deve ser um número!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return
        
        db.update_transacao_db(
            id=id_em_edicao.value,
            tipo=radio_group_tipo_edicao.value,
            descricao=txt_descricao.value,
            valor=valor,
            categoria=dd_categoria.value,
            data=txt_data_selecionada.value
        )

        linha_botoes_adicionar.visible = True
        btn_salvar.visible = False
        txt_descricao.value = ""
        txt_valor.value = ""
        dd_categoria.value = None
        txt_data_selecionada.value = "Selecione uma data..."
        
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        txt_ultima_atualizacao.value = f"Última atualização: {timestamp}"
        carregar_dados_iniciais()
        page.update()

    def atualizar_saldo():
        saldo = 0.0
        for t in todas_transacoes:
            valor = float(t['valor'])
            if t['tipo'] == "Receita":
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
            item = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        controls=[
                            # --- CORREÇÃO FINAL AQUI ---
                            ft.Text(f"{t['descricao']} ({t['categoria']})", weight=ft.FontWeight.BOLD),
                            ft.Text(t['data'], color="grey", size=12),
                        ],
                        expand=True, spacing=1,
                    ),
                    ft.Row(
                       spacing=0,
                       controls=[
                            ft.Text(
                                f"{'+' if t['tipo'] == 'Receita' else '-'} R$ {float(t['valor']):,.2f}", 
                                color="green" if t['tipo'] == 'Receita' else "red", 
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.IconButton(
                                icon=ft.Icons.EDIT, icon_color="blue",
                                tooltip="Editar Transação",
                                on_click=lambda e, transacao=t: iniciar_edicao(transacao),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE, icon_color="red",
                                tooltip="Deletar Transação",
                                on_click=lambda e, transacao=t: abrir_dialogo_confirmacao(transacao),
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
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        txt_ultima_atualizacao.value = f"Última atualização: {timestamp}"
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
            if t['tipo'] == 'Despesa':
                categoria = t['categoria']
                valor = float(t['valor'])
                gastos_por_categoria[categoria] = gastos_por_categoria.get(categoria, 0) + valor
        
        if not gastos_por_categoria:
            card_grafico.visible = False
            return

        cores = itertools.cycle([ft.Colors.RED, ft.Colors.ORANGE, ft.Colors.YELLOW, ft.Colors.GREEN, ft.Colors.BLUE, ft.Colors.PURPLE, ft.Colors.PINK])
        total_despesas = sum(gastos_por_categoria.values())
        fatias = []
        for categoria, total in gastos_por_categoria.items():
            fatias.append(
                ft.PieChartSection(value=total, title=f"{(total/total_despesas):.0%}",
                title_style=ft.TextStyle(size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                color=next(cores), radius=80)
            )
        grafico_pizza.sections = fatias
        card_grafico.visible = True

    # --- Componentes da Interface ---
    dialogo_confirmacao = ft.AlertDialog(modal=True, title=ft.Text("Confirmar Exclusão"),
        content=ft.Text("Você tem certeza que deseja apagar este registro?"),
        actions=[ft.TextButton("Cancelar", on_click=fechar_dialogo), ft.TextButton("Confirmar", on_click=confirmar_exclusao)],
        actions_alignment=ft.MainAxisAlignment.END)
    page.dialog = dialogo_confirmacao
    txt_saldo = ft.Text("Saldo Atual: R$ 0,00", size=24, weight=ft.FontWeight.BOLD)
    txt_ultima_atualizacao = ft.Text("Última atualização: -", size=12, italic=True, color="grey")
    seletor_data = ft.DatePicker(on_change=data_selecionada, first_date=datetime(2020, 1, 1),
        last_date=datetime(2030, 12, 31), help_text="Selecione a data da transação",
        cancel_text="Cancelar", confirm_text="Confirmar")
    page.overlay.append(seletor_data)
    txt_descricao = ft.TextField(label="Descrição")
    txt_valor = ft.TextField(label="Valor (R$)", keyboard_type=ft.KeyboardType.NUMBER)
    txt_data_selecionada = ft.Text("Selecione uma data...", color="grey")
    btn_abrir_calendario = ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, on_click=abrir_seletor_data, tooltip="Escolher Data")
    dd_categoria = ft.Dropdown(label="Categoria", options=todas_categorias)
    
    btn_add_receita = ft.ElevatedButton(text="Adicionar Receita", on_click=adicionar_transacao, data="Receita", icon=ft.Icons.ADD, bgcolor="green", color="white")
    btn_add_despesa = ft.ElevatedButton(text="Adicionar Despesa", on_click=adicionar_transacao, data="Despesa", icon=ft.Icons.REMOVE, bgcolor="red", color="white")
    linha_botoes_adicionar = ft.Row([btn_add_despesa, btn_add_receita], spacing=10)
    btn_salvar = ft.ElevatedButton(text="Salvar Alterações", on_click=salvar_edicao, icon=ft.Icons.SAVE, bgcolor="blue", color="white", visible=False)
    
    radio_group_tipo_edicao = ft.RadioGroup(
        content=ft.Row([ft.Radio(value="Despesa", label="Despesa"), ft.Radio(value="Receita", label="Receita")]),
        value="Despesa"
    )

    card_nova_transacao = ft.Card(elevation=10,
        content=ft.Container(padding=ft.padding.all(15),
            content=ft.Column(
                controls=[
                    ft.Text("Nova Transação", size=18, weight=ft.FontWeight.BOLD),
                    radio_group_tipo_edicao,
                    txt_descricao, txt_valor,
                    ft.Row([txt_data_selecionada, btn_abrir_calendario]),
                    dd_categoria,
                    linha_botoes_adicionar,
                    btn_salvar,
                ]
            )
        )
    )
    grafico_pizza = ft.PieChart(sections=[], center_space_radius=40)
    card_grafico = ft.Card(elevation=10, visible=False,
        content=ft.Container(padding=ft.padding.all(15),
            content=ft.Column(
                controls=[ft.Text("Gastos por Categoria", size=18, weight=ft.FontWeight.BOLD), grafico_pizza],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
    )
    historico_container = ft.Column(spacing=10)
    
    page.add(
        ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True,
            controls=[
                txt_saldo, txt_ultima_atualizacao, ft.Divider(),
                card_nova_transacao, ft.Divider(),
                card_grafico, ft.Text("Histórico", size=18),
                historico_container
            ]
        )
    )

    carregar_dados_iniciais()
    page.update()

ft.app(target=main)