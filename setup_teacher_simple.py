import sqlite3

db_path = 'instance/academy.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Clear
cursor.execute("DELETE FROM teacher_login")
cursor.execute("DELETE FROM teacher")
conn.commit()

# Insert teacher using only existing columns
cursor.execute("""
INSERT INTO teacher (name, first_name, last_name, email, phone, class_name, subject, qualification)
VALUES ('John Sokwayo', 'John', 'Sokwayo', 'sokwayo@gmail.com', '0722123456', 'Form 1A', 'Mathematics', 'B.Ed')
""")
teacher_id = cursor.lastrowid

# Insert login
cursor.execute("""
INSERT INTO teacher_login (teacher_id, username, password_hash)
VALUES (?, 'sokwayo@gmail.com', 'scrypt:32768:8:1$GI5Srvcr23aE8sgr$8e37a9d43b0c938d4bad9e280201b059a49013d9cc82bf938b4fdfcb9007ef93db606136f80bbb5aca2ff2c81d516e288412802a2d84bb7f78c242c654aa9abab5')
""", (teacher_id,))
conn.commit()

print(f"Created Teacher ID {teacher_id}")
print("Login: sokwayo@gmail.com / okwayo123")
print("Bypass ORM column mismatch - ready!")
