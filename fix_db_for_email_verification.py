import sqlite3

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check if the columns already exist
cursor.execute("PRAGMA table_info(treeapp_userprofile)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

# Add the phone column if it doesn't exist
if 'phone' not in column_names:
    cursor.execute("ALTER TABLE treeapp_userprofile ADD COLUMN phone VARCHAR(20)")
    print("Column 'phone' added successfully")
else:
    print("Column 'phone' already exists")

# Add the email_verified column if it doesn't exist
if 'email_verified' not in column_names:
    cursor.execute("ALTER TABLE treeapp_userprofile ADD COLUMN email_verified BOOLEAN DEFAULT 0")
    print("Column 'email_verified' added successfully")
else:
    print("Column 'email_verified' already exists")

# Add the email_verification_token column if it doesn't exist
if 'email_verification_token' not in column_names:
    cursor.execute("ALTER TABLE treeapp_userprofile ADD COLUMN email_verification_token VARCHAR(100)")
    print("Column 'email_verification_token' added successfully")
else:
    print("Column 'email_verification_token' already exists")

# Update the django_migrations table to mark the migration as applied
cursor.execute(
    "INSERT OR IGNORE INTO django_migrations (app, name, applied) VALUES (?, ?, datetime('now'))",
    ('treeapp', '0019_userprofile_phone_userprofile_email_verified_userprofile_email_verification_token')
)
print("Migration record added")

# Commit and close
conn.commit()
conn.close()

print("\nAll columns have been added to the database. You can now proceed with your development.")