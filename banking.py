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
        # Check if username exists
        query = "SELECT user_id FROM users WHERE username = %s"
        if self.db.execute_query(query, (username,), fetch=True):
            print("Username already exists.")
            return False
        
        # Hash Password
        hashed_password = self._hash_password(password)

        # Generate Account Number
        account_number = self._generate_account_number()

        # Use a single connection
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                # Start transaction
                conn.autocommit = False

                # Insert User
                query = """
                INSERT INTO users (username, password, name, address, aadhaar, mobile, account_number, balance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (username, hashed_password, name, address, aadhaar, mobile, account_number, 1000.0)
                cursor.execute(query, params)
                user_id = cursor.lastrowid  # Get inserted ID directly

                if not user_id:
                    conn.rollback()
                    return False

                # Add a debit card
                query = """
                INSERT INTO cards (user_id, card_number, card_type, pin, cvv)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query, (user_id, self._generate_card_number(), 'Debit', self._generate_pin(), self._generate_cvv()))

                # Add a credit card
                cursor.execute(query, (user_id, self._generate_card_number(), 'Credit', self._generate_pin(), self._generate_cvv()))

                # Commit transaction
                conn.commit()
                return True
        
            except Exception as e:
                # Rollback
                conn.rollback()
                print(f"Error occurred: {e}")
                return False
            finally:
                cursor.close()
        
    def login(self, username, password) :
        """Authenticate user and return user_id if succesful."""

        hashed_password = self._hash_password(password)
        query = "SELECT user_id FROM users WHERE username = %s AND password = %s"
        result = self.db.execute_query(query, (username, hashed_password), fetch=True )
        return result[0]['user_id'] if result else None
    
    def get_account_info(self, user_id) :
        """Fetch account informations."""
        query = "SELECT name, address, aadhaar, mobile, balance FROM users WHERE user_id = %s"
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

    def add_beneficiaries(self, user_id, name, account_number):
        """Add a new benficiary."""
        from validation import validate_account_number
        if not validate_account_number(account_number) or not name.strip():
            return False
        query = "INSERT INTO beneficiaries (user_id, name, account_number) VALUES (%s, %s, %s)"
        return self.db.execute_query(query, (user_id, name, account_number)) > 0
    
    def update_account_info(self, user_id, name, address, mobile):
        """Update account information if provided."""
        updates = {}
        if name.strip():
            updates['name'] = name
        
        if address.strip():
            updates['address'] = address

        if mobile.strip():
            updates['mobile'] = address

        if not updates:
            return False
        
        query_parts = [f"{k} = %s" for k in updates]
        query = f"UPDATE users SET {', '.join(query_parts)} WHERE user_id = %s"
        params = list(updates.values()) + [user_id]
        return self.db.execute_query(query, params) > 0
    
    def transfer_funds(self, user_id, account_number, amount):
        """Transfer funds to a beneficary and record transation."""
        if amount <= 0:
            return False
        
        #Check Balance
        info = self.get_account_info(user_id)
        if info['balance'] < amount:
            return False
        
        #Verify beneficiary
        query = "SELECT id FROM beneficiaries WHERE user_id = %s AND account_number = %s"
        if not self.db.execute_query(query, (user_id, account_number), fetch = True):
            return False
        
        # Record transaction first
        query = """
        INSERT INTO transactions (user_id, amount, beneficiary_account, transaction_date)
        VALUES (%s, %s, %s, %s)
        """
        transaction_success = self.db.execute_query(query, (user_id, amount, account_number, datetime.now()))
        
        # If transaction was recorded successfully, update the balance
        if transaction_success:
            query = "UPDATE users SET balance = balance - %s WHERE user_id = %s"
            return self.db.execute_query(query, (amount, user_id)) > 0
    
        # If transaction failed, don't subtract the amount
        return False

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
    