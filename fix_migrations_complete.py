import sqlite3

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check if the columns already exist
cursor.execute("PRAGMA table_info(treeapp_userprofile)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

# Add the name column if it doesn't exist
if 'name' not in column_names:
    cursor.execute("ALTER TABLE treeapp_userprofile ADD COLUMN name VARCHAR(100)")
    print("Column 'name' added successfully")
else:
    print("Column 'name' already exists")

# Add the plain_password column if it doesn't exist
if 'plain_password' not in column_names:
    cursor.execute("ALTER TABLE treeapp_userprofile ADD COLUMN plain_password VARCHAR(100)")
    print("Column 'plain_password' added successfully")
else:
    print("Column 'plain_password' already exists")

# Update the django_migrations table to mark all migrations as applied
migrations_to_add = [
    ('treeapp', '0017_userprofile_name'),
    ('treeapp', '0017_userprofile_name_userprofile_plain_password'),
    ('treeapp', '0018_merge_20250605_1450')
]

for app, name in migrations_to_add:
    cursor.execute(
        "INSERT OR IGNORE INTO django_migrations (app, name, applied) VALUES (?, ?, datetime('now'))",
        (app, name)
    )
    print(f"Migration record added: {app}.{name}")

# Commit and close
conn.commit()
conn.close()

print("\nAll migrations have been marked as applied. You can now proceed with your development.")