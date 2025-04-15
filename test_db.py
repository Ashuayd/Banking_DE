from database import Database

db = Database()

# Insert a user
insert_query = """
INSERT INTO users (username, password, name, address, aadhaar, mobile, account_number, balance)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""
params = (
    "alice123",        # username: ≤ 20 chars, unique
    "securepass123",   # password: ≤ 64 chars
    "Alice Smith",     # name: ≤ 100 chars
    "123 Main St",     # address: ≤ 200 chars
    "123456789012",    # aadhaar: 12 chars
    "9876543210",      # mobile: 10 chars
    "ACC1234567",      # account_number: ≤ 10 chars, unique
    500.00             # balance: decimal
)
row_count = db.execute_query(insert_query, params=params)
print(f"Inserted {row_count} row(s)")

# Verify
select_query = "SELECT username, name, balance FROM users"
result = db.execute_query(select_query, fetch=True)
print("Users:", result)