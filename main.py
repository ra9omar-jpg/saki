"""Entry point for Saki — start with: python main.py"""
import atexit
from webhook.app import create_app
from scheduler.scheduler import start as start_scheduler, stop as stop_scheduler
from config import config

app = create_app()
start_scheduler(app)
atexit.register(stop_scheduler)

if __name__ == "__main__":
    print(f"Saki er klar. Kører på port {config.PORT}.")
    app.run(host="0.0.0.0", port=config.PORT, debug=False)
