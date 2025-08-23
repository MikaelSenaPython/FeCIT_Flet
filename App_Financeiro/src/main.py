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

# 🔑 senha única do app
APP_PASSWORD = "162408"


# --- TELA DE LOGIN ---
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
            on_success()  # ✅ chama a interface principal
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


def main(page: ft.Page):
    def iniciar_app():
        page.clean()
        carregar_interface_principal(page)

    # começa mostrando a tela de login
    login_screen(page, on_success=iniciar_app)


def carregar_interface_principal(page: ft.Page):
    page.clean()
    page.title = "Meu App Financeiro"
    page.window_width = 450
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK

    # --- Banco de dados ---
    db.criar_tabelas(page)

    def testar_conexao_categorias(e):
        print("--- INICIANDO TESTE DE CATEGORIAS ---")
        try:
            categorias_no_db = db.buscar_categorias_db(page)
            if not categorias_no_db:
                print("RESULTADO: O banco de dados NÃO retornou nenhuma categoria. A lista está vazia.")
            else:
                print(f"RESULTADO: Sucesso! Encontradas {len(categorias_no_db)} categorias.")
                for cat in categorias_no_db:
                    # Convertendo para um dicionário para imprimir de forma legível
                    print(f"  - {dict(cat)}")
        except Exception as ex:
            print(f"ERRO NO TESTE: Ocorreu uma exceção ao buscar categorias: {ex}")
        print("--- FIM DO TESTE ---")

    # --- Funções de Backup / Restauração ---

    def atualizar_timestamp_permanente():
        """Atualiza o texto da UI e salva a data no banco de dados."""
        now_str = f"Última alteração: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}"
        txt_ultima_atualizacao.value = now_str
        db.set_config_value_db(page, 'ultima_alteracao', now_str)
        page.update() # Garante que a mudança seja visível imediatamente

    def criar_imagem_grafico(dados_categoria, titulo, caminho_arquivo):
        """Cria e salva um gráfico de pizza como uma imagem PNG."""
        if not dados_categoria:
            return False # Não cria gráfico se não houver dados

        labels = dados_categoria.keys()
        sizes = dados_categoria.values()
        
        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Garante que a pizza seja um círculo.
        plt.title(titulo)
        
        plt.savefig(caminho_arquivo, transparent=True)
        plt.close(fig) # Fecha a figura para liberar memória
        return True

    def gerar_relatorio_pdf(caminho_destino):
        """
        Gera um relatório PDF completo com base nos filtros definidos na tela de Relatórios.
        Inclui resumo, gráficos e uma lista detalhada de transações.
        """
        # 1. Validação de Entrada: Garante que um período foi selecionado
        if not data_inicio_relatorio.value or not data_fim_relatorio.value:
            page.snack_bar = ft.SnackBar(ft.Text("Por favor, selecione um período de datas."), bgcolor="orange")
            page.snack_bar.open = True
            page.update()
            return

        try:
            data_inicio = datetime.strptime(data_inicio_relatorio.value, "%d/%m/%Y")
            data_fim = datetime.strptime(data_fim_relatorio.value, "%d/%m/%Y")
            
            # 2. Filtragem dos Dados
            # Filtro primário por DATA
            transacoes_filtradas = [
                t for t in todas_transacoes
                if data_inicio <= datetime.strptime(t['data'], "%d/%m/%Y") <= data_fim
            ]

            # Filtro secundário por TIPO (Receita/Despesa)
            tipo_filtro = filtro_tipo_relatorio.value
            if tipo_filtro != "Todas":
                transacoes_filtradas = [t for t in transacoes_filtradas if t['tipo'] == tipo_filtro]

            # Filtro terciário por CATEGORIA
            cat_filtro = filtro_categoria_relatorio.value
            if cat_filtro != "Todas":
                transacoes_filtradas = [t for t in transacoes_filtradas if t['categoria'] == cat_filtro]
            
            # 3. Cálculos e Agregação de Dados para Gráficos
            receitas_total = sum(float(t['valor']) for t in transacoes_filtradas if t['tipo'] == "Receita")
            despesas_total = sum(float(t['valor']) for t in transacoes_filtradas if t['tipo'] == "Despesa")
            saldo = receitas_total - despesas_total
            
            dados_despesas_cat = {c: sum(float(t['valor']) for t in transacoes_filtradas if t['tipo'] == 'Despesa' and t['categoria'] == c) for c in set(t['categoria'] for t in transacoes_filtradas if t['tipo'] == 'Despesa')}
            dados_receitas_cat = {c: sum(float(t['valor']) for t in transacoes_filtradas if t['tipo'] == 'Receita' and t['categoria'] == c) for c in set(t['categoria'] for t in transacoes_filtradas if t['tipo'] == 'Receita')}

            # 4. Geração das Imagens dos Gráficos
            grafico_despesas_path = "grafico_despesas.png"
            grafico_receitas_path = "grafico_receitas.png"
            
            tem_grafico_despesas = criar_imagem_grafico(dados_despesas_cat, "Composição de Despesas", grafico_despesas_path)
            tem_grafico_receitas = criar_imagem_grafico(dados_receitas_cat, "Composição de Receitas", grafico_receitas_path)
            
            # 5. Construção do Documento PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)

            pdf.cell(0, 10, "Relatório Financeiro", 0, 1, "C")
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 10, f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}", 0, 1, "C")
            pdf.ln(10)

            pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "Resumo do Período", 0, 1, "L")
            pdf.set_font("Arial", "", 11)
            pdf.cell(0, 7, f"Total de Receitas: R$ {receitas_total:,.2f}", 0, 1, "L")
            pdf.cell(0, 7, f"Total de Despesas: R$ {despesas_total:,.2f}", 0, 1, "L")
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 7, f"Saldo Final: R$ {saldo:,.2f}", 0, 1, "L"); pdf.ln(10)

            if tem_grafico_despesas:
                pdf.image(grafico_despesas_path, x=10, y=None, w=180)
                pdf.ln(5)
            if tem_grafico_receitas:
                pdf.image(grafico_receitas_path, x=10, y=None, w=180)
                pdf.ln(5)
            
            if transacoes_filtradas:
                pdf.add_page()
                pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "Detalhes das Transações", 0, 1, "L")
                pdf.set_font("Arial", "B", 10)
                pdf.cell(25, 8, "Data", 1); pdf.cell(85, 8, "Descrição", 1); pdf.cell(35, 8, "Categoria", 1); pdf.cell(40, 8, "Valor (R$)", 1); pdf.ln()
                pdf.set_font("Arial", "", 10)
                for t in transacoes_filtradas:
                    descricao = t['descricao'].encode('latin-1', 'replace').decode('latin-1')
                    categoria = t['categoria'].encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_text_color(0, 128, 0) if t['tipo'] == 'Receita' else pdf.set_text_color(255, 0, 0)
                    valor_str = f"+{float(t['valor']):,.2f}" if t['tipo'] == 'Receita' else f"-{float(t['valor']):,.2f}"
                    pdf.cell(25, 8, t['data'], 1); pdf.cell(85, 8, descricao, 1); pdf.cell(35, 8, categoria, 1); pdf.cell(40, 8, valor_str, 1); pdf.ln()
                pdf.set_text_color(0, 0, 0)

            # 6. Salvar o arquivo PDF
            pdf.output(caminho_destino)
            page.snack_bar = ft.SnackBar(ft.Text("Relatório PDF salvo com sucesso!"), bgcolor="green"); page.snack_bar.open = True
        
        except Exception as ex:
            print(f"ERRO AO GERAR PDF: {ex}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao gerar PDF: {ex}"), bgcolor="red"); page.snack_bar.open = True
        
        finally:
            # 7. Limpar arquivos de imagem temporários, mesmo que ocorra um erro
            if os.path.exists("grafico_despesas.png"): os.remove("grafico_despesas.png")
            if os.path.exists("grafico_receitas.png"): os.remove("grafico_receitas.png")

        page.update()
    
    def salvar_pdf_result(e: ft.FilePickerResultEvent):
        if e.path:
            gerar_relatorio_pdf(e.path)

    # ATUALIZE as instâncias do FilePicker para usar as novas funções
    file_picker_salvar_pdf = ft.FilePicker(on_result=salvar_pdf_result)
    page.overlay.extend([file_picker_salvar_pdf])

    # --- Variáveis de Estado ---
    todas_transacoes = []
    todas_metas = []
    mes_selecionado = datetime.now()
    id_em_edicao = ft.Text(value=None, visible=False)
    lista_categorias_view = ft.ListView(expand=True, spacing=10)

    data_inicio_relatorio = ft.Text(value=None)
    data_fim_relatorio = ft.Text(value=None)
    selecionando_data_para = "" # Ajuda a saber se estamos escolhendo a data de início ou fim

    # =====================================================================
    # ======================= FUNÇÕES DE METAS ============================
    # =====================================================================

    def atualizar_cofre_inicio():
        total = sum(float(m["valor_atual"]) for m in todas_metas)
        txt_cofre_total.value = f"R$ {total:,.2f}"
        page.update()

    def atualizar_carteira():
        # Limpa cards antigos, preservando o título "Carteira"
        if len(carteira_view.controls) > 1:
            del carteira_view.controls[1:]

        if not todas_metas:
            carteira_view.controls.append(
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Nenhuma meta criada ainda.", size=16),
                        ft.Text(
                            "Toque no botão + para criar sua primeira meta.",
                            size=12,
                            color="grey",
                        ),
                    ],
                )
            )
        else:
            for meta in todas_metas:
                objetivo = float(meta["valor_objetivo"])
                atual = float(meta["valor_atual"])
                progresso = (atual / objetivo) if objetivo > 0 else 0.0
                progresso = max(0.0, min(1.0, progresso))

                carteira_view.controls.append(
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
                                            ft.Text(
                                                meta["nome"],
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            ft.Text(
                                                f"{progresso*100:,.0f}%", size=14
                                            ),
                                        ],
                                    ),
                                    ft.Text(
                                        f"Guardado: R$ {atual:,.2f} / R$ {objetivo:,.2f}",
                                        size=13,
                                        color="grey",
                                    ),
                                    ft.ProgressBar(value=progresso, width=320),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.ElevatedButton(
                                                "Depositar",
                                                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                                on_click=lambda e, m=meta: abrir_dialogo_deposito(
                                                    m
                                                ),
                                            ),
                                            ft.OutlinedButton(
                                                "Retirar",
                                                icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                                                on_click=lambda e, m=meta: abrir_dialogo_retirada(
                                                    m
                                                ),
                                            ),
                                            ft.IconButton(
                                                icon=ft.Icons.DELETE_OUTLINE,
                                                icon_color="red",
                                                tooltip="Excluir meta",
                                                on_click=lambda e, m=meta: abrir_dialogo_excluir_meta(
                                                    m
                                                ),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                    )
                )
        page.update()

    def carregar_metas():
        nonlocal todas_metas
        todas_metas = db.buscar_metas_db(page)
        atualizar_carteira()
        atualizar_cofre_inicio()

    def abrir_dialogo_nova_meta(e):
        nome = ft.TextField(label="Nome da Meta")
        valor_objetivo = ft.TextField(
            label="Valor Objetivo (R$)", keyboard_type=ft.KeyboardType.NUMBER
        )

        def salvar_meta(ev):
            if not nome.value or not valor_objetivo.value:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Preencha todos os campos!"), bgcolor="orange"
                )
                page.snack_bar.open = True
                page.update()
                return
            try:
                alvo = float(valor_objetivo.value)
                if alvo <= 0:
                    raise ValueError
                db.adicionar_meta_db(page, nome.value, alvo)
                page.close(dialogo)
                carregar_metas()
            except ValueError:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Valor objetivo inválido."), bgcolor="red"
                )
                page.snack_bar.open = True
                page.update()
            except Exception:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Erro ao salvar meta."), bgcolor="red"
                )
                page.snack_bar.open = True
                page.update()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nova Meta"),
            content=ft.Column([nome, valor_objetivo], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: page.close(dialogo)),
                ft.TextButton("Salvar", on_click=salvar_meta),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dialogo)

    def abrir_dialogo_deposito(meta):
        valor = ft.TextField(
            label="Valor a depositar (R$)", keyboard_type=ft.KeyboardType.NUMBER
        )

        def confirmar(ev):
            try:
                v = float(valor.value)
                if v <= 0:
                    raise ValueError
                novo = float(meta["valor_atual"]) + v
                objetivo = float(meta["valor_objetivo"])
                if objetivo > 0:
                    novo = min(novo, objetivo)
                db.atualizar_valor_meta_db(page, meta["id"], novo)
                page.close(dialogo)
                carregar_metas()
            except ValueError:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Informe um valor válido."), bgcolor="red"
                )
                page.snack_bar.open = True
                page.update()
            except Exception:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Erro ao depositar."), bgcolor="red"
                )
                page.snack_bar.open = True
                page.update()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Depositar em {meta['nome']}"),
            content=valor,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: page.close(dialogo)),
                ft.TextButton("Confirmar", on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dialogo)

    def abrir_dialogo_retirada(meta):
        valor = ft.TextField(
            label="Valor a retirar (R$)", keyboard_type=ft.KeyboardType.NUMBER
        )

        def confirmar(ev):
            try:
                v = float(valor.value)
                if v <= 0:
                    raise ValueError
                novo = max(0.0, float(meta["valor_atual"]) - v)
                db.atualizar_valor_meta_db(page, meta["id"], novo)
                page.close(dialogo)
                carregar_metas()
            except ValueError:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Informe um valor válido."), bgcolor="red"
                )
                page.snack_bar.open = True
                page.update()
            except Exception:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Erro ao retirar."), bgcolor="red"
                )
                page.snack_bar.open = True
                page.update()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Retirar de {meta['nome']}"),
            content=valor,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: page.close(dialogo)),
                ft.TextButton("Confirmar", on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dialogo)

    def abrir_dialogo_excluir_meta(meta):
        def confirmar(ev):
            try:
                db.deletar_meta_db(page, meta["id"])
            finally:
                page.close(dialogo)
                carregar_metas()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Excluir Meta"),
            content=ft.Text(
                f"Tem certeza que deseja excluir a meta '{meta['nome']}'?"
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: page.close(dialogo)),
                ft.TextButton("Excluir", on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dialogo)

    def ir_para_carteira():
        page.navigation_bar.selected_index = 2
        navigate(None)

    def data_relatorio_selecionada(e):
        """Chamada quando uma data é escolhida no DatePicker do relatório."""
        global selecionando_data_para
        data_formatada = e.control.value.strftime('%d/%m/%Y')
        
        if selecionando_data_para == "inicio":
            data_inicio_relatorio.value = data_formatada
        elif selecionando_data_para == "fim":
            data_fim_relatorio.value = data_formatada
        
        page.close(seletor_data_relatorio)
        page.update()

    def abrir_datepicker_relatorio(e):
        """Abre o DatePicker e armazena se é para a data de início ou fim."""
        global selecionando_data_para
        selecionando_data_para = e.control.data
        page.open(seletor_data_relatorio)

    def definir_periodo_relatorio(e):
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
        
        data_inicio_relatorio.value = data_inicio.strftime('%d/%m/%Y')
        data_fim_relatorio.value = data_fim.strftime('%d/%m/%Y')
        page.update()

    # =====================================================================
    # ===================== FUNÇÕES DE CATEGORIAS (CRUD) ==================
    # =====================================================================

    def carregar_e_exibir_categorias():
        lista_categorias_view.controls.clear()
        categorias_db = db.buscar_categorias_db(page)
        if not categorias_db:
            lista_categorias_view.controls.append(ft.Text("Nenhuma categoria cadastrada."))
        else:
            for categoria in categorias_db:
                lista_categorias_view.controls.append(
                    ft.ListTile(
                        title=ft.Text(categoria['nome']),
                        subtitle=ft.Text(categoria['tipo'], color="green" if categoria['tipo'] == 'Receita' else 'orange'),
                        trailing=ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color="red",
                            data=categoria['id'],
                            on_click=confirmar_delecao_categoria,
                        )
                    )
                )
        page.update()

    def adicionar_nova_categoria(e):
        # Esta função agora abre um diálogo, em vez de ler campos globais
        nome_field = ft.TextField(label="Nome da Categoria")
        tipo_dropdown = ft.Dropdown(
            label="Tipo",
            options=[
                ft.dropdown.Option("Receita"),
                ft.dropdown.Option("Despesa"),
            ]
        )

        def salvar_click(ev):
            nome = nome_field.value
            tipo = tipo_dropdown.value
            if not nome or not tipo:
                page.snack_bar = ft.SnackBar(ft.Text("Nome e tipo são obrigatórios!"), bgcolor="orange")
                page.snack_bar.open = True
                page.update()
                return
            try:
                db.adicionar_categoria_db(page, nome, tipo)
                page.close(dialogo)
                carregar_e_exibir_categorias()
                page.snack_bar = ft.SnackBar(ft.Text(f"Categoria '{nome}' adicionada!"), bgcolor="green")
                page.snack_bar.open = True
                page.update()
            except Exception:
                page.snack_bar = ft.SnackBar(ft.Text("Erro: Categoria já existe."), bgcolor="red")
                page.snack_bar.open = True
                page.update()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nova Categoria"),
            content=ft.Column([nome_field, tipo_dropdown], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.close(dialogo)),
                ft.TextButton("Salvar", on_click=salvar_click),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dialogo)

    def confirmar_delecao_categoria(e):
        categoria_id = e.control.data
        def deletar_click(ev):
            db.deletar_categoria_db(page, categoria_id)
            page.close(dlg_confirm)
            carregar_e_exibir_categorias()

        dlg_confirm = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text("Tem certeza? Isto não afetará transações já existentes."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.close(dlg_confirm)),
                ft.TextButton("Excluir", on_click=deletar_click)
            ]
        )
        page.open(dlg_confirm)

    # =====================================================================
    # ==================== FUNÇÕES PRINCIPAIS / DASHBOARD =================
    # =====================================================================

    


    def atualizar_views(e=None):
        """
        Carrega as transações do banco (com busca opcional),
        filtra por mês selecionado e atualiza UI.
        """
        termo = campo_busca.value.strip() if campo_busca.value else None
        transacoes = db.buscar_transacoes_db(page, termo_busca=termo)

        transacoes_do_mes = [
            t
            for t in transacoes
            if datetime.strptime(t["data"], "%d/%m/%Y").month
            == mes_selecionado.month
            and datetime.strptime(t["data"], "%d/%m/%Y").year
            == mes_selecionado.year
        ]

        atualizar_resumo_inicio(transacoes_do_mes)


        txt_mes_ano.value = (
            f"{month_name[mes_selecionado.month].capitalize()} {mes_selecionado.year}"
        )
        atualizar_dashboard_view(transacoes_do_mes)
        page.update()

    def carregar_dados_iniciais():
        nonlocal todas_transacoes
        todas_transacoes = db.buscar_transacoes_db(page)
        atualizar_views()

    def mudar_mes(e):
        nonlocal mes_selecionado
        if e.control.data == "prev":
            mes_selecionado = mes_selecionado.replace(day=1) - timedelta(days=1)
        elif e.control.data == "next":
            proximo_mes = mes_selecionado.replace(day=1) + timedelta(days=32)
            mes_selecionado = proximo_mes.replace(day=1)

        filtro_dashboard.selected_index = 0
        filtro_subcategoria_dashboard.value = "Todas"
        atualizar_views()

    # --- Funções de Atualização de UI ---
    def atualizar_resumo_inicio(transacoes):
        total_receitas = sum(
            float(t["valor"]) for t in transacoes if t["tipo"] == "Receita"
        )
        total_despesas = sum(
            float(t["valor"]) for t in transacoes if t["tipo"] == "Despesa"
        )
        saldo = total_receitas - total_despesas

        txt_total_receitas.value = f"R$ {total_receitas:,.2f}"
        txt_total_despesas.value = f"R$ {total_despesas:,.2f}"

        cor_saldo = "green" if saldo >= 0 else "red"
        txt_saldo_final.value = f"R$ {saldo:,.2f}"
        txt_saldo_final.color = cor_saldo

    def atualizar_dashboard_view(transacoes):
        filtro_selecionado = filtro_dashboard.selected_index
        filtro_subcategoria_dashboard.visible = False

        if filtro_selecionado == 0:  # Visão Geral
            transacoes_para_exibir = transacoes
            gerar_grafico_geral(transacoes)
            card_resumo_dashboard_geral.visible = True
            card_resumo_dashboard_filtrado.visible = False
        else:  # Receitas ou Despesas
            tipo_filtro = "Receita" if filtro_selecionado == 1 else "Despesa"

            categorias_do_tipo = sorted(
                list(
                    set(
                        [
                            t["categoria"]
                            for t in transacoes
                            if t["tipo"] == tipo_filtro
                        ]
                    )
                )
            )
            if categorias_do_tipo:
                filtro_subcategoria_dashboard.visible = True
                opcoes_filtro = [ft.dropdown.Option("Todas")] + [
                    ft.dropdown.Option(c) for c in categorias_do_tipo
                ]
                filtro_subcategoria_dashboard.options = opcoes_filtro
                if filtro_subcategoria_dashboard.value not in [
                    opt.key for opt in opcoes_filtro
                ]:
                    filtro_subcategoria_dashboard.value = "Todas"

            transacoes_do_tipo = [
                t for t in transacoes if t["tipo"] == tipo_filtro
            ]
            subcategoria_selecionada = filtro_subcategoria_dashboard.value

            if subcategoria_selecionada == "Todas":
                transacoes_para_exibir = transacoes_do_tipo
            else:
                transacoes_para_exibir = [
                    t
                    for t in transacoes_do_tipo
                    if t["categoria"] == subcategoria_selecionada
                ]

            gerar_grafico_por_tipo(transacoes_do_tipo, tipo_filtro)
            card_resumo_dashboard_geral.visible = False
            card_resumo_dashboard_filtrado.visible = True

            total_filtrado = sum(float(t["valor"]) for t in transacoes_para_exibir)

            if subcategoria_selecionada == "Todas":
                txt_resumo_filtrado_titulo.value = f"Total de {tipo_filtro}s"
            else:
                txt_resumo_filtrado_titulo.value = (
                    f"Total em '{subcategoria_selecionada}'"
                )

            txt_resumo_filtrado_valor.value = f"R$ {total_filtrado:,.2f}"
            txt_resumo_filtrado_valor.color = (
                "green" if tipo_filtro == "Receita" else "red"
            )

        atualizar_historico(transacoes_para_exibir)

        total_gasto = sum(
            float(t["valor"]) for t in transacoes if t["tipo"] == "Despesa"
        )
        total_ganho = sum(
            float(t["valor"]) for t in transacoes if t["tipo"] == "Receita"
        )
        lucro = total_ganho - total_gasto

        txt_total_gasto_mes.value = f"R$ {total_gasto:,.2f}"
        txt_total_ganho_mes.value = f"R$ {total_ganho:,.2f}"
        txt_lucro_mes.value = f"R$ {lucro:,.2f}"
        txt_lucro_mes.color = "green" if lucro >= 0 else "red"

        dashboard_view.controls.clear()
        dashboard_view.controls.extend(
            [
                mes_selector,
                campo_busca,  # 🔎 busca
                filtro_dashboard,
                filtro_subcategoria_dashboard,
                card_grafico,
                ver_transacoes_btn,
                historico_container,
                card_resumo_dashboard_geral,
                card_resumo_dashboard_filtrado,
            ]
        )

    def gerar_grafico_geral(transacoes):
        card_grafico_titulo.value = "Receitas x Despesas"
        grafico_legenda.controls.clear()
        total_receitas = sum(
            float(t["valor"]) for t in transacoes if t["tipo"] == "Receita"
        )
        total_despesas = sum(
            float(t["valor"]) for t in transacoes if t["tipo"] == "Despesa"
        )

        soma_total = total_receitas + total_despesas
        if soma_total == 0:
            card_grafico.visible = False
            return

        card_grafico.visible = True

        porc_receitas = (total_receitas / soma_total * 100) if soma_total > 0 else 0
        porc_despesas = (total_despesas / soma_total * 100) if soma_total > 0 else 0

        grafico_pizza.sections = [
            ft.PieChartSection(
                value=total_receitas, title=f"{porc_receitas:.0f}%", color="green", radius=80
            ),
            ft.PieChartSection(
                value=total_despesas, title=f"{porc_despesas:.0f}%", color="red", radius=80
            ),
        ]

        if total_receitas > 0:
            grafico_legenda.controls.append(
                ft.Row(
                    [
                        ft.Container(width=15, height=15, bgcolor="green", border_radius=10),
                        ft.Text(f"Receitas ({porc_receitas:.1f}%)"),
                    ]
                )
            )
        if total_despesas > 0:
            grafico_legenda.controls.append(
                ft.Row(
                    [
                        ft.Container(width=15, height=15, bgcolor="red", border_radius=10),
                        ft.Text(f"Despesas ({porc_despesas:.1f}%)"),
                    ]
                )
            )

    def gerar_grafico_por_tipo(transacoes, tipo):
        card_grafico_titulo.value = f"Composição de {tipo}s"
        grafico_legenda.controls.clear()

        if not transacoes:
            card_grafico.visible = False
            return

        card_grafico.visible = True

        total_tipo = sum(float(t["valor"]) for t in transacoes)

        dados_por_categoria = {}
        for t in transacoes:
            dados_por_categoria[t["categoria"]] = dados_por_categoria.get(
                t["categoria"], 0
            ) + float(t["valor"])

        if tipo == "Receita":
            cores = itertools.cycle(
                ["green", "orange", "#36A2EB", "#4BC0C0", "#9966FF"]
            )
        else:  # Despesa
            cores = itertools.cycle(
                ["red", "orange", "#FFCE56", "#FF9F40", "#FF6384"]
            )

        chart_sections = []
        for categoria, valor in dados_por_categoria.items():
            cor_atual = next(cores)
            porcentagem = (valor / total_tipo * 100) if total_tipo > 0 else 0

            chart_sections.append(
                ft.PieChartSection(
                    value=valor,
                    title=f"{porcentagem:.0f}%",
                    title_style=ft.TextStyle(
                        size=12, color="white", weight=ft.FontWeight.BOLD
                    ),
                    color=cor_atual,
                    radius=80,
                )
            )

            grafico_legenda.controls.append(
                ft.Row(
                    [
                        ft.Container(
                            width=15, height=15, bgcolor=cor_atual, border_radius=7
                        ),
                        ft.Text(f"{categoria} ({porcentagem:.1f}%)"),
                    ]
                )
            )

        grafico_pizza.sections = chart_sections

    def atualizar_historico(transacoes):
        historico_container.controls.clear()
        if not transacoes:
            historico_container.controls.append(
                ft.Text(
                    "Nenhuma transação encontrada para este filtro.",
                    text_align=ft.TextAlign.CENTER,
                )
            )
        for t in transacoes:
            historico_container.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(
                                    f"{t['descricao']} ({t['categoria']})",
                                    weight=ft.FontWeight.BOLD,
                                ),
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
                                    color="green"
                                    if t["tipo"] == "Receita"
                                    else "red",
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_color="blue",
                                    on_click=lambda e, transacao=t: iniciar_edicao(
                                        transacao
                                    ),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color="red",
                                    on_click=lambda e, transacao=t: abrir_dialogo_confirmacao(
                                        transacao
                                    ),
                                ),
                            ],
                        ),
                    ],
                )
            )

    # =====================================================================
    # =============== FUNÇÕES DE TRANSAÇÃO (ADD/EDIT/DELETE) ==============
    # =====================================================================

    def adicionar_transacao(e):
        tipo = e.control.data  # "Receita" ou "Despesa"
        if not all(
            [
                txt_descricao.value,
                txt_valor.value,
                dd_categoria.value,
                txt_data_selecionada.value != "Selecione uma data...",
            ]
        ):
            page.snack_bar = ft.SnackBar(
                ft.Text("Preencha todos os campos!"), bgcolor="orange"
            )
            page.snack_bar.open = True
            page.update()
            return
        try:
            valor = float(txt_valor.value)
        except ValueError:
            page.snack_bar = ft.SnackBar(
                ft.Text("O valor deve ser um número!"), bgcolor="red"
            )
            page.snack_bar.open = True
            page.update()
            return

        # (Opcional) Validar se a categoria pertence ao tipo escolhido
        categorias_do_tipo = [cat['nome'] for cat in db.buscar_categorias_db(page, tipo=tipo)]
        if categorias_do_tipo and dd_categoria.value not in categorias_do_tipo:
            page.snack_bar = ft.SnackBar(
                ft.Text(
                    f"A categoria '{dd_categoria.value}' não pertence a {tipo}. Selecione outra ou crie em Ajustes."
                ),
                bgcolor="orange",
            )
            page.snack_bar.open = True
            page.update()
            return

        db.adicionar_transacao_db(
            page,
            tipo,
            txt_descricao.value,
            valor,
            dd_categoria.value,
            txt_data_selecionada.value,
        )

        txt_descricao.value, txt_valor.value, dd_categoria.value = "", "", None
        txt_data_selecionada.value = "Selecione uma data..."
        atualizar_timestamp_permanente()
        carregar_dados_iniciais()

    def cancelar_edicao(e):
        card_title.value = "Nova Transação"
        id_em_edicao.value = None
        linha_botoes_adicionar.visible = True
        linha_botoes_edicao.visible = False
        radio_group_tipo_edicao.visible = False

        txt_descricao.value, txt_valor.value, dd_categoria.value = "", "", None
        txt_data_selecionada.value = "Selecione uma data..."
        page.update()

    def iniciar_edicao(transacao):
        card_title.value = "Editar Transação"
        id_em_edicao.value = transacao["id"]
        linha_botoes_adicionar.visible = False
        linha_botoes_edicao.visible = True
        radio_group_tipo_edicao.visible = True

        radio_group_tipo_edicao.value = transacao["tipo"]
        txt_descricao.value = transacao["descricao"]
        txt_valor.value = str(transacao["valor"])
        dd_categoria.value = transacao["categoria"]
        txt_data_selecionada.value = transacao["data"]
        page.update()

    def salvar_edicao(e):
        if not all([txt_descricao.value, txt_valor.value, dd_categoria.value]):
            page.snack_bar = ft.SnackBar(
                ft.Text("Preencha todos os campos!"), bgcolor="red"
            )
            page.snack_bar.open = True
            page.update()
            return
        try:
            valor = float(txt_valor.value)
        except ValueError:
            page.snack_bar = ft.SnackBar(
                ft.Text("O valor deve ser um número!"), bgcolor="red"
            )
            page.snack_bar.open = True
            page.update()
            return

        # (Opcional) Validar se a categoria pertence ao tipo escolhido na edição
        tipo = radio_group_tipo_edicao.value
        categorias_do_tipo = [cat['nome'] for cat in db.buscar_categorias_db(page, tipo=tipo)]
        if categorias_do_tipo and dd_categoria.value not in categorias_do_tipo:
            page.snack_bar = ft.SnackBar(
                ft.Text(
                    f"A categoria '{dd_categoria.value}' não pertence a {tipo}. Selecione outra ou ajuste em Ajustes."
                ),
                bgcolor="orange",
            )
            page.snack_bar.open = True
            page.update()
            return

        db.update_transacao_db(
            page,
            id=int(id_em_edicao.value),
            tipo=tipo,
            descricao=txt_descricao.value,
            valor=valor,
            categoria=dd_categoria.value,
            data=txt_data_selecionada.value,
        )
        cancelar_edicao(None)
        carregar_dados_iniciais()

    def deletar_transacao(transacao_a_deletar):
        db.deletar_transacao_db(page, transacao_a_deletar["id"])
        carregar_dados_iniciais()

    def fechar_dialogo(e):
        page.close(dialogo_confirmacao)

    def confirmar_exclusao(e):
        deletar_transacao(dialogo_confirmacao.data)
        page.close(dialogo_confirmacao)

    def abrir_dialogo_confirmacao(transacao):
        dialogo_confirmacao.data = transacao
        page.open(dialogo_confirmacao)

    def data_selecionada(e):
        txt_data_selecionada.value = e.control.value.strftime("%d/%m/%Y")
        page.close(seletor_data)
        page.update()

    def abrir_seletor_data(e):
        page.open(seletor_data)

    def toggle_historico_visibility(e):
        historico_container.visible = not historico_container.visible
        page.update()

    # main.py

    def atualizar_opcoes_categoria(e):
        """Força a atualização das opções do dropdown de categoria ao focar."""
        print("--- ATUALIZANDO OPÇÕES DO DROPDOWN ---")
        try:
            categorias_db = db.buscar_categorias_db(page)
            opcoes = [ft.dropdown.Option(cat['nome']) for cat in categorias_db]
            dd_categoria.options = opcoes
            print(f"Dropdown atualizado com {len(opcoes)} opções.")
            page.update()
        except Exception as ex:
            print(f"ERRO AO ATUALIZAR OPÇÕES: {ex}")



    # =====================================================================
    # ======================= COMPONENTES DE INTERFACE =====================
    # =====================================================================
    filtro_tipo_relatorio = ft.Dropdown(
        label="Filtrar por Tipo",
        options=[
            ft.dropdown.Option("Todas"),
            ft.dropdown.Option("Receita"),
            ft.dropdown.Option("Despesa"),
        ],
        value="Todas",
        expand=True,
    )

    filtro_categoria_relatorio = ft.Dropdown(
        label="Filtrar por Categoria",
        options=[ft.dropdown.Option("Todas")],
        value="Todas",
        expand=True,
        disabled=True # Começa desabilitado
    )
    def tipo_relatorio_changed(e):
        """Atualiza as opções de categoria na tela de relatórios."""
        tipo = filtro_tipo_relatorio.value
        if tipo == "Todas":
            # Se selecionar "Todas", busca todas as categorias
            categorias_db = db.buscar_categorias_db(page)
            filtro_categoria_relatorio.disabled = False
        else:
            # Busca apenas as categorias do tipo selecionado
            categorias_db = db.buscar_categorias_db(page, tipo=tipo)
            filtro_categoria_relatorio.disabled = False

        opcoes = [ft.dropdown.Option("Todas")] + [ft.dropdown.Option(cat['nome']) for cat in categorias_db]
        filtro_categoria_relatorio.options = opcoes
        filtro_categoria_relatorio.value = "Todas" # Reseta a seleção
        page.update()

    # Conecte a função ao componente
    filtro_tipo_relatorio.on_change = tipo_relatorio_changed

    # Dialogo confirmação de exclusão de transação
    dialogo_confirmacao = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirmar Exclusão"),
        content=ft.Text("Você tem certeza que deseja apagar este registro?"),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_dialogo),
            ft.TextButton("Confirmar", on_click=confirmar_exclusao),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # DatePicker
    seletor_data = ft.DatePicker(on_change=data_selecionada)

    seletor_data_relatorio = ft.DatePicker(on_change=data_relatorio_selecionada)
    page.overlay.extend([file_picker_salvar_pdf, seletor_data, seletor_data_relatorio]) # Adicione-o ao overlay

    # -- Card de Resumo (Início) --
    txt_total_receitas = ft.Text(size=16, weight=ft.FontWeight.BOLD, color="green")
    txt_total_despesas = ft.Text(size=16, weight=ft.FontWeight.BOLD, color="red")
    txt_saldo_final = ft.Text(size=20, weight=ft.FontWeight.BOLD)
    txt_ultima_atualizacao = ft.Text(size=11, color="grey", italic=True)
    card_resumo = ft.Card(
        elevation=5,
        content=ft.Container(
            padding=15,
            content=ft.Column(
                [
                    ft.Text("Resumo do Mês", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.ARROW_UPWARD, color="green"),
                            ft.Text("Receitas:"),
                            txt_total_receitas,
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.ARROW_DOWNWARD, color="red"),
                            ft.Text("Despesas:"),
                            txt_total_despesas,
                        ]
                    ),
                    ft.Divider(),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET),
                            ft.Text("Saldo:", size=18, weight=ft.FontWeight.BOLD),
                            txt_saldo_final,
                        ]
                    ),
                    txt_ultima_atualizacao,
                ]
            ),
        ),
    )

    # -- Card Cofre (Metas) --
    txt_cofre_total = ft.Text("R$ 0,00", size=24, weight=ft.FontWeight.BOLD)
    card_cofre = ft.Card(
        elevation=5,
        content=ft.Container(
            padding=15,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Cofre (Metas)", size=16, weight=ft.FontWeight.BOLD),
                            ft.Icon(ft.Icons.SAVINGS_OUTLINED),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    txt_cofre_total,
                    ft.Text("Valor atual somado das suas metas"),
                    ft.OutlinedButton(
                        "Gerenciar Metas", on_click=lambda e: ir_para_carteira()
                    ),
                ]
            ),
        ),
    )

    # -- Nova Transação --
    card_title = ft.Text("Nova Transação", size=16, weight=ft.FontWeight.BOLD)
    txt_descricao = ft.TextField(label="Descrição")
    txt_valor = ft.TextField(
        label="Valor (R$)", keyboard_type=ft.KeyboardType.NUMBER
    )
    txt_data_selecionada = ft.Text("Selecione uma data...")
    btn_abrir_calendario = ft.IconButton(
        icon=ft.Icons.CALENDAR_MONTH, on_click=abrir_seletor_data
    )

    # Dropdown de categorias dinâmico
    dd_categoria = ft.Dropdown(
        label="Categoria",
        options=[],  # todas as categorias
        expand=True

    )

    btn_add_receita = ft.ElevatedButton(
        "Adicionar Receita",
        on_click=adicionar_transacao,
        data="Receita",
        icon=ft.Icons.ADD,
        bgcolor="green",
        color="white",
    )
    btn_add_despesa = ft.ElevatedButton(
        "Adicionar Despesa",
        on_click=adicionar_transacao,
        data="Despesa",
        icon=ft.Icons.REMOVE,
        bgcolor="red",
        color="white",
    )
    linha_botoes_adicionar = ft.Row([btn_add_despesa, btn_add_receita], spacing=10)

    btn_salvar = ft.ElevatedButton(
        "Salvar", on_click=salvar_edicao, icon=ft.Icons.SAVE, bgcolor="blue", color="white"
    )
    btn_cancelar_edicao = ft.ElevatedButton(
        "Cancelar",
        on_click=cancelar_edicao,
        icon=ft.Icons.CANCEL,
        bgcolor="grey",
        color="white",
    )
    linha_botoes_edicao = ft.Row(
        [btn_salvar, btn_cancelar_edicao], spacing=10, visible=False
    )
    radio_group_tipo_edicao = ft.RadioGroup(
        content=ft.Row(
            [ft.Radio(value="Despesa", label="Despesa"), ft.Radio(value="Receita", label="Receita")]
        ),
        value="Despesa",
        visible=False,
    )

    card_nova_transacao = ft.Card(
        elevation=5,
        content=ft.Container(
            padding=15,
            content=ft.Column(
                [
                    card_title,
                    radio_group_tipo_edicao,
                    txt_descricao,
                    txt_valor,
                    ft.Row([txt_data_selecionada, btn_abrir_calendario]),
                    ft.Row(
                        controls=[
                            dd_categoria,
                            ft.IconButton(
                                icon=ft.Icons.SYNC,
                                tooltip="Atualizar Categorias",
                                on_click=atualizar_opcoes_categoria,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    linha_botoes_adicionar,
                    linha_botoes_edicao,
                ]
            ),
        ),
    )

    # -- Dashboard --
    txt_mes_ano = ft.Text(size=18, weight=ft.FontWeight.BOLD)
    mes_selector = ft.Row(
        [
            ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=mudar_mes, data="prev"),
            txt_mes_ano,
            ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=mudar_mes, data="next"),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # Campo de busca
    campo_busca = ft.TextField(
        label="Buscar transação (descrição)...",
        prefix_icon=ft.Icons.SEARCH,
        on_submit=lambda e: atualizar_views(),
    )

    filtro_dashboard = ft.Tabs(
        selected_index=0,
        on_change=atualizar_views,
        tabs=[ft.Tab("Visão Geral"), ft.Tab("Receitas"), ft.Tab("Despesas")],
    )

    filtro_subcategoria_dashboard = ft.Dropdown(
        label="Filtrar por Categoria",
        on_change=atualizar_views,
        value="Todas",
        visible=False,
    )

    grafico_pizza = ft.PieChart(sections=[], center_space_radius=40, expand=1)
    grafico_legenda = ft.Column(spacing=5)
    card_grafico_titulo = ft.Text("Visão Geral do Mês", size=16, weight=ft.FontWeight.BOLD)
    card_grafico = ft.Card(
        elevation=5,
        visible=False,
        content=ft.Container(
            padding=15,
            content=ft.Column(
                [
                    card_grafico_titulo,
                    ft.Row(
                        controls=[grafico_pizza, grafico_legenda],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ),
    )

    historico_container = ft.Column(spacing=10, visible=False)
    ver_transacoes_btn = ft.Container(
        content=ft.Row(
            [ft.Text("Ver transações"), ft.Icon(ft.Icons.CHEVRON_RIGHT)],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        on_click=toggle_historico_visibility,
        border_radius=5,
        ink=True,
    )

    txt_total_gasto_mes = ft.Text(size=16, color="red")
    txt_total_ganho_mes = ft.Text(size=16, color="green")
    txt_lucro_mes = ft.Text(size=20, weight=ft.FontWeight.BOLD)
    card_resumo_dashboard_geral = ft.Card(
        elevation=5,
        content=ft.Container(
            padding=15,
            content=ft.Column(
                [
                    ft.Row(
                        [ft.Text("Total Ganho:"), txt_total_ganho_mes],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Row(
                        [ft.Text("Total Gasto:"), txt_total_gasto_mes],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(),
                    ft.Row(
                        [ft.Text("Lucro do Mês:", weight=ft.FontWeight.BOLD, size=18), txt_lucro_mes],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ]
            ),
        ),
    )

    txt_resumo_filtrado_titulo = ft.Text(weight=ft.FontWeight.BOLD, size=18)
    txt_resumo_filtrado_valor = ft.Text(size=20, weight=ft.FontWeight.BOLD)
    card_resumo_dashboard_filtrado = ft.Card(
        elevation=5,
        visible=False,
        content=ft.Container(
            padding=15,
            content=ft.Row(
                [txt_resumo_filtrado_titulo, txt_resumo_filtrado_valor],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        ),
    )

    # --- Views ---
    inicio_view = ft.Column(
        [card_cofre, card_resumo, card_nova_transacao],
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    dashboard_view = ft.Column(
        controls=[],
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
        visible=False,
        expand=True,
    )

    # Carteira (Metas)
    carteira_view = ft.Column(
        [
            ft.Text("Carteira", size=24, weight=ft.FontWeight.BOLD),
            # cards de metas entram dinamicamente
        ],
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False,
    )

    # Ajustes (com Backup/Restore e Gerenciar Categorias)
    card_relatorios = ft.Card(
        elevation=4,
        content=ft.Container(
            padding=15,
            content=ft.Column([
                ft.Text("Relatórios em PDF", weight=ft.FontWeight.BOLD),
                ft.Text("Selecione um período para gerar o relatório."),

                # Seletores de Data Manuais
                ft.Row([
                    ft.Text("De:"), data_inicio_relatorio,
                    ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, on_click=abrir_datepicker_relatorio, data="inicio"),
                    ft.Text("Até:"), data_fim_relatorio,
                    ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, on_click=abrir_datepicker_relatorio, data="fim"),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                
                # Botões de Atalho
                ft.Row([
                    ft.ElevatedButton("Mês Atual", on_click=definir_periodo_relatorio, data="mes", expand=True),
                    ft.ElevatedButton("3 Meses", on_click=definir_periodo_relatorio, data="3_meses", expand=True),
                ]),
                ft.Row([
                    ft.ElevatedButton("6 Meses", on_click=definir_periodo_relatorio, data="6_meses", expand=True),
                    ft.ElevatedButton("1 Ano", on_click=definir_periodo_relatorio, data="ano", expand=True),
                ]),
                
                ft.Divider(height=20),
                
                # Botão principal para gerar
                ft.ElevatedButton(
                    "Gerar e Salvar PDF",
                    icon=ft.Icons.PICTURE_AS_PDF,
                    bgcolor=ft.Colors.RED_700,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: file_picker_salvar_pdf.save_file(
                        dialog_title="Salvar Relatório PDF Como...",
                        file_name=f"relatorio_financeiro.pdf",
                        allowed_extensions=["pdf"]
                    ),
                    expand=True
                ),
            ])
        )
    )

    card_categorias = ft.Card(
        elevation=4,
        content=ft.Container(
            padding=ft.padding.all(15),
            content=ft.Column(
                [
                    ft.Text("Gerenciar Categorias", weight=ft.FontWeight.BOLD),
                    ft.Row(
                        controls=[
                            ft.OutlinedButton(
                                "Nova Categoria", icon=ft.Icons.ADD, on_click=adicionar_nova_categoria
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    ft.Container(
                        content=lista_categorias_view, # <-- Use o nome correto da variável aqui
                        height=200, 
                        border=ft.border.all(1, "grey"),
                        border_radius=5,
                        padding=10
                    ),
                ],
                spacing=10,
            ),
        ),
    )

    configuracoes_view = ft.Column(
        [
            ft.Text("Ajustes", size=24, weight=ft.FontWeight.BOLD),
            
            # Card de Gerenciamento de Categorias
            ft.Card(
                elevation=4,
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Gerenciar Categorias", weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=lista_categorias_view,
                            height=200,
                            border=ft.border.all(1, ft.Colors.with_opacity(0.5, "white")),
                            border_radius=5,
                            padding=10
                        ),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Adicionar Categoria",
                                    on_click=adicionar_nova_categoria,
                                    icon=ft.Icons.ADD
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ])
                )
            ),
        ],
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
        visible=False
    )

    # main.py

    relatorios_view = ft.Column(
        [
            ft.Text("Relatórios", size=24, weight=ft.FontWeight.BOLD),
            ft.Card(
                elevation=4,
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Filtros do Relatório", weight=ft.FontWeight.BOLD),
                        
                        # Filtros de Tipo e Categoria
                        ft.Row([filtro_tipo_relatorio, filtro_categoria_relatorio]),
                        
                        ft.Divider(height=10),
                        
                        # Seletores de Data
                        ft.Text("Selecione um Período"),
                        ft.Row([
                            ft.Text("De:"), data_inicio_relatorio,
                            ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, on_click=abrir_datepicker_relatorio, data="inicio"),
                            ft.Text("Até:"), data_fim_relatorio,
                            ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, on_click=abrir_datepicker_relatorio, data="fim"),
                        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                        
                        # Botões de Atalho
                        ft.Row([
                            ft.ElevatedButton("Mês Atual", on_click=definir_periodo_relatorio, data="mes", expand=True),
                            ft.ElevatedButton("3 Meses", on_click=definir_periodo_relatorio, data="3_meses", expand=True),
                        ]),
                        ft.Row([
                            ft.ElevatedButton("6 Meses", on_click=definir_periodo_relatorio, data="6_meses", expand=True),
                            ft.ElevatedButton("1 Ano", on_click=definir_periodo_relatorio, data="ano", expand=True),
                        ]),
                        
                        ft.Divider(height=20),
                        
                        # Botão para Gerar
                        ft.ElevatedButton(
                            "Gerar e Salvar PDF", icon=ft.Icons.PICTURE_AS_PDF,
                            bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE,
                            on_click=lambda _: file_picker_salvar_pdf.save_file(
                                dialog_title="Salvar Relatório PDF Como...",
                                file_name=f"relatorio_financeiro.pdf",
                                allowed_extensions=["pdf"]
                            ),
                            expand=True
                        ),
                    ])
                )
            )
        ],
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
        visible=False # Começa invisível
    )

    # FAB global (visível só na Carteira)
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD, on_click=abrir_dialogo_nova_meta
    )

    def navigate(e):
        index = page.navigation_bar.selected_index
        inicio_view.visible = (index == 0)
        dashboard_view.visible = (index == 1)
        carteira_view.visible = (index == 2)
        relatorios_view.visible = (index == 3) # <-- NOVA LÓGICA
        configuracoes_view.visible = (index == 4) # <-- ÍNDICE ATUALIZADO

        if index == 1:
            atualizar_views()
        if index == 3: # Se abriu a tela de Relatórios
            tipo_relatorio_changed(None) # Para carregar as categorias
        if index == 4: # Se abriu a tela de Ajustes
            carregar_e_exibir_categorias()

        page.floating_action_button.visible = (index == 2) # FAB só na Carteira
        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=navigate,
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
                label="Relatórios"),

            ft.NavigationBarDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="Ajustes",
            ),
        ],
    )

    # Layout raiz com padding para status bar
    page.add(
        ft.Column(
            expand=True,
            controls=[
                ft.Container(
                    expand=True,
                    padding=ft.padding.only(top=40, left=15, right=15, bottom=15),
                    content=ft.Stack(
                        [inicio_view, dashboard_view, carteira_view, relatorios_view, configuracoes_view]
                    ),
                )
            ],
        )
    )

    # Inicializações
    carregar_dados_iniciais()
    carregar_metas()
    carregar_e_exibir_categorias()  # pré-carrega lista em Ajustes

    timestamp_salvo = db.get_config_value_db(page, 'ultima_alteracao')
    if timestamp_salvo:
        txt_ultima_atualizacao.value = timestamp_salvo
    else:
        txt_ultima_atualizacao.value = "Nenhuma alteração registrada."

    dd_categoria.options = [ft.dropdown.Option(cat['nome']) for cat in db.buscar_categorias_db(page)]
    page.floating_action_button.visible = False
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
