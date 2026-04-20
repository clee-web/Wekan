#!/usr/bin/env python3
"""Remove duplicate payments safely with dry-run option."""
import argparse
import sys
from datetime import date
from sqlalchemy import func, and_
from models import Payment, Student, db

def main():
    parser = argparse.ArgumentParser(description=\"Remove duplicate payments\")
    parser.add_argument('--dry-run', action='store_true', help=\"Show what would be deleted\")
    parser.add_argument('--execute', action='store_true', help=\"Actually delete duplicates\")
    parser.add_argument('--student', type=int, help=\"Remove duplicates for specific student ID\")
    args = parser.parse_args()
    
    if args.dry_run:
        print(\"=== DRY-RUN MODE ===\")
        removed = Payment.remove_duplicates(student_id=args.student, dry_run=True)
        print(f\"Would remove {removed} duplicates\")
    elif args.execute:
        print(\"=== LIVE MODE ===\")
        confirm = input(\"Confirm delete duplicates? (yes/no): \")
        if confirm.lower() == 'yes':
            removed = Payment.remove_duplicates(student_id=args.student, dry_run=False)
            print(f\"Removed {removed} duplicates\")
        else:
            print(\"Aborted.\")
    else:
        dups = Payment.find_duplicates(student_id=args.student)
        print(f\"Found {len(dups)} duplicate groups:\")
        for dup in dups:
            print(dup)

if __name__ == \"__main__\":  
    main()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=\"Remove duplicate payments\")
    parser.add_argument('--dry-run', action='store_true', help=\"Show what would be deleted\")
    parser.add_argument('--execute', action='store_true', help=\"Actually delete duplicates\")
    args = parser.parse_args()
    
    if args.dry_run:
        print(\"=== DRY-RUN MODE ===\")
        remove_duplicates(dry_run=True)
    elif args.execute:
        print(\"=== LIVE MODE - DELETING DUPLICATES ===\")
        confirm = input(\"Confirm deletion? (yes/no): \")
        if confirm.lower() == 'yes':
            remove_duplicates(dry_run=False)
        else:
            print(\"Aborted.\")
    else:
        print(find_duplicate_groups())

