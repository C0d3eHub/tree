import sqlite3

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check if the column already exists
cursor.execute("PRAGMA table_info(treeapp_userprofile)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

# Add the column if it doesn't exist
if 'name' not in column_names:
    cursor.execute("ALTER TABLE treeapp_userprofile ADD COLUMN name VARCHAR(100)")
    print("Column name added successfully")
else:
    print("Column name already exists")

# Commit and close
conn.commit()
conn.close()