import os
import pandas as pd
from sqlalchemy import create_engine, text
from langchain_core.documents import Document

CSV_PATH = "/app/data/dataset_-_2020-09-24.csv"
CONNECTION_STRING = os.getenv("DATABASE_URL")

def _safe_get(row, col, default=0):
    """Legge un valore da una riga, gestendo colonne mancanti e NaN."""
    try:
        val = row.get(col, default)
        return default if pd.isna(val) else val
    except Exception:
        return default

def _build_player_text(row) -> str:
    """Trasforma le statistiche in un testo descrittivo ricco per l'embedding."""
    name = _safe_get(row, "Name", "N/D")
    club = _safe_get(row, "Club", "N/D")
    position = _safe_get(row, "Position", "N/D")
    nationality = _safe_get(row, "Nationality", "N/D")
    age = _safe_get(row, "Age", "N/D")

    lines = [
        f"Il calciatore è {name}. Club: {club}. Ruolo: {position}. Nazionalità: {nationality}. Età: {age} anni.",
        f"{name} è un {position} del {club} in Premier League.",
    ]

    appearances = _safe_get(row, "Appearances")
    wins = _safe_get(row, "Wins")
    losses = _safe_get(row, "Losses")
    if appearances:
        lines.append(
            f"Ha disputato {appearances} presenze con il {club}, con {wins} vittorie e {losses} sconfitte."
        )

    goals = _safe_get(row, "Goals")
    assists = _safe_get(row, "Assists")
    shots = _safe_get(row, "Shots")
    shots_on_target = _safe_get(row, "Shots on target")
    headed_goals = _safe_get(row, "Headed goals")
    right_foot = _safe_get(row, "Goals with right foot")
    left_foot = _safe_get(row, "Goals with left foot")
    big_chances_missed = _safe_get(row, "Big chances missed")

    if goals or assists:
        lines.append(f"Ha segnato {goals} gol e fornito {assists} assist.")
    if shots:
        lines.append(f"Ha effettuato {shots} tiri, di cui {shots_on_target} nello specchio.")
    if headed_goals or right_foot or left_foot:
        lines.append(f"Gol di testa: {headed_goals}, con il destro: {right_foot}, con il sinistro: {left_foot}.")
    if big_chances_missed:
        lines.append(f"Grandi occasioni mancate: {big_chances_missed}.")

    tackles = _safe_get(row, "Tackles")
    tackle_success = _safe_get(row, "Tackle success %")
    interceptions = _safe_get(row, "Interceptions")
    clearances = _safe_get(row, "Clearances")
    recoveries = _safe_get(row, "Recoveries")
    duels_won = _safe_get(row, "Duels won")
    duels_lost = _safe_get(row, "Duels lost")
    aerial_won = _safe_get(row, "Aerial battles won")
    aerial_lost = _safe_get(row, "Aerial battles lost")

    if tackles:
        lines.append(f"Tackle effettuati: {tackles} (successo: {tackle_success}%), intercetti: {interceptions}, respinte: {clearances}.")
    if recoveries:
        lines.append(f"Recuperi palla: {recoveries}.")
    if duels_won or duels_lost:
        lines.append(f"Duelli vinti: {duels_won}, duelli persi: {duels_lost}.")
    if aerial_won or aerial_lost:
        lines.append(f"Contrasti aerei vinti: {aerial_won}, persi: {aerial_lost}.")

    passes = _safe_get(row, "Passes")
    passes_per_match = _safe_get(row, "Passes per match")
    big_chances_created = _safe_get(row, "Big chances created")
    crosses = _safe_get(row, "Crosses")
    cross_accuracy = _safe_get(row, "Cross accuracy %")
    through_balls = _safe_get(row, "Through balls")
    long_balls = _safe_get(row, "Accurate long balls")

    if passes:
        lines.append(f"Passaggi totali: {passes} ({passes_per_match} per partita).")
    if big_chances_created:
        lines.append(f"Grandi occasioni create: {big_chances_created}.")
    if crosses:
        lines.append(f"Cross: {crosses} (precisione: {cross_accuracy}%).")
    if through_balls:
        lines.append(f"Filtranti: {through_balls}.")
    if long_balls:
        lines.append(f"Lanci lunghi precisi: {long_balls}.")

    saves = _safe_get(row, "Saves")
    penalties_saved = _safe_get(row, "Penalties saved")
    clean_sheets = _safe_get(row, "Clean sheets")
    goals_conceded = _safe_get(row, "Goals conceded")
    punches = _safe_get(row, "Punches")
    high_claims = _safe_get(row, "High Claims")

    if saves:
        lines.append(
            f"{name} è il portiere del {club}: {saves} parate, {penalties_saved} rigori parati, "
            f"{clean_sheets} clean sheet, {goals_conceded} gol subiti."
        )
    if punches:
        lines.append(f"Pugni: {punches}, prese alte: {high_claims}.")

    yellow = _safe_get(row, "Yellow cards")
    red = _safe_get(row, "Red cards")
    fouls = _safe_get(row, "Fouls")
    offsides = _safe_get(row, "Offsides")

    if yellow or red or fouls:
        lines.append(f"Disciplina: {yellow} ammonizioni, {red} espulsioni, {fouls} falli commessi.")
    if offsides:
        lines.append(f"Fuorigioco: {offsides}.")

    return " ".join(lines)


def _create_sql_table(df: pd.DataFrame):
    """Crea la tabella SQL players in PostgreSQL."""
    engine = create_engine(CONNECTION_STRING)

    # Rinomina le colonne per SQL
    sql_df = df.rename(columns={
        "Name": "name",
        "Club": "team",
        "Position": "position",
        "Nationality": "nationality",
        "Age": "age",
        "Appearances": "appearances",
        "Wins": "wins",
        "Losses": "losses",
        "Goals": "goals",
        "Goals per match": "goals_per_match",
        "Headed goals": "headed_goals",
        "Goals with right foot": "goals_right_foot",
        "Goals with left foot": "goals_left_foot",
        "Penalties scored": "penalties_scored",
        "Freekicks scored": "freekicks_scored",
        "Shots": "shots",
        "Shots on target": "shots_on_target",
        "Shooting accuracy %": "shooting_accuracy",
        "Hit woodwork": "hit_woodwork",
        "Big chances missed": "big_chances_missed",
        "Clean sheets": "clean_sheets",
        "Goals conceded": "goals_conceded",
        "Tackles": "tackles",
        "Tackle success %": "tackle_success",
        "Last man tackles": "last_man_tackles",
        "Blocked shots": "blocked_shots",
        "Interceptions": "interceptions",
        "Clearances": "clearances",
        "Headed Clearance": "headed_clearances",
        "Clearances off line": "clearances_off_line",
        "Recoveries": "recoveries",
        "Duels won": "duels_won",
        "Duels lost": "duels_lost",
        "Successful 50/50s": "successful_50_50s",
        "Aerial battles won": "aerial_won",
        "Aerial battles lost": "aerial_lost",
        "Own goals": "own_goals",
        "Errors leading to goal": "errors_leading_to_goal",
        "Assists": "assists",
        "Passes": "passes",
        "Passes per match": "passes_per_match",
        "Big chances created": "big_chances_created",
        "Crosses": "crosses",
        "Cross accuracy %": "cross_accuracy",
        "Through balls": "through_balls",
        "Accurate long balls": "accurate_long_balls",
        "Saves": "saves",
        "Penalties saved": "penalties_saved",
        "Punches": "punches",
        "High Claims": "high_claims",
        "Catches": "catches",
        "Sweeper clearances": "sweeper_clearances",
        "Throw outs": "throw_outs",
        "Goal Kicks": "goal_kicks",
        "Yellow cards": "yellow_cards",
        "Red cards": "red_cards",
        "Fouls": "fouls",
        "Offsides": "offsides",
    })

    # Rimuovi colonna Jersey Number
    sql_df = sql_df.drop(columns=["Jersey Number"], errors="ignore")

    # Scrivi la tabella in PostgreSQL
    sql_df.to_sql("players", engine, if_exists="replace", index=False)


def fetch_kaggle_data(progress_callback=None) -> list[Document]:
    """
    Legge il dataset CSV di Kaggle (Premier League) e restituisce
    una lista di Document pronti per il vectorstore.
    Crea anche la tabella SQL players in PostgreSQL.
    """
    total_steps = 3

    if progress_callback:
        progress_callback(1, total_steps, "Caricando il dataset...")
    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        raise RuntimeError(
            f"File CSV non trovato in {CSV_PATH}. "
            "Assicurati di aver copiato il file in data/dataset_-_2020-09-24.csv"
        )

    if progress_callback:
        progress_callback(2, total_steps, "Creando tabella SQL...")
    _create_sql_table(df)

    if progress_callback:
        progress_callback(3, total_steps, f"Costruendo profili per {len(df)} giocatori...")

    docs = []
    for _, row in df.iterrows():
        try:
            text = _build_player_text(row)
            metadata = {
                "player": str(_safe_get(row, "Name", "N/D")),
                "team": str(_safe_get(row, "Club", "N/D")),
                "league": "Premier League",
                "position": str(_safe_get(row, "Position", "N/D")),
                "nationality": str(_safe_get(row, "Nationality", "N/D")),
                "goals": int(_safe_get(row, "Goals")),
                "assists": int(_safe_get(row, "Assists")),
                "appearances": int(_safe_get(row, "Appearances")),
            }
            docs.append(Document(page_content=text, metadata=metadata))
        except Exception:
            continue

    if progress_callback:
        progress_callback(total_steps, total_steps, "Completato!")

    return docs