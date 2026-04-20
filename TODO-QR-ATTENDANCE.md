# QR Attendance Register System

**Status: New Task**

## Requirements:
1. QR scan marks attendance for:
   - Saturday normal class
   - Sunday normal class  
   - Sunday leadership class
2. Track absences per class type
3. 3 leadership absences → auto-deactivate student
4. Scan shows inactive status (admin only reactivation)
5. Admin sees inactive students list

## Plan:
1. Add `Attendance` model: student_id, date, class_type (normal/leadership), status
2. `/scan` endpoint: Scan QR → mark attendance + check/reactivate logic
3. Admin dashboard: View attendance + reactivate students
4. Update QR data to include session

**Progress:**
- [✅] models.py updated (session_type, qr_token, teacher_id nullable)
- [✅] routes/qr_routes.py fixed (teacher_id=None for QR)
- [✅] DB schema synced (teacher_id nullable)
- [✅] IntegrityError fixed

**Next:** Run `python app.py` to test QR attendance.
