import flet as ft
import requests

API_URL = "http://127.0.0.1:8000/api/"  # Asegúrate de que tu API DRF esté corriendo

def main(page: ft.Page):
    page.title = "Flet + DRF Auth"
    page.scroll = "auto"

    username = ft.TextField(label="Usuario")
    password = ft.TextField(label="Contraseña", password=True, can_reveal_password=True)
    resultado = ft.Text()

    def mostrar_bienvenida(nombre):
        page.controls.clear()
        page.add(
            ft.Column([
                ft.Text(f"Bienvenido, {nombre}!", size=24, weight="bold"),
                ft.Text("Has iniciado sesión correctamente."),
            ])
        )
        page.update()

    def login(e):
        try:
            r = requests.post(API_URL + "login/", json={
                "username": username.value,
                "password": password.value
            })
            if r.status_code == 200:
                mostrar_bienvenida(username.value)
            else:
                resultado.value = f"Error: {r.json().get('detail', r.text)}"
                page.update()
        except Exception as err:
            resultado.value = f"Error de conexión: {err}"
            page.update()

    def register(e):
        try:
            r = requests.post(API_URL + "register/", json={
                "username": username.value,
                "password": password.value
            })
            if r.status_code == 201:
                resultado.value = "Usuario registrado correctamente"
            else:
                resultado.value = f"Error: {r.json().get('error', r.text)}"
            page.update()
        except Exception as err:
            resultado.value = f"Error de conexión: {err}"
            page.update()

    page.add(
        ft.Column([
            username,
            password,
            ft.Row([
                ft.ElevatedButton("Login", on_click=login),
                ft.ElevatedButton("Registrar", on_click=register),
            ]),
            resultado
        ])
    )

# 👇 Esto abre siempre en el navegador
ft.app(target=main, view=ft.AppView.WEB_BROWSER)
