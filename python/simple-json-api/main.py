import os
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from oidc_config import OIDCProvider, oidc_config

app = FastAPI(title="Simple JSON API", version="1.0.0")

# Auth configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OIDC Configuration
OIDC_ENABLED = os.getenv("OIDC_ENABLED", "false").lower() == "true"


# Initialize OIDC providers from environment
def init_oidc_providers():
    if not OIDC_ENABLED:
        return

    # Google OIDC example
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    if google_client_id:
        google_provider = OIDCProvider(
            name="google",
            issuer="https://accounts.google.com",
            client_id=google_client_id,
            algorithms=["RS256"],
        )
        oidc_config.add_provider(google_provider)

    # Auth0 example
    auth0_domain = os.getenv("AUTH0_DOMAIN")
    auth0_client_id = os.getenv("AUTH0_CLIENT_ID")
    if auth0_domain and auth0_client_id:
        auth0_provider = OIDCProvider(
            name="auth0",
            issuer=f"https://{auth0_domain}/",
            client_id=auth0_client_id,
            algorithms=["RS256"],
        )
        oidc_config.add_provider(auth0_provider)

    # Generic OIDC provider
    oidc_issuer = os.getenv("OIDC_ISSUER")
    oidc_client_id = os.getenv("OIDC_CLIENT_ID")
    if oidc_issuer and oidc_client_id:
        generic_provider = OIDCProvider(
            name="generic",
            issuer=oidc_issuer,
            client_id=oidc_client_id,
            algorithms=["RS256", "HS256"],
        )
        oidc_config.add_provider(generic_provider)


init_oidc_providers()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: int
    username: str
    email: str
    oidc_subject: str | None = None
    oidc_provider: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class ItemCreate(BaseModel):
    name: str
    description: str | None = None
    price: float


class Item(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float
    owner_id: int


users_db = []
items_db = []
next_user_id = 1
next_id = 1


# Auth helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_username(username: str):
    for user in users_db:
        if user.username == username:
            return user
    return None


def get_user_by_oidc_subject(subject: str, provider: str):
    for user in users_db:
        if hasattr(user, "oidc_subject") and hasattr(user, "oidc_provider"):
            if user.oidc_subject == subject and user.oidc_provider == provider:
                return user
    return None


def create_oidc_user(oidc_payload: dict, provider_name: str):
    global next_user_id

    # Extract user info from OIDC claims
    subject = oidc_payload.get("sub")
    email = oidc_payload.get("email", f"{subject}@{provider_name}")
    name = oidc_payload.get("name") or oidc_payload.get("preferred_username") or subject

    user = type(
        "User",
        (),
        {
            "id": next_user_id,
            "username": name,
            "email": email,
            "oidc_subject": subject,
            "oidc_provider": provider_name,
            "password_hash": None,  # OIDC users don't have local passwords
        },
    )()

    next_user_id += 1
    users_db.append(user)
    return user


def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    # First try OIDC validation if enabled
    if OIDC_ENABLED:
        oidc_payload = oidc_config.validate_token(token)
        if oidc_payload:
            subject = oidc_payload.get("sub")
            issuer = oidc_payload.get("iss")

            # Find provider name by issuer
            provider_name = None
            for name, provider in oidc_config.providers.items():
                if provider.issuer == issuer:
                    provider_name = name
                    break

            if subject and provider_name:
                # Look for existing OIDC user
                user = get_user_by_oidc_subject(subject, provider_name)
                if not user:
                    # Create new OIDC user automatically
                    user = create_oidc_user(oidc_payload, provider_name)
                return user

    # Fall back to local JWT validation
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        user = get_user_by_username(username)
        if user is None:
            raise credentials_exception
        return user

    except JWTError:
        raise credentials_exception


@app.get("/")
async def root():
    return {"message": "Welcome to the Simple JSON API"}


@app.get("/auth/oidc/config")
async def get_oidc_config():
    """Get OIDC configuration for client applications"""
    if not OIDC_ENABLED:
        return {"oidc_enabled": False}

    providers_info = {}
    for name, provider in oidc_config.providers.items():
        providers_info[name] = {
            "issuer": provider.issuer,
            "client_id": provider.client_id,
        }

    return {"oidc_enabled": True, "providers": providers_info}


@app.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    user_info = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "auth_type": "oidc"
        if hasattr(current_user, "oidc_subject") and current_user.oidc_subject
        else "local",
    }

    if hasattr(current_user, "oidc_provider") and current_user.oidc_provider:
        user_info["oidc_provider"] = current_user.oidc_provider

    return user_info


@app.post("/register", response_model=User)
async def register(user_data: UserCreate):
    global next_user_id

    # Check if user already exists
    if get_user_by_username(user_data.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = type(
        "User",
        (),
        {
            "id": next_user_id,
            "username": user_data.username,
            "email": user_data.email,
            "password_hash": hashed_password,
        },
    )()

    next_user_id += 1
    users_db.append(user)

    # Return user without password
    return User(id=user.id, username=user.username, email=user.email)


@app.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    user = authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/items", response_model=list[Item])
async def get_items(current_user: User = Depends(get_current_user)):
    return [item for item in items_db if item.owner_id == current_user.id]


@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int, current_user: User = Depends(get_current_user)):
    for item in items_db:
        if item.id == item_id:
            if item.owner_id != current_user.id:
                raise HTTPException(status_code=404, detail="Item not found")
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.post("/items", response_model=Item)
async def create_item(
    item_data: ItemCreate, current_user: User = Depends(get_current_user)
):
    global next_id
    item = Item(
        id=next_id,
        name=item_data.name,
        description=item_data.description,
        price=item_data.price,
        owner_id=current_user.id,
    )
    next_id += 1
    items_db.append(item)
    return item


@app.put("/items/{item_id}", response_model=Item)
async def update_item(
    item_id: int, item_data: ItemCreate, current_user: User = Depends(get_current_user)
):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            if item.owner_id != current_user.id:
                raise HTTPException(
                    status_code=403, detail="Not authorized to update this item"
                )
            updated_item = Item(
                id=item_id,
                name=item_data.name,
                description=item_data.description,
                price=item_data.price,
                owner_id=item.owner_id,
            )
            items_db[i] = updated_item
            return updated_item
    raise HTTPException(status_code=404, detail="Item not found")


@app.delete("/items/{item_id}")
async def delete_item(item_id: int, current_user: User = Depends(get_current_user)):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            if item.owner_id != current_user.id:
                raise HTTPException(
                    status_code=403, detail="Not authorized to delete this item"
                )
            items_db.pop(i)
            return {"message": "Item deleted successfully"}
    raise HTTPException(status_code=404, detail="Item not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
