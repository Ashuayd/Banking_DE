from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, field_validator
from banking import BankSystem
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

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


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print(f"Attempting to decode token: {token[:20]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        print(f"Decoded payload: {payload}")
        if user_id is None:
            print("No user_id in payload")
            raise credentials_exception
        return int(user_id)
    except (JWTError, ValueError) as e:
        print(f"JWT Decode Error: {str(e)}")
        raise credentials_exception


@app.post("/register")
async def register_user(user: User):
    success = bank.register_user(
        user.username, user.password, user.name, user.address, user.aadhaar, user.mobile
        )
    if success:
        return {"status": "success", "message": "Registration successful! Please login"}
    return {"status": "failed", "message": "Registration failed. Username or Aadhaar may exist."}


@app.post("/login")
async def login_user(login: LoginRequest):
    user_id = bank.login(login.username, login.password)
    if user_id: 
        access_token = create_access_token(data={"sub": str(user_id)})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password"
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