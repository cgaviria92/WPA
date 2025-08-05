import flet as ft
import requests

API_URL = "http://127.0.0.1:8000/"  # Apunta al backend

def main(page: ft.Page):
    page.title = "Flet + DRF"
    page.scroll = "auto"

    def enviar(e):
        r = requests.get(API_URL)
        resultado.value = f"Respuesta: {r.status_code}"
        page.update()

    boton = ft.ElevatedButton("Probar API", on_click=enviar)
    resultado = ft.Text()
    
    page.add(ft.Column([boton, resultado]))

ft.app(target=main)
