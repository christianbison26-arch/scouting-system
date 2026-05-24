# Variabili
DC = docker compose

.PHONY: help start stop logs clean pull restart

help:
	@echo "Comandi disponibili:"
	@echo "  make start   - Costruisce e avvia tutti i servizi (App, DB, Ollama)"
	@echo "  make pull    - Scarica i modelli AI dentro il container Ollama"
	@echo "  make stop    - Ferma tutti i servizi"
	@echo "  make logs    - Mostra i log dell'app Streamlit in tempo reale"
	@echo "  make clean   - Rimuove i container e i volumi (Attenzione: cancella il DB)"

start:
	$(DC) up -d --build
	@echo "L'app sarà disponibile a breve su http://localhost:8501"

stop:
	$(DC) down

restart:
	$(DC) down
	$(DC) up -d --build
	@echo "L'app sarà disponibile a breve su http://localhost:8501"

logs:
	$(DC) logs -f app

clean:
	@echo "⚠️  Attenzione: questa operazione cancella il DB e tutti i volumi!"
	@read -p "Sei sicuro? [y/N] " confirm && [ "$$confirm" = "y" ]
	$(DC) down -v

pull:
	@echo "Scaricamento modelli (Llama3 e Embeddings)..."
	docker exec -it ollama-service ollama pull llama3
	docker exec -it ollama-service ollama pull nomic-embed-text
	@echo "Modelli pronti."