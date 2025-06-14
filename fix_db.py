import sqlite3

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check if the column already exists
cursor.execute("PRAGMA table_info(treeapp_userprofile)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

# Add the column if it doesn't exist
if 'member_id_id' not in column_names:
    cursor.execute("ALTER TABLE treeapp_userprofile ADD COLUMN member_id_id INTEGER REFERENCES treeapp_familymember(id)")
    print("Column member_id_id added successfully")
else:
    print("Column member_id_id already exists")

# Commit and close
conn.commit()
conn.close()