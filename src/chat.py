import os
import streamlit as st
from sqlalchemy import create_engine, text
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from pydantic import Field
from src.scout import get_vectorstore

CLUBS = {
    "arsenal": "Arsenal",
    "liverpool": "Liverpool",
    "chelsea": "Chelsea",
    "manchester city": "Manchester-City",
    "manchester united": "Manchester-United",
    "tottenham": "Tottenham-Hotspur",
    "leicester": "Leicester-City",
    "everton": "Everton",
    "leeds": "Leeds-United",
    "aston villa": "Aston-Villa",
    "wolves": "Wolverhampton-Wanderers",
    "wolverhampton": "Wolverhampton-Wanderers",
    "west ham": "West-Ham-United",
    "brighton": "Brighton-and-Hove-Albion",
    "burnley": "Burnley",
    "crystal palace": "Crystal-Palace",
    "newcastle": "Newcastle-United",
    "southampton": "Southampton",
    "fulham": "Fulham",
    "west brom": "West-Bromwich-Albion",
    "sheffield": "Sheffield-United",
}

ROLES = {
    "goalkeeper": "Goalkeeper",
    "portiere": "Goalkeeper",
    "portieri": "Goalkeeper",
    "goalkeepers": "Goalkeeper",
    "defender": "Defender",
    "difensore": "Defender",
    "difensori": "Defender",
    "defenders": "Defender",
    "midfielder": "Midfielder",
    "centrocampista": "Midfielder",
    "centrocampisti": "Midfielder",
    "midfielders": "Midfielder",
    "forward": "Forward",
    "attaccante": "Forward",
    "attaccanti": "Forward",
    "forwards": "Forward",
}

SQL_KEYWORDS = [
    "quanti", "quante", "how many", "how much",
    "più", "most", "migliore", "best", "peggiore", "worst",
    "massimo", "maximum", "minimo", "minimum",
    "media", "average", "totale", "total",
    "top", "classifica", "ranking",
    "segnato", "scored",
    "assist", "presenze", "appearances",
    "gol", "goals", "parate", "saves",
]

STAT_KEYWORDS = {
    "goals": ["goal", "gol", "segnato", "scored"],
    "assists": ["assist"],
    "appearances": ["presenze", "appearances", "partite", "matches"],
    "saves": ["parate", "saves"],
    "yellow_cards": ["gialli", "ammonizioni", "yellow"],
    "red_cards": ["rossi", "espulsioni", "red card"],
    "tackles": ["tackle", "contrasti"],
    "clean_sheets": ["clean sheet", "imbattuto"],
    "goals_conceded": ["gol subiti", "goals conceded"],
}

IGNORE_WORDS = {
    "how", "many", "did", "score", "who", "are", "the", "what",
    "chi", "ha", "fatto", "quanti", "quante", "nel", "del", "per",
    "goals", "assists", "saves", "tackles", "tell", "me", "names",
    "play", "for", "that", "players", "giocatori", "portieri",
    "difensori", "centrocampisti", "attaccanti", "goalkeepers",
    "defenders", "midfielders", "forwards", "premier", "league",
}

ITALIAN_KEYWORDS = [
    "chi", "cosa", "quanti", "quante", "qual", "quale",
    "dimmi", "mostrami", "il", "la", "lo", "gli", "le",
    "del", "della", "nel", "nella", "per", "con", "più",
    "gol", "parate", "presenze", "portiere", "portieri",
    "difensore", "difensori", "centrocampista", "centrocampisti",
    "attaccante", "attaccanti", "segnato", "giocatori",
]


def _detect_language(query: str) -> str:
    """Rileva la lingua della domanda — 'it' o 'en'."""
    query_lower = query.lower()
    words = set(query_lower.split())
    
    # Keyword italiane esclusive — parole che esistono SOLO in italiano
    italian_exclusive = {
        "chi", "cosa", "quanti", "quante", "qual", "quale",
        "dimmi", "mostrami", "gli", "dello", "della", "nel",
        "nella", "negli", "nelle", "oppure", "oppure",
        "gol", "parate", "presenze", "portiere", "portieri",
        "difensore", "difensori", "centrocampista", "centrocampisti",
        "attaccante", "attaccanti", "segnato", "giocatori",
        "più", "migliore", "peggiore", "classifica",
    }

    # Keyword inglesi esclusive
    english_exclusive = {
        "who", "what", "how", "many", "much", "which",
        "the", "are", "did", "does", "score", "scored",
        "most", "best", "worst", "among", "between",
        "play", "plays", "played", "tell", "show",
        "goalkeeper", "goalkeepers", "defender", "defenders",
        "midfielder", "midfielders", "forward", "forwards",
    }

    italian_count = len(words & italian_exclusive)
    english_count = len(words & english_exclusive)

    # Se entrambi hanno match, vince chi ne ha di più
    # In caso di parità, default inglese
    return "it" if italian_count > english_count else "en"


def _get_language_config(lang: str) -> dict:
    """Restituisce le istruzioni di lingua per il prompt."""
    if lang == "it":
        return {
            "lang_instruction": "Rispondi in italiano, in modo formale e preciso.",
            "role_translations": (
                "Traduci i ruoli così: "
                "Goalkeeper=Portiere, Defender=Difensore, "
                "Midfielder=Centrocampista, Forward=Attaccante."
            ),
            "no_data": "Non ho trovato dati corrispondenti nel database.",
            "no_info": "Non ho questa informazione nel database.",
        }
    else:
        return {
            "lang_instruction": "Reply in English, formally and precisely.",
            "role_translations": (
                "Use original role names: "
                "Goalkeeper, Defender, Midfielder, Forward."
            ),
            "no_data": "No matching data found in the database.",
            "no_info": "I don't have this information in the database.",
        }


def _is_sql_query(query: str) -> bool:
    """Determina se la domanda richiede una query SQL."""
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in SQL_KEYWORDS)


def _build_sql_query(user_query: str) -> str | None:
    """
    Costruisce una query SQL a partire dalla domanda dell'utente
    usando pattern matching, senza passare per Llama3.
    Restituisce None se non riesce a costruire una query.
    """
    q = user_query.lower()

    # Trova la statistica richiesta
    stat_col = None
    for col, keywords in STAT_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            stat_col = col
            break

    if not stat_col:
        return None

    # Trova il club nella query
    team_filter = None
    for keyword, club_name in CLUBS.items():
        if keyword in q:
            team_filter = club_name
            break

    # Trova il ruolo nella query
    role_filter = None
    for keyword, role_name in ROLES.items():
        if keyword in q:
            role_filter = role_name
            break

    # Domanda comparativa
    is_comparative = any(kw in q for kw in [
        "più", "most", "migliore", "best", "top",
        "massimo", "maximum", "chi ha", "who has", "who scored"
    ])

    # Cerca nome proprio nella query
    player_name = None
    words = user_query.split()
    name_parts = []
    for word in words:
        clean = word.strip("?.,!")
        if (clean and clean[0].isupper()
                and clean.lower() not in IGNORE_WORDS
                and clean.lower() not in CLUBS
                and clean.lower() not in ROLES):
            name_parts.append(clean)
    if name_parts:
        player_name = " ".join(name_parts)

    # Costruisci la query SQL
    if player_name and not is_comparative:
        return f"""
            SELECT name, team, position, {stat_col}
            FROM players
            WHERE name ILIKE '%{player_name}%'
            AND {stat_col} IS NOT NULL
            AND {stat_col} > 0
            LIMIT 5
        """
    elif is_comparative and team_filter and role_filter:
        return f"""
            SELECT name, team, position, {stat_col}
            FROM players
            WHERE team = '{team_filter}'
            AND position = '{role_filter}'
            AND {stat_col} IS NOT NULL
            AND {stat_col} > 0
            ORDER BY {stat_col} DESC
            LIMIT 5
        """
    elif is_comparative and team_filter:
        return f"""
            SELECT name, team, position, {stat_col}
            FROM players
            WHERE team = '{team_filter}'
            AND {stat_col} IS NOT NULL
            AND {stat_col} > 0
            ORDER BY {stat_col} DESC
            LIMIT 5
        """
    elif is_comparative and role_filter:
        return f"""
            SELECT name, team, position, {stat_col}
            FROM players
            WHERE position = '{role_filter}'
            AND {stat_col} IS NOT NULL
            AND {stat_col} > 0
            ORDER BY {stat_col} DESC
            LIMIT 5
        """
    elif is_comparative:
        return f"""
            SELECT name, team, position, {stat_col}
            FROM players
            WHERE {stat_col} IS NOT NULL
            AND {stat_col} > 0
            ORDER BY {stat_col} DESC
            LIMIT 5
        """
    elif team_filter:
        return f"""
            SELECT name, team, {stat_col}
            FROM players
            WHERE team = '{team_filter}'
            AND {stat_col} IS NOT NULL
            AND {stat_col} > 0
            ORDER BY {stat_col} DESC
        """

    return None


class SmartRetriever(BaseRetriever):
    k: int = Field(default=20)

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        store = get_vectorstore()
        query_lower = query.lower()
        filter_dict = {}

        for keyword, club_name in CLUBS.items():
            if keyword in query_lower:
                filter_dict["team"] = club_name
                break

        for keyword, role_name in ROLES.items():
            if keyword in query_lower:
                filter_dict["position"] = role_name
                break

        if filter_dict:
            results = store.similarity_search_with_score(
                query, k=30, filter=filter_dict
            )
        else:
            results = store.similarity_search_with_score(query, k=self.k)

        return [doc for doc, _ in results]


@st.cache_resource
def get_llm():
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    return ChatOllama(model="llama3", base_url=ollama_url, temperature=0)


@st.cache_resource
def get_rag_chain():
    llm = get_llm()
    retriever = SmartRetriever(k=20)

    prompt = ChatPromptTemplate.from_template("""
Hai accesso SOLO a questo database di giocatori della Premier League.
Il database contiene informazioni su ruoli in inglese: Goalkeeper, Defender, Midfielder, Forward.
Rispondi nella stessa lingua della domanda — italiano se la domanda è in italiano, inglese se è in inglese.
Traduci i ruoli nella lingua della risposta:
  Goalkeeper=Portiere, Defender=Difensore, Midfielder=Centrocampista, Forward=Attaccante (in italiano)
  Goalkeeper, Defender, Midfielder, Forward (in inglese)
Rispondi SOLO usando i nomi e le informazioni presenti nel testo sotto.
Se la risposta non è nel testo, di' "Non ho questa informazione nel database" (italiano) o "I don't have this information in the database" (inglese).
NON usare mai la tua conoscenza generale sul calcio.
NON completare liste con nomi non presenti nel database.
NON scrivere frasi introduttive.
Quando ti chiedono giocatori per ruolo, includi SOLO i giocatori il cui ruolo corrisponde ESATTAMENTE a quello richiesto.
Vai direttamente alla risposta.

Contesto:
{context}

Storico conversazione:
{chat_history}

Domanda: {input}

Risposta:""")

    combine_docs_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, combine_docs_chain)


def get_chat_response(user_query: str, chat_history: list = None) -> str:
    history_text = ""
    if chat_history:
        for m in chat_history:
            role = "Utente" if m["role"] == "user" else "Assistente"
            history_text += f"{role}: {m['content']}\n"

    lang = _detect_language(user_query)
    lang_config = _get_language_config(lang)

    if _is_sql_query(user_query):
        try:
            sql_query = _build_sql_query(user_query)

            if sql_query:
                engine = create_engine(os.getenv("DATABASE_URL"))
                with engine.connect() as conn:
                    result = conn.execute(text(sql_query))
                    rows = result.fetchall()
                    columns = list(result.keys())

                if not rows:
                    return lang_config["no_data"]

                result_text = "\n".join(
                    [", ".join(f"{col}: {val}" for col, val in zip(columns, row))
                     for row in rows]
                )

                llm = get_llm()
                prompt = f"""Sei un analista calcistico.
{lang_config["lang_instruction"]}
{lang_config["role_translations"]}
NON inventare dati. Usa SOLO i dati forniti qui sotto.
Vai direttamente alla risposta senza frasi introduttive.

Domanda: {user_query}

Dati dal database:
{result_text}

Risposta:"""

                response = llm.invoke(prompt)
                return response.content

        except Exception as e:
            return f"Errore nella ricerca: {str(e)}"

    # Fallback al RAG per domande semantiche
    chain = get_rag_chain()
    response = chain.invoke({
        "input": user_query,
        "chat_history": history_text
    })
    return response["answer"]