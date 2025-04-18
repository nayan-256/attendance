import sqlite3
import os

DATABASE_PATH = 'database.db'

def delete_user_record(student_id):
    try:
        print(f"🔍 Connecting to database: {DATABASE_PATH}")
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()

        # Fetch user info
        cur.execute("SELECT id, name, image_path FROM users WHERE student_id = ?", (student_id,))
        result = cur.fetchone()

        if not result:
            print(f"🚫 No user found with student ID: {student_id}")
            return

        user_id, name, image_path = result
        print(f"✅ Found user: {name} (ID: {user_id})")

        confirm = input(f"Are you sure you want to delete '{name}' (ID: {student_id}) and all their data? (yes/no): ").lower()
        if confirm != 'yes':
            print("❌ Deletion cancelled.")
            return

        # Delete attendance
        cur.execute("DELETE FROM attendance WHERE user_id = ?", (user_id,))
        print(f"🗑️ Deleted attendance for user_id {user_id}")

        # Delete user
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        print(f"🗑️ Deleted user with id {user_id}")

        # Delete image
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
            print(f"🗑️ Deleted image: {image_path}")
        else:
            print(f"⚠️ Image not found: {image_path}")

        conn.commit()
        print("✅ All records deleted successfully.")

    except sqlite3.Error as e:
        print(f"⚠️ SQLite error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    student_id = input("Enter the student ID of the user to delete: ").strip()
    delete_user_record(student_id)
