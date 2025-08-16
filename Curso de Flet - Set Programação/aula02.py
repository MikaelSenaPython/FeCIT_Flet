import flet as ft


def main(page):

    def login(e):
        if not entrada_nome.value:
            entrada_nome.error_text = "Por favor, preencha o eu nome!"
            page.update()
        if not entrada_senha.value:
            entrada_senha.error_text = "Campo de senha obrigatoriro!"
            page.update()
        else:
            nome = entrada_nome.value # Obtém o valor da entrada de nome
            senha = entrada_senha.value # Obtém o valor da entrada de senha
            print("Nome: {}\nSenha: {}".format(nome, senha))
            
            page.clean() # Função para limpar a página!!
            page.add(ft.Text("Olá, {}! Seja bem vindo(a) a nossa aplicação!".format(nome)))
            pass


    entrada_nome = ft.TextField(label="Digite o seu nome!")
    entrada_senha = ft.TextField(label="Digite a sua senha!")

    page.add(
        entrada_nome,
        entrada_senha,
        ft.ElevatedButton("Clique em mim!", on_click=login)

    )
    pass
    
ft.app(target=main, view=ft.AppView.WEB_BROWSER)
