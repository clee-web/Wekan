"""Add admission_number to Student

Revision ID: add_admission_number
Revises: 
Create Date: 2025-10-27 10:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_admission_number'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add admission_number column without UNIQUE constraint first
    op.add_column('student', sa.Column('admission_number', sa.String(length=20), nullable=True))
    
    # Create a connection to execute raw SQL
    conn = op.get_bind()
    
    # Generate admission numbers for existing students
    result = conn.execute("SELECT id FROM student ORDER BY id")
    students = result.fetchall()
    
    for i, (student_id,) in enumerate(students, 1):
        admission_number = f'ADM-{i:04d}'
        conn.execute(
            "UPDATE student SET admission_number = ? WHERE id = ?",
            (admission_number, student_id)
        )
    
    # Now add the UNIQUE constraint
    op.create_unique_constraint('uq_student_admission_number', 'student', ['admission_number'])
    # Make the column NOT NULL after populating all rows
    op.alter_column('student', 'admission_number', nullable=False)

def downgrade():
    # Drop the UNIQUE constraint first
    op.drop_constraint('uq_student_admission_number', 'student', type_='unique')
    # Then drop the column
    op.drop_column('student', 'admission_number')
