# ProScout AI

> Italiano | [English below](#proscout-ai-1)

---

## Italiano — ProScout AI

Una piattaforma avanzata di **Sports Analytics** che combina statistiche calcistiche reali con la potenza dei Large Language Models (LLM), il tutto eseguito **interamente in locale** per garantire privacy e controllo dei dati.

> **Progetto educativo** — Realizzato a scopo di apprendimento. I dati utilizzati provengono da un dataset pubblico su Kaggle e non vengono mai redistribuiti.

---

### Funzionalità principali

**Home**
- Pagina introduttiva con card interattive che descrivono le funzionalità del sistema
- Si adatta automaticamente al tema chiaro/scuro

**Analytics**
- Analisi statistica interattiva tramite grafici Plotly
- 4 preset di analisi selezionabili:
  - **Top scorer per club** — visualizza i migliori giocatori di un club per qualsiasi statistica
  - **Confronto tra due giocatori** — grafico comparativo con statistiche personalizzabili
  - **Distribuzione ruoli per club** — grafico a torta con dettaglio per ruolo
  - **Top giocatori per statistica** — classifica globale filtrabile per ruolo

**AI Chat**
- Chatbot basato su **Llama 3** con memoria della conversazione
- Supporta domande in **italiano e inglese** — rileva automaticamente la lingua
- Due modalità di risposta:
  - **SQL** — per domande statistiche precise ("Quanti gol ha segnato De Bruyne?")
  - **RAG** — per domande semantiche ("Chi sono i portieri dell'Arsenal?")
- Implementa **RAG** (Retrieval-Augmented Generation) con pgvector
- Query SQL dirette su PostgreSQL per statistiche comparative

---

### Tecnologie utilizzate

| Tecnologia | Ruolo |
|---|---|
| Python 3.10 | Linguaggio principale |
| Streamlit | Interfaccia web |
| Docker & Docker Compose | Orchestrazione dei servizi |
| PostgreSQL + pgvector | Database vettoriale e relazionale |
| Ollama | LLM e embeddings in locale (Llama3 + mxbai-embed-large) |
| LangChain | Framework RAG |
| pandas | Elaborazione del dataset CSV |
| Plotly | Grafici interattivi |
| SQLAlchemy | Query SQL dirette |

---

### Installazione e avvio

#### Prerequisiti
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- `make` (`sudo apt install build-essential` su Ubuntu/WSL2)
- WSL2 (se sei su Windows)

#### Configurazione

Crea un file `.env` nella root del progetto (usa `.env.example` come riferimento):

```bash
cp .env.example .env
```

Modifica `.env` con le tue credenziali:

```env
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_db
DATABASE_URL=postgresql://your_user:your_password@db:5432/your_db
OLLAMA_BASE_URL=http://ollama:11434
```

#### Dataset

Scarica il dataset da Kaggle e copialo nella cartella `data/`:

1. Scarica il CSV da [Kaggle — English Premier League Players Statistics](https://www.kaggle.com/code/desalegngeb/english-premier-league-players-statistics/notebook)
2. Rinominalo in `dataset_-_2020-09-24.csv` e copialo in `data/`

```bash
cp /percorso/del/file/dataset_-_2020-09-24.csv data/
```

#### Avvio

```bash
# Avvia tutti i servizi (App, DB, Ollama)
make start

# Scarica i modelli AI (solo la prima volta)
make pull
```

Apri il browser su **http://localhost:8501**

#### Caricamento dati

Una volta avviata l'app, carica i dati dalla **sidebar** cliccando su "Carica Dati Premier League". Il sistema creerà automaticamente sia il vectorstore che la tabella SQL.

#### Altri comandi utili

```bash
make stop      # Ferma tutti i servizi
make restart   # Riavvia e ricostruisce l'immagine
make logs      # Mostra i log dell'app in tempo reale
make clean     # Rimuove container e volumi (attenzione: cancella il DB)
```

---

### Struttura del progetto

```
proscout-ai/
├── data/                          # Dataset CSV (escluso da git)
│   └── dataset_-_2020-09-24.csv  # Da scaricare da Kaggle
├── src/
│   ├── main.py                    # Interfaccia Streamlit (UI)
│   ├── chat.py                    # Logica AI Chat (RAG + SQL)
│   ├── scout.py                   # Logica ricerca vettoriale (pgvector)
│   ├── ingest.py                  # Ingestion dati CSV -> vectorstore + SQL
│   ├── style.css                  # Design adattivo chiaro/scuro
│   └── __init__.py                # Definizione pacchetto Python
├── .env.example                   # Template variabili d'ambiente
├── .gitignore                     # File e cartelle escluse da git
├── Dockerfile                     # Configurazione container App
├── docker-compose.yml             # Orchestrazione App, DB e Ollama
├── Makefile                       # Comandi rapidi di gestione
└── requirements.txt               # Dipendenze Python
```

---

### Note importanti

- **Privacy**: tutto il processo AI avviene localmente tramite Ollama. Nessun dato viene inviato a server esterni.
- **Dataset**: la cartella `data/` è esclusa da git. Ogni utente deve scaricare il CSV da Kaggle seguendo le istruzioni sopra.
- **Modelli AI**: al primo avvio esegui `make pull` per scaricare Llama3 (~4GB) e mxbai-embed-large (~670MB).
- **Limitazioni SQL**: il sistema SQL è basato su pattern matching — domande molto complesse o ambigue potrebbero non essere riconosciute correttamente.
- **Caricamento dati**: durante il caricamento del dataset dalla sidebar, Streamlit mostra il pulsante "Stop" in alto a destra — è un comportamento normale del framework per operazioni lunghe e non indica un errore. Al termine del caricamento il pulsante scompare automaticamente.

---

### Miglioramenti futuri

Il progetto nella sua forma attuale è funzionante e completo per scopi educativi. Tuttavia, esistono alcune aree di miglioramento che potrebbero rendere il sistema più robusto ed efficiente:

**Integrazione con API AI esterne**
L'attuale sistema utilizza Llama 3 in locale tramite Ollama. Una versione più avanzata potrebbe integrare API esterne come Claude API di Anthropic, che garantirebbe risposte più precise, migliore comprensione del linguaggio naturale e supporto nativo per query SQL complesse.

**Introduzione di un MCP Server**
Per mantenere i dati completamente isolati e sicuri, si potrebbe introdurre un [MCP Server (Model Context Protocol)](https://modelcontextprotocol.io) come layer intermedio tra l'AI e il database. In questo modo il modello non avrebbe accesso diretto ai dati, ma solo attraverso strumenti controllati e sicuri — un pattern architetturale molto più robusto per ambienti di produzione.

**Altre migliorie possibili**
- Aggiornamento automatico del dataset tramite API ufficiali
- Supporto multi-campionato (Serie A, La Liga, Bundesliga)
- Sistema di autenticazione per ambienti multi-utente
- Dashboard esportabile in PDF

---

### Sviluppato con il supporto di AI

Il progetto è stato sviluppato con il supporto di **Claude** (Anthropic) come strumento di assistenza. Tutte le scelte architetturali, le decisioni tecniche e la comprensione del codice sono dell'autore, l'AI ha accelerato il processo senza sostituire il ragionamento critico.

---
---

## English — ProScout AI

An advanced **Sports Analytics** platform that combines real football statistics with the power of Large Language Models (LLMs), running **entirely locally** to ensure privacy and data control.

> **Educational project** — Built for learning purposes. Data comes from a public Kaggle dataset and is never redistributed.

---

### Key Features

**Home**
- Introductory page with interactive cards describing the system's features
- Automatically adapts to light/dark theme

**Analytics**
- Interactive statistical analysis via Plotly charts
- 4 selectable analysis presets:
  - **Top scorer per club** — display the best players of a club for any statistic
  - **Player comparison** — comparative chart with customizable statistics
  - **Role distribution per club** — pie chart with role breakdown
  - **Top players by statistic** — global ranking filterable by role

**AI Chat**
- Chatbot powered by **Llama 3** with conversation memory
- Supports questions in **Italian and English** — automatically detects the language
- Two response modes:
  - **SQL** — for precise statistical questions ("How many goals did De Bruyne score?")
  - **RAG** — for semantic questions ("Who are the Arsenal goalkeepers?")
- Implements **RAG** (Retrieval-Augmented Generation) with pgvector
- Direct SQL queries on PostgreSQL for comparative statistics

---

### Tech Stack

| Technology | Role |
|---|---|
| Python 3.10 | Core language |
| Streamlit | Web interface |
| Docker & Docker Compose | Service orchestration |
| PostgreSQL + pgvector | Vector and relational database |
| Ollama | Local LLM and embeddings (Llama3 + mxbai-embed-large) |
| LangChain | RAG framework |
| pandas | CSV dataset processing |
| Plotly | Interactive charts |
| SQLAlchemy | Direct SQL queries |

---

### Installation & Setup

#### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- `make` (`sudo apt install build-essential` on Ubuntu/WSL2)
- WSL2 (if on Windows)

#### Configuration

Create a `.env` file in the project root (use `.env.example` as reference):

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_db
DATABASE_URL=postgresql://your_user:your_password@db:5432/your_db
OLLAMA_BASE_URL=http://ollama:11434
```

#### Dataset

Download the dataset from Kaggle and copy it to the `data/` folder:

1. Download the CSV from [Kaggle — English Premier League Players Statistics](https://www.kaggle.com/code/desalegngeb/english-premier-league-players-statistics/notebook)
2. Rename it to `dataset_-_2020-09-24.csv` and copy it to `data/`

```bash
cp /path/to/file/dataset_-_2020-09-24.csv data/
```

#### Start

```bash
# Start all services (App, DB, Ollama)
make start

# Download AI models (first time only)
make pull
```

Open your browser at **http://localhost:8501**

#### Loading data

Once the app is running, load the data from the **sidebar** by clicking "Carica Dati Premier League". The system will automatically create both the vectorstore and the SQL table.

#### Other useful commands

```bash
make stop      # Stop all services
make restart   # Restart and rebuild the image
make logs      # Stream app logs in real time
make clean     # Remove containers and volumes (warning: deletes the DB)
```

---

### Project Structure

```
proscout-ai/
├── data/                          # CSV dataset (git-ignored)
│   └── dataset_-_2020-09-24.csv  # Download from Kaggle
├── src/
│   ├── main.py                    # Streamlit UI
│   ├── chat.py                    # AI Chat logic (RAG + SQL)
│   ├── scout.py                   # Vector search logic (pgvector)
│   ├── ingest.py                  # CSV ingestion -> vectorstore + SQL
│   ├── style.css                  # Adaptive light/dark design
│   └── __init__.py                # Python package definition
├── .env.example                   # Environment variables template
├── .gitignore                     # Git-ignored files and folders
├── Dockerfile                     # App container configuration
├── docker-compose.yml             # App, DB and Ollama orchestration
├── Makefile                       # Quick management commands
└── requirements.txt               # Python dependencies
```

---

### Important Notes

- **Privacy**: all AI processing runs locally via Ollama. No data is ever sent to external servers.
- **Dataset**: the `data/` folder is git-ignored. Each user must download the CSV from Kaggle following the instructions above.
- **AI Models**: on first run, execute `make pull` to download Llama3 (~4GB) and mxbai-embed-large (~670MB).
- **SQL Limitations**: the SQL system is based on pattern matching — very complex or ambiguous questions may not be recognized correctly.
- **Data loading**: during dataset loading from the sidebar, Streamlit displays a "Stop" button in the top right corner — this is normal framework behavior for long operations and does not indicate an error. The button disappears automatically once loading is complete.
---

### Future Improvements

The project in its current form is functional and complete for educational purposes. However, there are several areas of improvement that could make the system more robust and efficient:

**Integration with external AI APIs**
The current system uses Llama 3 locally via Ollama. A more advanced version could integrate external APIs such as Anthropic's Claude API, which would provide more accurate responses, better natural language understanding, and native support for complex SQL queries.

**Introduction of an MCP Server**
To keep data completely isolated and secure, an [MCP Server (Model Context Protocol)](https://modelcontextprotocol.io) could be introduced as an intermediate layer between the AI and the database. This way the model would not have direct access to the data, but only through controlled and secure tools — a much more robust architectural pattern for production environments.

**Other possible improvements**
- Automatic dataset updates via official APIs
- Multi-league support (Serie A, La Liga, Bundesliga)
- Authentication system for multi-user environments
- Exportable PDF dashboard

---

### Developed with AI support

This project was developed with the support of **Claude** (Anthropic) as an assistance tool. All architectural choices, technical decisions and code understanding belong to the author, AI accelerated the process without replacing critical thinking.