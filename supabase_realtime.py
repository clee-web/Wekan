"""
Supabase Real-time Subscriptions
Set up real-time listeners for database changes
"""
from supabase_client import supabase

class SupabaseRealtime:
    """Manage Supabase real-time subscriptions"""
    
    def __init__(self):
        self.subscriptions = {}
    
    def subscribe_to_table(self, table_name, callback, event_type='*'):
        """
        Subscribe to real-time changes on a table
        
        Args:
            table_name: Name of the table to subscribe to
            callback: Function to call when data changes
            event_type: Type of event to listen for ('INSERT', 'UPDATE', 'DELETE', or '*')
        
        Returns: subscription object
        """
        try:
            # Subscribe to table changes
            subscription = supabase.table(table_name).on_change(
                event_type,
                callback
            ).subscribe()
            
            self.subscriptions[table_name] = subscription
            return subscription
        except Exception as e:
            print(f"Error subscribing to {table_name}: {str(e)}")
            return None
    
    def subscribe_to_students(self, callback):
        """Subscribe to student changes"""
        return self.subscribe_to_table('students', callback)
    
    def subscribe_to_payments(self, callback):
        """Subscribe to payment changes"""
        return self.subscribe_to_table('payments', callback)
    
    def subscribe_to_teachers(self, callback):
        """Subscribe to teacher changes"""
        return self.subscribe_to_table('teachers', callback)
    
    def subscribe_to_attendance(self, callback):
        """Subscribe to attendance changes"""
        return self.subscribe_to_table('attendance', callback)
    
    def subscribe_to_exam_results(self, callback):
        """Subscribe to exam result changes"""
        return self.subscribe_to_table('exam_results', callback)
    
    def unsubscribe(self, table_name):
        """Unsubscribe from a table"""
        if table_name in self.subscriptions:
            try:
                self.subscriptions[table_name].unsubscribe()
                del self.subscriptions[table_name]
                return True
            except Exception as e:
                print(f"Error unsubscribing from {table_name}: {str(e)}")
                return False
        return False
    
    def unsubscribe_all(self):
        """Unsubscribe from all tables"""
        for table_name in list(self.subscriptions.keys()):
            self.unsubscribe(table_name)

# Example usage
def example_student_callback(payload):
    """Example callback for student changes"""
    print(f"Student data changed: {payload}")

def example_payment_callback(payload):
    """Example callback for payment changes"""
    print(f"Payment data changed: {payload}")

# Initialize realtime instance
realtime = SupabaseRealtime()

# Example: Subscribe to students
# realtime.subscribe_to_students(example_student_callback)
