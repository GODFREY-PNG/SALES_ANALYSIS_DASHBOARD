# test_connection.py
from sql_utils import get_engine, run_query
import os
from dotenv import load_dotenv

# Load your .env file
load_dotenv()

print("🔍 Testing connection to Neon PostgreSQL...")
print(f"Host: {os.getenv('DB_HOST')}")
print(f"Database: {os.getenv('DB_NAME')}")
print(f"User: {os.getenv('DB_USERNAME')}")
print(f"Port: {os.getenv('DB_PORT')}")
print(f"Password: {'*' * 8} (hidden)")

try:
    # Create engine and test connection
    engine = get_engine()
    
    # Simple query to verify
    result = run_query("SELECT version();", engine)
    print("\n✅ CONNECTION SUCCESSFUL!")
    print(f"PostgreSQL version: {result.iloc[0,0][:50]}...")
    
    # Check if tables exist
    tables = run_query("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """, engine)
    
    print(f"\n📊 Existing tables: {list(tables['table_name'])}")
    
except Exception as e:
    print(f"\n❌ CONNECTION FAILED: {e}")
    print("\nCheck your .env file values:")
    print("- Username correct? (neondb_owner)")
    print("- Password correct? (no spaces, exact match)")
    print("- Host correct? (from your connection string)")