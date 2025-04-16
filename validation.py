import re

def validate_registration(username, password, name, address, aadhaar, mobile):
    """Validate registration input data."""

    if not re.match(r"^[a-zA-Z0-9]{3,20}$", username) :
        print("Invalid username. It must be alphanumeric and between 3 to 20 characters.")
        return False
    
    if len(password) < 6:
        print("Password is too short. It must be at least 6 characters long.")
        return False
    
    if not name.strip():
        print("Name cannot be empty.")
        return False
    
    if not address.strip():
        print("Address cannot be empty.")
        return False
    
    if not re.match(r"^\d{12}$", aadhaar):
        print("Invalid Aadhaar. It must be a 12-digit number.")
        return False
    
    if not re.match(r"^\d{10}$", mobile):
        print("Invalid mobile number. It must be a 10-digit number.")
        return False
    return True

def validate_login(username, password):
    """Validate login credentials format."""

    if not re.match("^[a-zA-Z0-9]{3,20}$", username) :
        return False
    
    if len(password) < 6 :
        return False
    
    return True

def validate_pin(pin):
    """Validate card PIN (4 digits)."""

    return re.match(r"^\d{4}$", pin) is not None

def validate_account_number(account_number):
    """Validate account number (simplified: 10 digits)."""

    return re.match(r"^\d{10}$", account_number) is not None