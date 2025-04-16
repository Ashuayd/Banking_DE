# Banking_DE

# Bash Bank

A Python-based banking system with registration, login, and account management features, using MySQL for data storage.

## Features
- **Registration**: Create an account with name, address, Aadhar, mobile; get one debit and one credit card.
- **Login**: Access account with username and password.
- **User Options**:
  - View account info and balance.
  - List beneficiaries and cards.
  - Add beneficiary.
  - Update account info.
  - Transfer funds (records transaction).
  - Change card MPIN.
  - Add new credit card.
- Integer-based menu for user interaction.

## Prerequisites
- Python 3.6+
- MySQL Server
- Required Python packages:
  ```bash
  pip install mysql-connector-python fastapi uvicorn pydantic

  python jose

