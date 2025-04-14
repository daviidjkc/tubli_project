from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)  # Configurar debug=False en producción
