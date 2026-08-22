import sqlite3
from datetime import datetime

def get_connection():
    return sqlite3.connect("filedata.db")


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            local_folder_name TEXT NOT NULL,
            is_ingested INTEGER CHECK (is_ingested   IN (0, 1)),
            created_on TEXT,
            updated_on TEXT
        )
    """)

    conn.commit()
    conn.close()


def insert_file_meta(file_name:str, file_type:str, local_folder_name:str, is_ingested: int,created_on:str,updated_on:str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO file_meta (file_name, file_type,local_folder_name, is_ingested,created_on,updated_on)
        VALUES (?, ?, ?, ?, ?, ?)
        RETURNING id
    """, (file_name, file_type, local_folder_name, is_ingested,created_on,updated_on))
    new_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return new_id


def get_file_meta_list():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM file_meta")
    rows = cursor.fetchall()

    conn.close()
    return rows


def get_file_by_id(file_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM file_meta WHERE id = ?",
        (file_id,)
    )

    file = cursor.fetchone()

    conn.close()
    return file


def update_status(file_id, is_ingested):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now() # Current datetime
    cursor.execute("""
        UPDATE file_meta
        SET is_ingested = ?, updated_on = ?
        WHERE id = ?
    """, (is_ingested, now.strftime("%Y-%m-%d %H:%M:%S"), file_id))

    conn.commit()
    conn.close()


def delete_file_meta(file_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM file_meta WHERE id = ?",
        (file_id,)
    )

    conn.commit()
    conn.close()


def drop_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS file_meta")

    conn.commit()
    conn.close()


if __name__ == "__main__":

    create_table()
    insert_file_meta("Pranav", "text","Test_Folder" ,0,datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"")


    print("All Files:")
    print(get_file_meta_list())

    print("\n File ID 1:")
    print(get_file_by_id(1))

    #update_employee(1, "Pranav Pandey", "AI Architect", 120000)

    #print("\nAfter Update:")
    #print(get_employee_by_id(1))

    #delete_employee(2)

    #print("\nAfter Delete:")
    #print(get_all_employees())