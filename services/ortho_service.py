import sqlite3
from flask import current_app

def get_all_ortho_patients():
    db = sqlite3.connect(current_app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    patients = db.execute('SELECT * FROM ortho_patients ORDER BY created_at DESC').fetchall()
    db.close()
    return patients
