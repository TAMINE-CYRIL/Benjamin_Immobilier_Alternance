import datetime as dt

from psycopg2.extras import Json

from database.connection import get_connection


def create_run(run_type="full", log_path=None):
    """
    Crée une nouvelle entrée dans la table automation_runs pour suivre l'exécution d'un processus d'automatisation.
    - run_type : type de processus (ex: "full", "dvf_import", "annonces_scraping", etc.)
    - log_path : chemin vers le fichier de log associé à ce run (optionnel)
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO automation_runs (run_type, status, log_path)
            VALUES (%s, 'running', %s)
            RETURNING id, started_at
            """,
            (run_type, log_path),
        )
        run_id, started_at = cur.fetchone()
        conn.commit()
        return {"id": run_id, "started_at": started_at}
    finally:
        cur.close()
        conn.close()


def finish_run(run_id, status, summary=None, error_message=None):
    """
    Met à jour l'entrée de la table automation_runs pour indiquer la fin d'un processus d'automatisation.
    - run_id : ID du run à mettre à jour
    - status : statut final du run ("success", "failure", etc.)
    - summary : résumé des résultats du run (optionnel, doit être JSON-serializable)
    - error_message : message d'erreur en cas d'échec (optionnel)
    """
    completed_at = dt.datetime.now()
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE automation_runs
            SET status = %s,
                completed_at = %s,
                duration_seconds = EXTRACT(EPOCH FROM (%s - started_at)),
                summary = %s,
                error_message = %s
            WHERE id = %s
            """,
            (status, completed_at, completed_at, Json(summary or {}), error_message, run_id),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def list_runs(limit=20):
    """
    Liste les runs d'automatisation.
    - limit : nombre maximum de runs à retourner (par défaut : 20, max : 100)
    """
    safe_limit = min(max(int(limit or 20), 1), 100)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, run_type, status, started_at, completed_at, duration_seconds,
                   log_path, summary, error_message
            FROM automation_runs
            ORDER BY started_at DESC
            LIMIT %s
            """,
            (safe_limit,),
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return [
        {
            "id": row[0],
            "run_type": row[1],
            "status": row[2],
            "started_at": row[3],
            "completed_at": row[4],
            "duration_seconds": row[5],
            "log_path": row[6],
            "summary": row[7] or {},
            "error_message": row[8],
        }
        for row in rows
    ]
