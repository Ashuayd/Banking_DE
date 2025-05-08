from database import Database
import random
import string
import hashlib
from datetime import datetime

class BankSystem:
    """Main Class to handle Banking Operations."""

    def __init__(self):
        """Initialize database connection."""
        self.db = Database()

    def _hash_password(self, password):
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_card_number(self):
        """Generate a 16 digit Card Number."""
        return ''.join(random.choices(string.digits, k=16))
    
    def _generate_cvv(self):
        """Generate a 3 digit CVV."""
        return ''.join(random.choices(string.digits, k=3))
    
    def _generate_pin(self):
        """Generate a 4 digit PIN."""
        return ''.join(random.choices(string.digits, k=4))
    
    def _generate_account_number(self):
        """Generate a 10 digit Account Number"""
        return ''.join(random.choices(string.digits, k=10))
    
    def register_user(self, username, password, name, address, aadhaar, mobile):
        """Register a new user with one credit and one debit card."""
        #Check if ussername exists

        query = "SELECT user_id FROM users WHERE username = %s"
        result = self.db.execute_query(query, (username,), fetch=True)
        print("Username check result:", result)
        if result:
            return False

        
        # Hash Password
        hashed_password = self._hash_password(password)

        # Generate Account Number
        account_number = self._generate_account_number()

        # Insert User
        query = """
        INSERT INTO users (username, password, name, address, aadhaar, mobile, account_number, balance)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        params = (username, hashed_password, name, address, aadhaar, mobile, account_number, 1000.0)
        user_id = self.db.execute_query(query,params)

        if not user_id:

            return False
        
        #Get user_id (MySQL return rowcount, so query again)

        query = "SELECT user_id FROM users WHERE username = %s"
        result = self.db.execute_query(query,(username,), fetch=True)
        user_id = result[0]['user_id']

        #Add a debit card

        query = """
        INSERT INTO cards (user_id, card_number, card_type, pin, cvv)
        VALUES (%s, %s, %s, %s, %s)
        """
        self.db.execute_query(query, (user_id, self._generate_card_number(), 'Debit', self._generate_pin(), self._generate_cvv()))

        #Add a credit card

        self.db.execute_query(query, (user_id, self._generate_card_number(), 'Credit', self._generate_pin(), self._generate_cvv()))

        return True
    
    def login(self, username, password) :
        """Authenticate user and return user_id if succesful."""

        hashed_password = self._hash_password(password)
        query = "SELECT user_id FROM users WHERE username = %s AND password = %s"
        result = self.db.execute_query(query, (username, hashed_password), fetch=True )
        return result[0]['user_id'] if result else None
    
    def check_balance(self, username):
        query = "SELECT balance FROM users WHERE username = %s"
        result = self.db.execute_query(query, (username,), fetch=True)
        if result:
            return result[0]["balance"]
        return None
    
    def deposit(self, user_id, amount, account_number):
        if amount <= 0:
            return False
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                conn.autocommit = False
                query = "UPDATE users SET balance = balance + %s WHERE user_id = %s"
                cursor.execute(query, (amount, user_id))
                if cursor.rowcount == 0:
                    conn.rollback()
                    return False
                query = """
                INSERT INTO transactions (user_id, type, amount, account_number)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query, (user_id, 'deposit', amount, account_number))
                conn.commit()
                return True
            except:
                conn.rollback()
                return False
            finally:
                cursor.close()

    def withdraw(self, user_id, amount, account_number):
        if amount <= 0:
            return False
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                conn.autocommit = False
                query = "SELECT balance FROM users WHERE user_id = %s"
                cursor.execute(query, (user_id,))
                balance = cursor.fetchone()
                if not balance or balance[0] < amount:
                    conn.rollback()
                    return False
                query = "UPDATE users SET balance = balance - %s WHERE user_id = %s"
                cursor.execute(query, (amount, user_id))
                query = """
                INSERT INTO transactions (user_id, type, amount, account_number)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query, (user_id, 'withdrawal', amount, account_number))
                conn.commit()
                return True
            except:
                conn.rollback()
                return False
            finally:
                cursor.close()

    def transfer_funds(self, user_id, account_number, amount):
        """Transfer funds to a beneficiary and record transaction."""
        from validation import validate_account_number
        from datetime import datetime
        if amount <= 0 or not validate_account_number(account_number):
            print("[DEBUG] Invalid amount or account number format")
            return False
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                conn.autocommit = False

                # Check sender's balance and account
                print(f"[DEBUG] Checking sender's balance for user_id: {user_id}...")
                query = "SELECT balance, account_number FROM users WHERE user_id = %s"
                cursor.execute(query, (user_id,))
                sender = cursor.fetchone()
                print(f"[DEBUG] Sender fetched: {sender}")
                if not sender or sender['balance'] < amount:
                    print(f"[DEBUG] Sender with user_id {user_id} not found or insufficient balance.")
                    conn.rollback()
                    return False
                print(f"[DEBUG] Sender balance: {sender['balance']}")
                sender_account_number = sender['account_number']

                # Verify beneficiary
                query = "SELECT id, account_number FROM beneficiaries WHERE user_id = %s AND account_number = %s"
                cursor.execute(query, (user_id, account_number))
                beneficiary = cursor.fetchone()
                print(f"[DEBUG] Beneficiary check result: {beneficiary}")
                if not beneficiary:
                    print("[DEBUG] Beneficiary not found for this user")
                    conn.rollback()
                    return False

                # Check if transferring to own account
                if account_number == sender_account_number:
                    print("[DEBUG] Cannot transfer to your own account")
                    conn.rollback()
                    return False

                # Check if recipient account is internal (exists in users)
                query = "SELECT user_id, account_number FROM users WHERE account_number = %s"
                cursor.execute(query, (account_number,))
                recipient = cursor.fetchone()
                print(f"[DEBUG] Recipient query executed with account_number: {account_number}")
                print(f"[DEBUG] Recipient fetched: {recipient}")

                print("[DEBUG] Updating sender balance...")
                # Update sender balance
                query = "UPDATE users SET balance = balance - %s WHERE user_id = %s"
                cursor.execute(query, (amount, user_id))

                # Update recipient balance if internal account
                if recipient:
                    print("[DEBUG] Internal account found, updating recipient balance...")
                    query = "UPDATE users SET balance = balance + %s WHERE user_id = %s"
                    cursor.execute(query, (amount, recipient['user_id']))
                else:
                    print("[DEBUG] External account, no recipient balance update in users table")

                # Record sender transaction
                print("[DEBUG] Recording sender transaction...")
                transaction_query = """
                INSERT INTO transactions (user_id, type, amount, related_account, transaction_date)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(transaction_query, (user_id, 'transfer', amount, account_number, datetime.now()))

                # Record recipient transaction if internal account
                if recipient:
                    print("[DEBUG] Recording recipient transaction...")
                    cursor.execute(transaction_query, (recipient['user_id'], 'deposit', amount, sender_account_number, datetime.now()))
                else:
                    print("[DEBUG] External account, no recipient transaction recorded")

                # Commit transaction
                conn.commit()
                return True
            except Exception as e:
                print(f"[ERROR] An error occurred: {e}")
                conn.rollback()
                return False
            finally:
                cursor.close()

    
    def get_account_info(self, user_id) :
        """Fetch account informations."""
        query = "SELECT username, name, address, aadhaar, mobile, balance FROM users WHERE user_id = %s"
        result = self.db.execute_query(query, (user_id,), fetch=True)
        return result[0] if result else {}
    
    def get_beneficiaries(self, user_id) :
        """Fetch list of beneficiaries"""
        query = "SELECT name, account_number FROM beneficiaries WHERE user_id = %s"
        return self.db.execute_query(query, (user_id,), fetch =True) or []

    def get_cards(self, user_id):
        """Fetch list of cards."""
        query = "SELECT card_number, card_type, pin, cvv FROM cards WHERE user_id = %s"
        return self.db.execute_query(query, (user_id,), fetch = True) or []

    # def add_beneficiaries(self, user_id, name, account_number):
    #     """Add a new benficiary."""
    #     from validation import validate_account_number
    #     if not validate_account_number(account_number) or not name.strip():
    #         return False
    #     query = "INSERT INTO beneficiaries (user_id, name, account_number) VALUES (%s, %s, %s)"
    #     return self.db.execute_query(query, (user_id, name, account_number)) > 0
    def add_beneficiaries(self, user_id, name, account_number):
        """Add a new beneficiary."""
        from validation import validate_account_number
        if not validate_account_number(account_number) or not name.strip():
            print("[DEBUG] Invalid account number format or empty name")
            return False
        
        # Get the account holder's account number
        query = "SELECT account_number FROM users WHERE user_id = %s"
        result = self.db.execute_query(query, (user_id,), fetch=True)
        if not result:
            print("[DEBUG] Account holder not found")
            return False
        holder_account_number = result[0]['account_number']
        
        # Check if account number is the holder's own account
        if account_number == holder_account_number:
            print("[DEBUG] Cannot add your own account as a beneficiary")
            return False
        
        # Check if beneficiary already exists for this user
        query = "SELECT id FROM beneficiaries WHERE user_id = %s AND account_number = %s"
        if self.db.execute_query(query, (user_id, account_number), fetch=True):
            print("[DEBUG] Beneficiary already exists")
            return False
        
        # Add beneficiary
        query = "INSERT INTO beneficiaries (user_id, name, account_number) VALUES (%s, %s, %s)"
        success = self.db.execute_query(query, (user_id, name, account_number)) > 0
        if success:
            print("[DEBUG] Beneficiary added successfully")
        return success
    

    def update_account_info(self, user_id, name, address, mobile):
        """Update account information if provided."""
        updates = {}
        if name.strip():
            updates['name'] = name
        
        if address.strip():
            updates['address'] = address

        if mobile.strip():
            updates['mobile'] = mobile

        if not updates:
            return False
        
        query_parts = [f"{k} = %s" for k in updates]
        query = f"UPDATE users SET {', '.join(query_parts)} WHERE user_id = %s"
        params = list(updates.values()) + [user_id]
        return self.db.execute_query(query, params) > 0
    
    
    def change_card_pin(self, user_id, card_number_last4, new_pin):
        """Update card PIN."""
        from validation import validate_pin
        if not validate_pin(new_pin):
            return False
        
        query = "SELECT card_number FROM cards WHERE user_id = %s AND card_number LIKE %s"
        result = self.db.execute_query(query, (user_id, f'%{card_number_last4}'), fetch = True)
        if not result:
            return False
        
        query = "Update cards SET pin = %s WHERE user_id = %s AND card_number = %s"
        return self.db.execute_query(query, (new_pin, user_id, result[0]['card_number'])) > 0
    
    def add_credit_card(self, user_id):
        """Add a new credit card."""

        query = """
        INSERT INTO cards (user_id, card_number, card_type, pin, cvv)
        VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.execute_query(query, (user_id, self._generate_card_number(), 'Credit', self._generate_pin(), self._generate_cvv())) > 0
    