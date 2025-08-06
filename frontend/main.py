import flet as ft
import requests

API_URL = "http://127.0.0.1:8000/api/"  # Asegúrate de que tu API DRF esté corriendo

def main(page: ft.Page):
    page.title = "Flet + DRF Auth"
    page.scroll = "auto"

    username = ft.TextField(label="Usuario")
    password = ft.TextField(label="Contraseña", password=True, can_reveal_password=True)
    resultado = ft.Text()

    def mostrar_bienvenida(nombre, experiencia, coint):
        page.controls.clear()
        page.add(
            ft.Container(
                content=ft.Card(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.PERSON, size=40),
                            ft.Text(f"Bienvenido, {nombre}!", size=28, weight="bold"),
                        ], alignment="center"),
                        ft.Divider(),
                        ft.Row([
                            ft.Icon(ft.icons.MONETIZATION_ON, color="gold", size=30),
                            ft.Text(f"Monedas: {coint}", size=22),
                        ], alignment="center"),
                        ft.Row([
                            ft.Icon(ft.icons.STAR, color="orange", size=30),
                            ft.Text(f"Experiencia: {experiencia}", size=22),
                        ], alignment="center"),
                        ft.Divider(),
                        ft.Text("¡Has iniciado sesión correctamente!", size=18, italic=True, color="green"),
                    ], spacing=20, alignment="center"),
                ),
                padding=30,
                alignment=ft.alignment.center,
            )
        )
        page.update()

    def login(e):
        try:
            r = requests.post(API_URL + "login/", json={
                "username": username.value,
                "password": password.value
            })
            if r.status_code == 200:
                token = r.json()["access"]
                headers = {"Authorization": f"Bearer {token}"}
                r_profile = requests.get(API_URL + "profile/", headers=headers)
                if r_profile.status_code == 200:
                    data = r_profile.json()
                    mostrar_bienvenida(data["username"], data["experiencia"], data["coint"])
                else:
                    resultado.value = "No se pudo obtener perfil."
                    page.update()
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
