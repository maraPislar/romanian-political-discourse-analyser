from fastapi import FastAPI
import sqlite3

app = FastAPI()

@app.get("/speeches")
def get_speeches():
    conn = sqlite3.connect("data/db.sqlite")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM speeches LIMIT 50;")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
