
import flet as ft
import requests

API_URL = "http://127.0.0.1:8000/api/"

def main(page: ft.Page):
    page.title = "Flet + DRF Auth"
    page.scroll = "auto"

    username = ft.TextField(label="Usuario")
    password = ft.TextField(label="Contraseña", password=True, can_reveal_password=True)
    resultado = ft.Text()

    def login(e):
        r = requests.post(API_URL + "login/", json={
            "username": username.value,
            "password": password.value
        })
        if r.status_code == 200:
            resultado.value = f"Login OK. Token: {r.json()['access']}"
        else:
            resultado.value = f"Error: {r.json().get('detail', r.text)}"
        page.update()

    def register(e):
        r = requests.post(API_URL + "register/", json={
            "username": username.value,
            "password": password.value
        })
        if r.status_code == 201:
            resultado.value = "Usuario registrado correctamente"
        else:
            resultado.value = f"Error: {r.json().get('error', r.text)}"
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

ft.app(target=main)
