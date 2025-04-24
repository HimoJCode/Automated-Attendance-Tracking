import sqlite3
import os

person_id_to_delete = 44
  # Replace this with the actual person_id

# Connect to your database
conn = sqlite3.connect("recognition.db")
cursor = conn.cursor()

try:
    # 🖼️ First, delete image files linked to this person
    cursor.execute("SELECT image_path FROM FaceImages WHERE person_id = ?", (person_id_to_delete,))
    image_paths = cursor.fetchall()
    for (img_path,) in image_paths:
        if img_path and os.path.exists(img_path):
            try:
                os.remove(img_path)
                print(f"🗑️ Deleted file: {img_path}")
            except Exception as e:
                print(f"⚠️ Could not delete {img_path}: {e}")

    # 🧼 Delete from all related tables
    cursor.execute("DELETE FROM FaceImages WHERE person_id = ?", (person_id_to_delete,))
    cursor.execute("DELETE FROM FaceEmbeddings WHERE person_id = ?", (person_id_to_delete,))
    cursor.execute("DELETE FROM StudentDetails WHERE person_id = ?", (person_id_to_delete,))
    cursor.execute("DELETE FROM StaffDetails WHERE person_id = ?", (person_id_to_delete,))
    cursor.execute("DELETE FROM AttendanceRecords WHERE person_id = ?", (person_id_to_delete,))
    cursor.execute("DELETE FROM Person WHERE person_id = ?", (person_id_to_delete,))

    print(f"✅ Deleted person with ID {person_id_to_delete} and all associated records.")

except sqlite3.Error as e:
    print(f"⚠️ SQLite Error: {e}")

conn.commit()
conn.close()
