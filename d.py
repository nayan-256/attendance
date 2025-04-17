import sqlite3

DATABASE_PATH = 'database.db'

# Function to delete a specific user's record from users and attendance tables
def delete_user_record(name):
    try:
        # Connect to the database
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()

        # Delete user's attendance records
        cur.execute("DELETE FROM attendance WHERE user_id = (SELECT id FROM users WHERE name = ?)", (name,))
        
        # Delete the user record
        cur.execute("DELETE FROM users WHERE name = ?", (name,))
        
        # Commit the changes
        conn.commit()
        print(f"Record for user {name} deleted successfully!")
    except sqlite3.Error as e:
        print(f"Error while deleting record for {name}: {e}")
    finally:
        conn.close()

# Call the function to delete a specific user's record
if __name__ == '__main__':
    user_name = input("Enter the name of the user to delete: ")
    delete_user_record(user_name)
