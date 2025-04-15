import getpass
from banking import BankSystem
from validation import validate_login, validate_registration

def display_menu():
    """Display the main menu options."""
    print("\n=== Bash Menu ===")
    print("1. Register")
    print("2. Login")
    print("3. Exit")
    return input("Enter choice (1-3): ")

def display_user_menu():
    """Display user option after login."""
    print("\n=== User Menu ===")
    print("1. Display Account Info")
    print("2. List Beneficiaries")
    print("3. List Cards")
    print("4. Add Beneficiary")
    print("5. Update Account Info")
    print("6. Transfer Funds")
    print("7. Change Card MPIN")
    print("8. Register New Credit Card")
    print("9. Logout")
    return input("Enter choice (1-9): ")

def main():
    """Main function to run the banking system."""
    bank = BankSystem()

    while True:
        choice = display_menu()

        if choice == "1" :
            #Registration
            print("\n--- Registration ---")
            username = input("Username: ")
            password = getpass.getpass("Password: ")
            name = input("Full Name: ")
            address = input("Address: ")
            aadhaar = input("Aadhaaar Number: ")
            mobile = input("Mobile Number: ")

            if validate_registration(username, password, name, address, aadhaar, mobile):
                success = bank.register_user(username, password, name, address, aadhaar, mobile)
                if success:
                    print("Registration successfull! Please login")
                else:
                    print("Registration failed. Username may exist.")
            else: 
                print("Invalid input. Check Aadhar (12 digits), mobile (10 digits).")

        elif choice == "2":
            # Login
            print("\n--- Login ---")
            username = input("Username: ")
            password = getpass.getpass("Password: ")
            
            if validate_login(username, password):
                user_id = bank.login(username, password)
                if user_id:
                    print("Login successful!")
                    while True:
                        user_choice = display_user_menu()
                        
                        if user_choice == "1":
                            # Display account info
                            info = bank.get_account_info(user_id)
                            print("\nAccount Info:")
                            print(f"Name: {info['name']}")
                            print(f"Address: {info['address']}")
                            print(f"Aadhar: {info['aadhar']}")
                            print(f"Mobile: {info['mobile']}")
                            print(f"Balance: ${info['balance']:.2f}")
                        
                        elif user_choice == "2":
                            # List beneficiaries
                            beneficiaries = bank.get_beneficiaries(user_id)
                            print("\nBeneficiaries:")
                            for b in beneficiaries:
                                print(f"- {b['name']} (Account: {b['account_number']})")
                        
                        elif user_choice == "3":
                            # List cards
                            cards = bank.get_cards(user_id)
                            print("\nCards:")
                            for c in cards:
                                print(f"- {c['card_type']} Card (****{c['card_number'][-4:]}), PIN: {c['pin']}, CVV: {c['cvv']}")
                        
                        elif user_choice == "4":
                            # Add beneficiary
                            name = input("Beneficiary Name: ")
                            account_number = input("Beneficiary Account Number: ")
                            if bank.add_beneficiary(user_id, name, account_number):
                                print("Beneficiary added!")
                                print("\nUpdated Beneficiaries:")
                                for b in bank.get_beneficiaries(user_id):
                                    print(f"- {b['name']} (Account: {b['account_number']})")
                            else:
                                print("Failed to add beneficiary.")
                        
                        elif user_choice == "5":
                            # Update account info
                            name = input("New Name (leave blank to keep current): ")
                            address = input("New Address (leave blank to keep current): ")
                            mobile = input("New Mobile (leave blank to keep current): ")
                            if bank.update_account_info(user_id, name, address, mobile):
                                info = bank.get_account_info(user_id)
                                print("\nUpdated Account Info:")
                                print(f"Name: {info['name']}")
                                print(f"Address: {info['address']}")
                                print(f"Mobile: {info['mobile']}")
                            else:
                                print("Update failed.")
                        
                        elif user_choice == "6":
                            # Transfer funds
                            account_number = input("Beneficiary Account Number: ")
                            amount = input("Amount to Transfer: ")
                            try:
                                amount = float(amount)
                                if bank.transfer_funds(user_id, account_number, amount):
                                    print("Transfer successful!")
                                    info = bank.get_account_info(user_id)
                                    print(f"New Balance: ${info['balance']:.2f}")
                                else:
                                    print("Transfer failed. Check account number or balance.")
                            except ValueError:
                                print("Invalid amount.")
                        
                        elif user_choice == "7":
                            # Change card MPIN
                            card_number = input("Card Number (last 4 digits): ")
                            new_pin = input("New PIN (4 digits): ")
                            if bank.change_card_pin(user_id, card_number, new_pin):
                                print("PIN updated!")
                                print("\nUpdated Cards:")
                                for c in bank.get_cards(user_id):
                                    print(f"- {c['card_type']} Card (****{c['card_number'][-4:]}), PIN: {c['pin']}")
                            else:
                                print("Failed to update PIN.")
                        
                        elif user_choice == "8":
                            # Register new credit card
                            if bank.add_credit_card(user_id):
                                print("New credit card added!")
                                print("\nUpdated Cards:")
                                for c in bank.get_cards(user_id):
                                    print(f"- {c['card_type']} Card (****{c['card_number'][-4:]}), PIN: {c['pin']}")
                            else:
                                print("Failed to add card.")
                        
                        elif user_choice == "9":
                            # Logout
                            print("Logged out.")
                            break
                        
                        else:
                            print("Invalid choice.")
                else:
                    print("Login failed. Check credentials.")
            else:
                print("Invalid username or password format.")
        
        elif choice == "3":
            print("Thank you for using BashBank!")
            break
        
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()        
