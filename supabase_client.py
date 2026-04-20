import requests
import os

url = os.getenv('SUPABASE_URL', 'https://abmuzxugpqzbrwfewhri.supabase.co')
key = os.getenv('SUPABASE_KEY', '')

class SupabaseClient:
    """Simple Supabase REST API client"""
    
    def __init__(self, url, key):
        self.url = url
        self.key = key
        self.headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
    
    def table(self, table_name):
        return SupabaseTable(self.url, table_name, self.headers)

class SupabaseTable:
    """Supabase table operations"""
    
    def __init__(self, base_url, table_name, headers):
        self.base_url = base_url
        self.table_name = table_name
        self.headers = headers
        self.endpoint = f"{base_url}/rest/v1/{table_name}"
    
    def select(self, columns='*'):
        """Select data from table - returns self for chaining"""
        self.select_columns = columns
        self.operation = 'select'
        return self
    
    def insert(self, data):
        """Insert data into table"""
        response = requests.post(self.endpoint, headers=self.headers, json=data)
        if not response.ok:
            print(f"HTTP {response.status_code}: {response.text}")
        return SupabaseResponse(response.json() if response.content else [])
    
    def update(self, data):
        """Update data in table - must be chained with filter"""
        self.update_data = data
        self.operation = 'update'
        return self
    
    def delete(self):
        """Delete data in table - must be chained with filter"""
        self.delete_mode = True
        self.operation = 'delete'
        return self
    
    def eq(self, column, value):
        """Add equality filter"""
        if not hasattr(self, 'filters'):
            self.filters = []
        self.filters.append(f"{column}=eq.{value}")
        return self
    
    def execute(self):
        """Execute the query"""
        if hasattr(self, 'operation') and self.operation == 'delete':
            url = f"{self.endpoint}?{'&'.join(self.filters)}"
            response = requests.delete(url, headers=self.headers)
        elif hasattr(self, 'operation') and self.operation == 'update':
            url = f"{self.endpoint}?{'&'.join(self.filters)}"
            response = requests.patch(url, headers=self.headers, json=self.update_data)
        else:
            # Default to select
            columns = getattr(self, 'select_columns', '*')
            filters = getattr(self, 'filters', [])
            url = f"{self.endpoint}?select={columns}"
            if filters:
                url += f"&{'&'.join(filters)}"
            response = requests.get(url, headers=self.headers)
        return SupabaseResponse(response.json())

class SupabaseResponse:
    """Wrapper for Supabase API responses"""
    
    def __init__(self, data):
        self.data = data if isinstance(data, list) else [data] if data else []

supabase = SupabaseClient(url, key)
