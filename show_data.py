import sqlite3
from PyQt5.QtWidgets import QTableWidgetItem

def show_all_tables(self):
    conn = sqlite3.connect("recognition.db")
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    for table_name in tables:
        table = table_name[0]
        print(f"\n--- {table} ---")
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        headers = [desc[0] for desc in cursor.description]

        print(" | ".join(headers))
        for row in rows:
            print(" | ".join(str(cell) for cell in row))

    conn.close()
