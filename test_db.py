from banking import BankSystem

# Temporary test snippet to update balance
bank = BankSystem()
username = "helloworld"

query = "UPDATE users SET balance = %s WHERE username = %s"
params = (1323000.0, username)
result = bank.db.execute_query(query, params)

if result is not None:
    print(f"✅ Balance updated for {username}")
else:
    print("❌ Failed to update balance")