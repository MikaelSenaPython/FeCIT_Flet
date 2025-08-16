# Flet é uma biblioteca para criar interfaces de usuário (UI) em Python.
# Este exemplo mostra como criar uma aplicação simples que exibe texto na tela.

#flet run aula01.py -w

import flet as ft

def main(page: ft.Page):
    ola = ft.Text("Olá, Mundo!", size=30) # Criar um controle de texto com o texto "Olá, Mundo!" e tamanho 30.
    page.controls.append(ola) # Adicionar o texto no controle da página.
    page.update() # Atualizar a página para mostrar o texto.




ft.app(target=main, view=ft.AppView.WEB_BROWSER)
# ft.app(target=main) # Executar a aplicação com a função main como ponto de entrada.