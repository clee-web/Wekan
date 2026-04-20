import sqlite3

conn = sqlite3.connect('instance/academy.db')
cursor = conn.cursor()

# Get table info
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='payment'")
result = cursor.fetchone()
print("Table Schema:")
print(result[0] if result else "Table not found")

# Get column names
cursor.execute("PRAGMA table_info(payment)")
columns = cursor.fetchall()
print("\nColumns:")
for col in columns:
    print(f"{col[1]} ({col[2]})")

conn.close()
