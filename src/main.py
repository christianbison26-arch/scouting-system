import streamlit as st
import os
import pandas as pd
import plotly.express as px
from langchain_core.documents import Document
from src.scout import similarity_search_with_score, get_vectorstore, clear_database
from src.chat import get_chat_response

# --- FUNZIONE CSS (cachata) ---
@st.cache_data
def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            return f.read()
    return ""

# --- CARICAMENTO DATI (cachato) ---
@st.cache_data
def load_dataframe():
    try:
        return pd.read_csv("/app/data/dataset_-_2020-09-24.csv")
    except FileNotFoundError:
        return pd.DataFrame()

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="ProScout AI", page_icon="⚽", layout="wide")
css = load_css("src/style.css")
if css:
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚽ Dashboard")

    try:
        from src.scout import get_document_count
        count = get_document_count()
        st.info(f"📊 Documenti nel DB: {count}")
    except Exception:
        st.info("📊 Documenti nel DB: N/D")

    st.divider()

    # --- Caricamento dati ---
    st.subheader("📥 Carica Dati")

    # Inizializza lo stato
    if "loading_done" not in st.session_state:
        st.session_state.loading_done = False
    if "loading_count" not in st.session_state:
        st.session_state.loading_count = 0

    if st.button("📥 Carica Dati Premier League", use_container_width=True):
        st.session_state.loading_done = False
        with st.spinner("Caricamento in corso..."):
            try:
                from src.ingest import fetch_kaggle_data
                docs = fetch_kaggle_data()
                get_vectorstore().add_documents(docs)
                st.session_state.loading_done = True
                st.session_state.loading_count = len(docs)
            except Exception as e:
                st.error(f"❌ Errore: {e}")

    if st.session_state.loading_done:
        st.success(f"✅ Caricati {st.session_state.loading_count} giocatori!")

    st.divider()

    if st.button("🗑️ Svuota Database", use_container_width=True):
        clear_database()
        st.session_state.loading_done = False
        st.session_state.loading_count = 0
        st.success("Database pulito!")
        st.rerun()

st.title("🏟️ Scouting & Intelligence System")

tab1, tab2, tab3 = st.tabs(["🏠 Home", "📊 Analytics", "🤖 AI Chat"])

# --- TAB 1: HOME ---
with tab1:
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0 1rem 0;">
            <h1 style="font-size: 2.5rem;">⚽ ProScout AI</h1>
            <p style="font-size: 1.2rem; color: #666;">
                Il tuo analista tattico intelligente per la Premier League
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
            <div class="player-card">
                <div class="player-name">📊 Analytics</div>
                <p>Analizza le statistiche della Premier League attraverso grafici interattivi.</p>
                <ul>
                    <li>Top scorer per club</li>
                    <li>Confronto tra giocatori</li>
                    <li>Distribuzione dei ruoli</li>
                    <li>Top giocatori per statistica</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="player-card">
                <div class="player-name">🤖 AI Chat</div>
                <p>Interroga il database in linguaggio naturale, in italiano o in inglese.</p>
                <ul>
                    <li>Domande su giocatori specifici</li>
                    <li>Statistiche comparative</li>
                    <li>Ricerca per club e ruolo</li>
                    <li>Memoria della conversazione</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class="player-card">
                <div class="player-name">📊 Dataset</div>
                <p>Basato su dati reali della Premier League 2019/20.</p>
                <ul>
                    <li>571 giocatori</li>
                    <li>20 club</li>
                    <li>59 statistiche per giocatore</li>
                    <li>Fonte: Kaggle</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.9rem;">
            💡 <b>Come iniziare:</b> Carica i dati dalla sidebar, poi esplora Analytics o chatta con l'AI.
        </div>
    """, unsafe_allow_html=True)

# --- TAB 2: ANALYTICS ---
with tab2:
    st.header("📊 Analytics — Analisi Statistica")

    df = load_dataframe()

    if df.empty:
        st.warning("⚠️ Nessun dato disponibile. Carica i dati dalla sidebar.")
    else:
        # --- Preset selector ---
        preset = st.selectbox(
            "Seleziona analisi:",
            [
                "🥇 Top scorer per club",
                "⚔️ Confronto tra due giocatori",
                "🧩 Distribuzione ruoli per club",
                "📈 Top giocatori per statistica",
            ]
        )

        st.divider()

        # --- PRESET 1: Top scorer per club ---
        if preset == "🥇 Top scorer per club":
            col1, col2 = st.columns([2, 1])
            with col1:
                club = st.selectbox("Club:", sorted(df["Club"].unique()))
            with col2:
                stat = st.selectbox("Statistica:", [
                    "Goals", "Assists", "Appearances",
                    "Tackles", "Saves", "Passes"
                ])

            filtered = df[df["Club"] == club][["Name", "Position", stat]].dropna()
            filtered = filtered[filtered[stat] > 0].sort_values(stat, ascending=False).head(10)

            if filtered.empty:
                st.info("Nessun dato disponibile per questa combinazione.")
            else:
                fig = px.bar(
                    filtered,
                    x="Name",
                    y=stat,
                    color="Position",
                    title=f"Top giocatori del {club} per {stat}",
                    labels={"Name": "Giocatore", stat: stat},
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig.update_layout(xaxis_tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)

        # --- PRESET 2: Confronto tra due giocatori ---
        elif preset == "⚔️ Confronto tra due giocatori":
            players = sorted(df["Name"].unique())
            col1, col2 = st.columns(2)
            with col1:
                p1 = st.selectbox("Giocatore 1:", players, index=0)
            with col2:
                p2 = st.selectbox("Giocatore 2:", players, index=1)

            stats_to_compare = st.multiselect(
                "Statistiche da confrontare:",
                ["Goals", "Assists", "Appearances", "Tackles",
                 "Passes", "Saves", "Yellow cards", "Red cards",
                 "Shots", "Shots on target"],
                default=["Goals", "Assists", "Appearances"]
            )

            if stats_to_compare:
                p1_data = df[df["Name"] == p1][stats_to_compare].fillna(0).iloc[0]
                p2_data = df[df["Name"] == p2][stats_to_compare].fillna(0).iloc[0]

                compare_df = pd.DataFrame({
                    "Statistica": stats_to_compare,
                    p1: p1_data.values,
                    p2: p2_data.values,
                })

                fig = px.bar(
                    compare_df.melt(id_vars="Statistica", var_name="Giocatore", value_name="Valore"),
                    x="Statistica",
                    y="Valore",
                    color="Giocatore",
                    barmode="group",
                    title=f"Confronto: {p1} vs {p2}",
                    color_discrete_sequence=["#007bff", "#ff6b6b"]
                )
                st.plotly_chart(fig, use_container_width=True)

                # Tabella riepilogativa
                st.dataframe(compare_df.set_index("Statistica"), use_container_width=True)

        # --- PRESET 3: Distribuzione ruoli per club ---
        elif preset == "🧩 Distribuzione ruoli per club":
            club = st.selectbox("Club:", sorted(df["Club"].unique()))
            filtered = df[df["Club"] == club]["Position"].value_counts().reset_index()
            filtered.columns = ["Ruolo", "Conteggio"]

            fig = px.pie(
                filtered,
                names="Ruolo",
                values="Conteggio",
                title=f"Distribuzione ruoli — {club}",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig, use_container_width=True)

            # Tabella giocatori per ruolo
            role = st.selectbox(
                "Dettaglio per ruolo:",
                sorted(df[df["Club"] == club]["Position"].unique())
            )
            role_df = df[(df["Club"] == club) & (df["Position"] == role)][
                ["Name", "Goals", "Assists", "Appearances"]
            ].fillna(0).sort_values("Appearances", ascending=False)
            st.dataframe(role_df.set_index("Name"), use_container_width=True)

        # --- PRESET 4: Top giocatori per statistica ---
        elif preset == "📈 Top giocatori per statistica":
            col1, col2, col3 = st.columns(3)
            with col1:
                stat = st.selectbox("Statistica:", [
                    "Goals", "Assists", "Appearances", "Tackles",
                    "Saves", "Passes", "Shots", "Yellow cards",
                    "Red cards", "Clean sheets"
                ])
            with col2:
                position_filter = st.selectbox(
                    "Filtra per ruolo:",
                    ["Tutti", "Goalkeeper", "Defender", "Midfielder", "Forward"]
                )
            with col3:
                top_n = st.slider("Numero di giocatori:", 5, 20, 10)

            filtered = df.copy()
            if position_filter != "Tutti":
                filtered = filtered[filtered["Position"] == position_filter]

            filtered = filtered[["Name", "Club", "Position", stat]].dropna()
            filtered = filtered[filtered[stat] > 0].sort_values(stat, ascending=False).head(top_n)

            if filtered.empty:
                st.info("Nessun dato disponibile per questa combinazione.")
            else:
                fig = px.bar(
                    filtered,
                    x="Name",
                    y=stat,
                    color="Club",
                    title=f"Top {top_n} giocatori per {stat}",
                    labels={"Name": "Giocatore"},
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(xaxis_tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(filtered.set_index("Name"), use_container_width=True)

# --- TAB 3: AI CHAT ---
with tab3:
    st.header("🤖 Conversazione AI")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Chiedi all'analista..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response = get_chat_response(
                    prompt,
                    chat_history=st.session_state.messages
                )
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Errore: {e}")