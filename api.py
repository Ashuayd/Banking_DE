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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError as e:
        print("JWT Decode Error:", e)
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
    if bank.login(login.username, login.password):
        access_token = create_access_token(data={"sub": login.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password"
    )

@app.get("/balance/{username}")
async def get_balance(username: str, current_user: str = Depends(get_current_user)):
    if current_user != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's balance"
        )
    balance = bank.check_balance(username)
    if balance is not None:
        return {"status": "success", "username": username, "balance": balance}
    return {"status": "failed", "message": "User not found"}
