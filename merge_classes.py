import sqlite3
from collections import defaultdict
import re

DB_PATH = 'instance/academy.db'

def normalize_class_name(class_name):
    """Standardize class names."""
    if not class_name:
        return ''
    
    # Lowercase
    norm = class_name.lower().strip()
    
    # Common mappings
    mappings = {
        r'care.*giver': 'caregiver',
        r'food.*bever.*|hospitality': 'food and beverage',
        r'hair.*beauty|beauty.*hair': 'hair and beauty',
        r'electrical.*': 'electrical installation',
        r'plumb.*': 'plumbing',
        r'tailor.*': 'tailoring',
        r'[^a-z\s]': '',  # Remove non-alphanum except spaces
    }
    
    for pattern, replacement in mappings.items():
        norm = re.sub(pattern, replacement, norm, flags=re.IGNORECASE)
    
    # Title case
    norm = re.sub(r'\b\w', lambda m: m.group(0).upper(), norm)
    
    return norm

def get_duplicates():
    """Get class variants."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT LOWER(class_name) as norm, class_name, COUNT(*) 
        FROM student 
        WHERE active=1 AND class_name IS NOT NULL
        GROUP BY LOWER(class_name), class_name 
        HAVING COUNT(*) > 0
        ORDER BY COUNT(*) DESC, norm
    """)
    return cursor.fetchall()

def merge_sessions():
    """Merge session variants to '9'."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE student SET session='9' WHERE LOWER(session) LIKE '%season 9%' OR LOWER(session) LIKE '%session 9%' OR LOWER(session) = '9'")
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"Updated {updated} session records to '9'")
    return updated

def merge_classes():
    """Merge duplicate classes to normalized name."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    variants = defaultdict(list)
    cursor.execute("SELECT id, class_name FROM student WHERE active=1")
    for row in cursor.fetchall():
        student_id, class_name = row
        norm = normalize_class_name(class_name)
        variants[norm].append((student_id, class_name))
    
    updated = 0
    for norm, students in variants.items():
        if len(set(s[1] for s in students)) > 1:  # Has variants
            print(f"Merging {len(students)} students to '{norm}'")
            cursor.execute("UPDATE student SET class_name=? WHERE id=?", (norm, students[0][0]))
            for sid, _ in students[1:]:
                cursor.execute("UPDATE student SET class_name=? WHERE id=?", (norm, sid))
                updated += 1
            conn.commit()
    
    conn.close()
    print(f"Updated {updated} records")
    return updated

if __name__ == '__main__':
    print("Class variants:")
    print(get_duplicates())
    print("\nMerging classes...")
    merge_classes()
    print("Done. Restart app to see changes.")
