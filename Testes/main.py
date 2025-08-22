import flet as ft

def main(page: ft.Page):
    page.title = "Contador de Exemplo"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # VARIÁVEIS E CONTROLES GLOBAIS
    limite_cliques = 10 
    txt_number = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, width=100)
    parabens_text = ft.Text("Parabéns, você chegou ao limite!", visible=False, size=20, weight=ft.FontWeight.BOLD)
    
    # Campo de texto dentro do BottomSheet
    limite_input = ft.TextField(
        label="Digite o novo limite", 
        value=str(limite_cliques), 
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    
    # FUNÇÕES PARA O BOTTOMSHEET
    def fechar_bottom_sheet(e):
        bottom_sheet.open = False
        page.update()

    def confirmar_limite(e):
        nonlocal limite_cliques
        try:
            novo_limite = int(limite_input.value)
            limite_cliques = novo_limite
            if int(txt_number.value) > limite_cliques:
                txt_number.value = "0"
                parabens_text.visible = False
            
            fechar_bottom_sheet(e)
            
        except ValueError:
            limite_input.error_text = "Por favor, digite um número inteiro."
            page.update()

    # DEFINIÇÃO DO BOTTOMSHEET
    bottom_sheet = ft.BottomSheet(
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("Definir Novo Limite", size=20, weight=ft.FontWeight.BOLD),
                    limite_input,
                    ft.Row(
                        [
                            ft.TextButton("Cancelar", on_click=fechar_bottom_sheet),
                            ft.ElevatedButton("OK", on_click=confirmar_limite),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                tight=True
            ),
            padding=ft.padding.all(20),
        )
    )

    def abrir_bottom_sheet(e):
        bottom_sheet.open = True
        page.update()

    # ATRIBUIMOS O BOTTOMSHEET À PÁGINA
    page.bottom_sheet = bottom_sheet

    # FUNÇÕES PARA O CONTADOR
    def subtrair(e):
        valor_atual = int(txt_number.value)
        novo_valor = valor_atual - 1
        txt_number.value = str(novo_valor)
        
        if novo_valor < limite_cliques:
            parabens_text.visible = False
        
        page.update()

    def somar(e):
        valor_atual = int(txt_number.value)
        novo_valor = valor_atual + 1
        txt_number.value = str(novo_valor)

        if novo_valor == limite_cliques:
            parabens_text.visible = True
        
        page.update()
    
    def zerar(e):
        txt_number.value = "0"
        parabens_text.visible = False
        page.update()

    # LAYOUT DA PÁGINA
    page.add(
        ft.Column(
            [
                ft.Text("Contador de Cliques", size=24), 
                parabens_text,
                ft.Row(
                    [
                        ft.IconButton(ft.Icons.REMOVE, on_click=subtrair),
                        txt_number,
                        ft.IconButton(ft.Icons.ADD, on_click=somar),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.IconButton(ft.Icons.RESTART_ALT, on_click=zerar, tooltip="Zerar contador"),
                        ft.ElevatedButton("Definir Limite", on_click=abrir_bottom_sheet)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

# EXECUÇÃO DO APLICATIVO
ft.app(target=main)