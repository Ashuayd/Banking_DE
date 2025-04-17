from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, field_validator
from banking import BankSystem
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
bank = BankSystem()

#JWT COnfiguration
SECRET_KEY = "1234-1234-1234"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')


class User(BaseModel):
    username: str
    password: str
    name: str
    address: str
    aadhaar: str
    mobile: str

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v):
        if not v:
            raise ValueError("Password cannot be empty")
        return v

    @field_validator("aadhaar")
    @classmethod
    def validate_aadhaar(cls, v):
        if len(v) != 12 or not v.isdigit():
            raise ValueError("Aadhaar must be 12 digits")
        return v

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        if len(v) != 10 or not v.isdigit():
            raise ValueError("Mobile must be 10 digits")
        return v
    
class LoginRequest(BaseModel):
    username: str
    password: str

class Transaction(BaseModel):
    amount: float

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

class Transfer(BaseModel):
    beneficiary_account: str
    amount: float

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v
    
# Pydantic Models
class Beneficiary(BaseModel):
    name: str
    account_number: str

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, v):
        if len(v) != 10 or not v.isdigit():
            raise ValueError("Account number must be 10 digits")
        return v

class UpdateAccount(BaseModel):
    name: str = ""
    address: str = ""
    mobile: str = ""

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        if v and (len(v) != 10 or not v.isdigit()):
            raise ValueError("Mobile must be 10 digits or empty")
        return v

class ChangePin(BaseModel):
    card_number_last4: str
    new_pin: str

    @field_validator("card_number_last4")
    @classmethod
    def validate_card_number_last4(cls, v):
        if len(v) != 4 or not v.isdigit():
            raise ValueError("Last 4 digits of card number must be 4 digits")
        return v

    @field_validator("new_pin")
    @classmethod
    def validate_new_pin(cls, v):
        if len(v) != 4 or not v.isdigit():
            raise ValueError("PIN must be 4 digits")
        return v


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         print(f"Attempting to decode token: {token[:20]}...")
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: str = payload.get("sub")
#         print(f"Decoded payload: {payload}")
#         if user_id is None:
#             print("No user_id in payload")
#             raise credentials_exception
#         return int(user_id)
#     except (JWTError, ValueError) as e:
#         print(f"JWT Decode Error: {str(e)}")
#         raise credentials_exception
    
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return int(user_id)
    except JWTError:
        raise credentials_exception



@app.post("/register")
async def register_user(user: User):
    success = bank.register_user(
        user.username, user.password, user.name, user.address, user.aadhaar, user.mobile
        )
    if success:
        return {"status": "success", "message": "Registration successful! Please login"}
    return {"status": "failed", "message": "Registration failed. Username or Aadhaar may exist."}


# @app.post("/login")
# async def login_user(login: LoginRequest):
#     user_id = bank.login(login.username, login.password)
#     if user_id: 
#         access_token = create_access_token(data={"sub": str(user_id)})
#         return {"access_token": access_token, "token_type": "bearer"}
#     raise HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Incorrect username or password"
#     )

@app.post("/login")
async def login_user(login: LoginRequest):
    logger.info(f"Login attempt for username: {login.username}")
    try:
        user_id = bank.login(login.username, login.password)
        if user_id:
            access_token = create_access_token(data={"sub": str(user_id)})
            logger.info(f"Login successful for user_id: {user_id}")
            return {"access_token": access_token, "token_type": "bearer"}
        logger.warning(f"Login failed for username: {login.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )



@app.post("/deposit")
async def deposit(transaction: Transaction, user_id: int = Depends(get_current_user)):
    account_info = bank.get_account_info(user_id)
    if not account_info:
        raise HTTPException(status_code=404, detail="User not found")
    success = bank.deposit(user_id, transaction.amount, account_info['account_number'])
    if success:
        return {"status": "success", "message": f"Deposited {transaction.amount}"}
    return {"status": "failed", "message": "Deposit failed"}


@app.post("/withdraw")
async def withdraw(transaction: Transaction, user_id: int = Depends(get_current_user)):
    account_info = bank.get_account_info(user_id)
    if not account_info:
        raise HTTPException(status_code=404, detail="User not found")
    success = bank.withdraw(user_id, transaction.amount, account_info['account_number'])
    if success:
        return {"status": "success", "message": f"Withdrew {transaction.amount}"}
    return {"status": "failed", "message": "Withdrawal failed. Insufficient balance or invalid account"}


@app.post("/transfer")
async def transfer(transfer: Transfer, user_id: int = Depends(get_current_user)):
    success = bank.transfer_funds(user_id, transfer.beneficiary_account, transfer.amount)
    if success:
        return {"status": "success", "message": f"Transferred {transfer.amount} to {transfer.beneficiary_account}"}
    return {"status": "failed", "message": "Transfer failed. Check beneficiary or balance"}


@app.get("/balance")
async def get_balance(user_id: int = Depends(get_current_user)):
    try:
        account_info = bank.get_account_info(user_id)
        if not account_info:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "success", "username": account_info['username'], "balance": account_info['balance']}
    except Exception as e:
        print(f"Balance Error for user_id {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    

@app.get("/beneficiaries")
async def get_beneficiaries(user_id: int = Depends(get_current_user)):
    beneficiaries = bank.get_beneficiaries(user_id)
    return {"status": "success", "beneficiaries": beneficiaries}

@app.get("/cards")
async def get_cards(user_id: int = Depends(get_current_user)):
    cards = bank.get_cards(user_id)
    # Mask sensitive fields
    for card in cards:
        card['pin'] = "****"
        card['cvv'] = "***"
    return {"status": "success", "cards": cards}

@app.post("/beneficiaries")
async def add_beneficiary(beneficiary: Beneficiary, user_id: int = Depends(get_current_user)):
    success = bank.add_beneficiaries(user_id, beneficiary.name, beneficiary.account_number)
    if success:
        return {"status": "success", "message": f"Added beneficiary {beneficiary.name}"}
    return {"status": "failed", "message": "Failed to add beneficiary. Invalid account number or name."}

@app.put("/account")
async def update_account(update: UpdateAccount, user_id: int = Depends(get_current_user)):
    success = bank.update_account_info(user_id, update.name, update.address, update.mobile)
    if success:
        return {"status": "success", "message": "Account information updated"}
    return {"status": "failed", "message": "No valid fields provided to update"}

@app.post("/cards/change-pin")
async def change_card_pin(pin_change: ChangePin, user_id: int = Depends(get_current_user)):
    success = bank.change_card_pin(user_id, pin_change.card_number_last4, pin_change.new_pin)
    if success:
        return {"status": "success", "message": "Card PIN updated"}
    return {"status": "failed", "message": "Failed to update PIN. Invalid card or PIN."}

@app.post("/cards")
async def add_credit_card(user_id: int = Depends(get_current_user)):
    success = bank.add_credit_card(user_id)
    if success:
        return {"status": "success", "message": "Credit card added"}
    return {"status": "failed", "message": "Failed to add credit card"}    
    