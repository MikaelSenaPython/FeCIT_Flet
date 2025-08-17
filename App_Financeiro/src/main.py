# main.py
import flet as ft
from datetime import datetime, timedelta
import itertools
import database as db

def main(page: ft.Page):
    page.title = "Meu App Financeiro"
    page.window_width = 450
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK

    # Garante que a tabela do DB seja criada no local correto ao iniciar
    db.criar_tabela(page)

    # --- TEMA PARA ESCONDER A BARRA DE ROLAGEM ---
    page.theme = ft.Theme(
        scrollbar_theme=ft.ScrollbarTheme(
            thumb_visibility=False,
            thickness=0
        )
    )

    todas_transacoes = []
    id_em_edicao = ft.Text(value=None, visible=False)

    # --- FUNÇÃO PRINCIPAL DE FILTRAGEM ---
    def aplicar_filtros_e_atualizar(e=None):
        """
        Aplica todos os filtros selecionados, atualiza a interface e fecha o painel.
        """
        transacoes_filtradas = todas_transacoes[:]

        # 1. Filtro por Tipo (Receita/Despesa)
        tipo_selecionado = filtro_tipo.value
        if tipo_selecionado != "Todos":
            transacoes_filtradas = [t for t in transacoes_filtradas if t['tipo'] == tipo_selecionado]

        # 2. Filtro por Descrição
        texto_busca = filtro_descricao.value.lower() if filtro_descricao.value else ""
        if texto_busca:
            transacoes_filtradas = [
                t for t in transacoes_filtradas 
                if texto_busca in t['descricao'].lower()
            ]

        # 3. Filtro por Intervalo de Datas
        try:
            data_inicio_str = txt_data_de.value
            data_fim_str = txt_data_ate.value

            if data_inicio_str != "De:":
                data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y")
                transacoes_filtradas = [
                    t for t in transacoes_filtradas 
                    if datetime.strptime(t['data'], "%d/%m/%Y") >= data_inicio
                ]
            
            if data_fim_str != "Até:":
                data_fim = datetime.strptime(data_fim_str, "%d/%m/%Y")
                transacoes_filtradas = [
                    t for t in transacoes_filtradas 
                    if datetime.strptime(t['data'], "%d/%m/%Y") <= data_fim
                ]
        except (ValueError, TypeError):
            pass

        atualizar_saldo(transacoes_filtradas)
        atualizar_historico(transacoes_filtradas)
        gerar_grafico(transacoes_filtradas)
        
        # Fecha o painel de filtros se ele estiver aberto
        if e is not None:
            page.close(bs)
        page.update()

    def carregar_dados_iniciais():
        nonlocal todas_transacoes
        todas_transacoes = db.buscar_transacoes_db(page) # Passa 'page'
        aplicar_filtros_e_atualizar() 

    def deletar_transacao(transacao_a_deletar):
        db.deletar_transacao_db(page, transacao_a_deletar['id']) # Passa 'page'
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        nova_msg = f"Última atualização: {timestamp}"
        txt_ultima_atualizacao.value = nova_msg
        page.client_storage.set("ultima_atualizacao", nova_msg)
        carregar_dados_iniciais()

    def cancelar_edicao(e):
        """Volta ao estado inicial, cancelando a edição."""
        card_title.value = "Nova Transação"
        id_em_edicao.value = None
        linha_botoes_adicionar.visible = True
        linha_botoes_edicao.visible = False
        radio_group_tipo_edicao.visible = False
        
        txt_descricao.value = ""
        txt_valor.value = ""
        dd_categoria.value = None
        txt_data_selecionada.value = "Selecione uma data..."
        page.update()

    def iniciar_edicao(transacao):
        card_title.value = "Editar Transação"
        id_em_edicao.value = transacao['id']
        linha_botoes_adicionar.visible = False
        linha_botoes_edicao.visible = True
        radio_group_tipo_edicao.visible = True
        
        radio_group_tipo_edicao.value = transacao['tipo']
        txt_descricao.value = transacao['descricao']
        txt_valor.value = str(transacao['valor'])
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
            page, # Passa 'page'
            id=int(id_em_edicao.value), 
            tipo=radio_group_tipo_edicao.value,
            descricao=txt_descricao.value, 
            valor=valor,
            categoria=dd_categoria.value, 
            data=txt_data_selecionada.value
        )

        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        nova_msg = f"Última atualização: {timestamp}"
        txt_ultima_atualizacao.value = nova_msg
        page.client_storage.set("ultima_atualizacao", nova_msg)
        cancelar_edicao(None)
        carregar_dados_iniciais()

    def atualizar_saldo(transacoes):
        total_receitas = sum(float(t['valor']) for t in transacoes if t['tipo'] == "Receita")
        total_despesas = sum(float(t['valor']) for t in transacoes if t['tipo'] == "Despesa")
        saldo = total_receitas - total_despesas

        txt_total_receitas.value = f"R$ {total_receitas:,.2f}"
        txt_total_despesas.value = f"R$ {total_despesas:,.2f}"
        
        cor_saldo = "green" if saldo >= 0 else "red"
        txt_saldo_final.value = f"R$ {saldo:,.2f}"
        txt_saldo_final.color = cor_saldo
    
    def fechar_dialogo(e):
        page.close(dialogo_confirmacao)

    def confirmar_exclusao(e):
        deletar_transacao(dialogo_confirmacao.data)
        page.close(dialogo_confirmacao)
    
    def abrir_dialogo_confirmacao(transacao):
        dialogo_confirmacao.data = transacao
        page.open(dialogo_confirmacao)

    def atualizar_historico(transacoes):
        historico_container.controls.clear()
        if not transacoes:
            historico_container.controls.append(ft.Text("Nenhuma transação encontrada.", color="grey"))
        for t in transacoes:
            historico_container.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(f"{t['descricao']} ({t['categoria']})", weight=ft.FontWeight.BOLD),
                                ft.Text(t['data'], color="grey", size=12),
                            ], expand=True, spacing=1,
                        ),
                        ft.Row(
                            spacing=0,
                            controls=[
                                ft.Text(f"{'+' if t['tipo'] == 'Receita' else '-'} R$ {float(t['valor']):,.2f}", 
                                        color="green" if t['tipo'] == 'Receita' else "red", weight=ft.FontWeight.BOLD),
                                ft.IconButton(icon=ft.Icons.EDIT, icon_color="blue", on_click=lambda e, transacao=t: iniciar_edicao(transacao)),
                                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="red", on_click=lambda e, transacao=t: abrir_dialogo_confirmacao(transacao)),
                            ]
                        )
                    ]
                )
            )
    
    def adicionar_transacao(e):
        tipo = e.control.data # Pega o tipo do botão clicado
        if txt_data_selecionada.value == "Selecione uma data...":
            page.snack_bar = ft.SnackBar(ft.Text("Por favor, selecione uma data!"), bgcolor="orange")
            page.snack_bar.open = True
            page.update()
            return
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
        
        db.adicionar_transacao_db(page, tipo, txt_descricao.value, valor, dd_categoria.value, txt_data_selecionada.value) # Passa 'page'
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        nova_msg = f"Última atualização: {timestamp}"
        txt_ultima_atualizacao.value = nova_msg
        page.client_storage.set("ultima_atualizacao", nova_msg)
        txt_descricao.value, txt_valor.value, dd_categoria.value = "", "", None
        txt_data_selecionada.value = "Selecione uma data..."
        carregar_dados_iniciais()

    def data_selecionada(e):
        data_formatada = e.control.value.strftime("%d/%m/%Y")
        if e.control.data == "principal":
            txt_data_selecionada.value = data_formatada
        elif e.control.data == "filtro_de":
            txt_data_de.value = data_formatada
        elif e.control.data == "filtro_ate":
            txt_data_ate.value = data_formatada
        e.control.open = False
        page.update()

    def abrir_seletor_data(e):
        seletor_data.data = e.control.data
        seletor_data.open = True
        page.update()
        
    def gerar_grafico(transacoes):
        gastos_por_categoria = {}
        for t in transacoes:
            if t['tipo'] == 'Despesa':
                categoria = t['categoria']
                valor = float(t['valor'])
                gastos_por_categoria[categoria] = gastos_por_categoria.get(categoria, 0) + valor
        
        card_grafico.visible = bool(gastos_por_categoria)
        if not gastos_por_categoria:
            page.update()
            return

        cores = itertools.cycle(["red", "orange", "yellow", "green", "blue", "purple", "pink"])
        total_despesas = sum(gastos_por_categoria.values())
        grafico_pizza.sections = [
            ft.PieChartSection(
                value=total, title=f"{(total/total_despesas):.0%}",
                title_style=ft.TextStyle(size=12, color="white", weight=ft.FontWeight.BOLD),
                color=next(cores), radius=80
            ) for categoria, total in gastos_por_categoria.items()
        ]
        page.update()

    # --- Componentes da Interface (definidos uma vez) ---
    dialogo_confirmacao = ft.AlertDialog(modal=True, title=ft.Text("Confirmar Exclusão"),
        content=ft.Text("Você tem certeza?"),
        actions=[ft.TextButton("Cancelar", on_click=fechar_dialogo), ft.TextButton("Confirmar", on_click=confirmar_exclusao)],
        actions_alignment=ft.MainAxisAlignment.END)
    page.dialog = dialogo_confirmacao
    
    # Componentes para o Card de Resumo
    txt_total_receitas = ft.Text(size=18, weight=ft.FontWeight.BOLD, color="green")
    txt_total_despesas = ft.Text(size=18, weight=ft.FontWeight.BOLD, color="red")
    txt_saldo_final = ft.Text(size=22, weight=ft.FontWeight.BOLD)

    card_resumo = ft.Card(
        elevation=10,
        content=ft.Container(
            padding=15,
            content=ft.Column(
                [
                    ft.Text("Resumo do Período", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.ARROW_UPWARD, color="green"),
                            ft.Text("Receitas:", weight=ft.FontWeight.BOLD),
                            txt_total_receitas,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.ARROW_DOWNWARD, color="red"),
                            ft.Text("Despesas:", weight=ft.FontWeight.BOLD),
                            txt_total_despesas,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Divider(),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET),
                            ft.Text("Saldo:", size=20, weight=ft.FontWeight.BOLD),
                            txt_saldo_final,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                ]
            ),
        ),
    )
    
    msg_atualizacao = page.client_storage.get("ultima_atualizacao") or "Nenhuma atualização registrada."
    txt_ultima_atualizacao = ft.Text(msg_atualizacao, size=12, italic=True, color="grey")
    
    seletor_data = ft.DatePicker(on_change=data_selecionada, first_date=datetime(2020, 1, 1), last_date=datetime.now() + timedelta(days=365))
    page.overlay.append(seletor_data)
    
    card_title = ft.Text("Nova Transação", size=18, weight=ft.FontWeight.BOLD)
    txt_descricao = ft.TextField(label="Descrição")
    txt_valor = ft.TextField(label="Valor (R$)", keyboard_type=ft.KeyboardType.NUMBER)
    txt_data_selecionada = ft.Text("Selecione uma data...", color="grey")
    btn_abrir_calendario = ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, on_click=abrir_seletor_data, data="principal")
    dd_categoria = ft.Dropdown(label="Categoria", options=[ft.dropdown.Option(c) for c in ["Alimentação", "Transporte", "Lazer", "Moradia", "Salário", "Vendas", "Bônus", "Outros"]])
    
    btn_add_receita = ft.ElevatedButton("Adicionar Receita", on_click=adicionar_transacao, data="Receita", icon=ft.Icons.ADD, bgcolor="green", color="white")
    btn_add_despesa = ft.ElevatedButton("Adicionar Despesa", on_click=adicionar_transacao, data="Despesa", icon=ft.Icons.REMOVE, bgcolor="red", color="white")
    linha_botoes_adicionar = ft.Row([btn_add_despesa, btn_add_receita], spacing=10)
    
    btn_salvar = ft.ElevatedButton("Salvar", on_click=salvar_edicao, icon=ft.Icons.SAVE, bgcolor="blue", color="white")
    btn_cancelar_edicao = ft.ElevatedButton("Cancelar", on_click=cancelar_edicao, icon=ft.Icons.CANCEL, bgcolor="grey", color="white")
    linha_botoes_edicao = ft.Row([btn_salvar, btn_cancelar_edicao], spacing=10, visible=False)
    
    radio_group_tipo_edicao = ft.RadioGroup(content=ft.Row([ft.Radio(value="Despesa", label="Despesa"), ft.Radio(value="Receita", label="Receita")]), value="Despesa", visible=False)

    card_nova_transacao = ft.Card(elevation=10, content=ft.Container(padding=15, content=ft.Column(
        controls=[
            card_title,
            radio_group_tipo_edicao, txt_descricao, txt_valor,
            ft.Row([txt_data_selecionada, btn_abrir_calendario]),
            dd_categoria, linha_botoes_adicionar, linha_botoes_edicao,
        ])))
    
    # --- Componentes dos Filtros (para o BottomSheet) ---
    filtro_tipo = ft.RadioGroup(content=ft.Row([ft.Radio(value="Todos", label="Todos"), ft.Radio(value="Receita", label="Receita"), ft.Radio(value="Despesa", label="Despesa")]), value="Todos")
    filtro_descricao = ft.TextField(label="Buscar por descrição...", prefix_icon=ft.Icons.SEARCH)
    txt_data_de = ft.Text("De:", color="grey")
    btn_data_de = ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, on_click=abrir_seletor_data, data="filtro_de")
    txt_data_ate = ft.Text("Até:", color="grey")
    btn_data_ate = ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, on_click=abrir_seletor_data, data="filtro_ate")

    # --- Painel Deslizante (BottomSheet) ---
    bs = ft.BottomSheet(
        ft.Container(
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Text("Filtros", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("Tipo", weight=ft.FontWeight.BOLD),
                    filtro_tipo,
                    ft.Divider(height=10),
                    filtro_descricao,
                    ft.Divider(height=10),
                    ft.Text("Período", weight=ft.FontWeight.BOLD),
                    ft.Row([txt_data_de, btn_data_de]),
                    ft.Row([txt_data_ate, btn_data_ate]),
                    ft.Divider(height=20),
                    ft.ElevatedButton("Aplicar Filtros", on_click=aplicar_filtros_e_atualizar, icon=ft.Icons.CHECK)
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO
            )
        )
    )
    page.overlay.append(bs)

    def abrir_painel_filtros(e):
        page.open(bs)

    # --- Componentes Gráficos e de Histórico ---
    grafico_pizza = ft.PieChart(sections=[], center_space_radius=40)
    card_grafico = ft.Card(elevation=10, visible=False, content=ft.Container(padding=15, content=ft.Column(
        [ft.Text("Gastos por Categoria", size=18, weight=ft.FontWeight.BOLD), grafico_pizza],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER)))
    historico_container = ft.Column(spacing=10)

    # --- Layout Principal da Página ---
    page.appbar = ft.AppBar(
        title=ft.Text("App Financeiro"),
        actions=[ft.IconButton(ft.Icons.FILTER_LIST, on_click=abrir_painel_filtros, tooltip="Filtros")]
    )
    
    page.add(
        ft.Container(
            padding=ft.padding.symmetric(horizontal=20),
            expand=True,
            content=ft.Column(
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    card_resumo, 
                    txt_ultima_atualizacao, 
                    ft.Divider(),
                    card_nova_transacao, 
                    ft.Divider(),
                    card_grafico, 
                    ft.Text("Histórico", size=18, weight=ft.FontWeight.BOLD),
                    historico_container,
                ],
            )
        )
    )
    
    carregar_dados_iniciais()

if __name__ == "__main__":
    ft.app(target=main)
