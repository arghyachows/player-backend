from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Security
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer, SecurityScopes
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
import csv
import io

import models
import schemas
import auth
from database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Configure CORS
origins = [
    "https://player-angular-five.vercel.app",
    "http://localhost:4200",  # Angular default port
]

app = FastAPI(
    title="Player Management API",
    description="A REST API for managing players with JWT authentication",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Operations with authentication"
        },
        {
            "name": "Players",
            "description": "Operations with players"
        }
    ]
)

# Configure OAuth2 with Bearer token
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add JWT bearer security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter the JWT token in the format: Bearer <token>"
        }
    }
    # Add global security requirement
    openapi_schema["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Auth endpoints
@app.post("/api/signup", response_model=schemas.User, tags=["Authentication"])
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = auth.get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/token", response_model=schemas.Token, tags=["Authentication"])
async def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/logout", tags=["Authentication"])
async def logout(
    current_user: models.User = Security(auth.get_current_active_user, scopes=[])
):
    # In a real application, you might want to blacklist the token
    return {"message": "Successfully logged out"}

# Player endpoints
@app.post("/api/players/", response_model=schemas.Player, tags=["Players"])
def create_player(
    player: schemas.PlayerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Security(auth.get_current_active_user, scopes=[])
):
    db_player = models.Player(**player.dict())
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player

@app.get("/api/players/", response_model=List[schemas.Player], tags=["Players"])
def read_players(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Security(auth.get_current_active_user, scopes=[])
):
    players = db.query(models.Player).offset(skip).limit(limit).all()
    return players

@app.get("/api/players/{player_id}", response_model=schemas.Player, tags=["Players"])
def read_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Security(auth.get_current_active_user, scopes=[])
):
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@app.put("/api/players/{player_id}", response_model=schemas.Player, tags=["Players"])
def update_player(
    player_id: int,
    player: schemas.PlayerUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Security(auth.get_current_active_user, scopes=[])
):
    db_player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if db_player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    
    for key, value in player.dict(exclude_unset=True).items():
        setattr(db_player, key, value)
    
    db.commit()
    db.refresh(db_player)
    return db_player

@app.delete("/api/players/{player_id}", tags=["Players"])
def delete_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Security(auth.get_current_active_user, scopes=[])
):
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    
    db.delete(player)
    db.commit()
    return {"message": "Player deleted successfully"}


@app.get("/api/search", response_model=List[schemas.Player], tags=["Players"])
def search_players_by_name(
    name: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Security(auth.get_current_active_user, scopes=[])
):
    players = db.query(models.Player).filter(models.Player.name.ilike(f"%{name}%")).offset(skip).limit(limit).all()
    if not players:
        raise HTTPException(status_code=404, detail="No players found with the given name")
    return players

# ...existing code...

@app.post("/api/players/upload-csv", response_model=List[schemas.Player], tags=["Players"])
async def upload_players_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        # Read the CSV file
        contents = await file.read()
        csv_data = contents.decode()
        csv_file = io.StringIO(csv_data)
        csv_reader = csv.DictReader(csv_file)
        
        # List to store created players
        created_players = []
        
        # Process each row
        for row in csv_reader:
            try:
                # Check if name exists
                if "name" not in row or not row["name"].strip():
                    raise HTTPException(status_code=400, detail="Name field is required")
                
                # Create player object with optional fields
                player_data = {
                    "name": row["name"].strip()
                }
                
                # Add optional fields if they exist and are not empty
                if "position" in row and row["position"].strip():
                    player_data["position"] = row["position"].strip()
                if "team" in row and row["team"].strip():
                    player_data["team"] = row["team"].strip()
                if "age" in row and row["age"].strip():
                    try:
                        player_data["age"] = int(row["age"])
                    except ValueError:
                        pass  # Skip invalid age values
                if "jersey_number" in row and row["jersey_number"].strip():
                    try:
                        player_data["jersey_number"] = int(row["jersey_number"])
                    except ValueError:
                        pass  # Skip invalid jersey number values
                
                # Validate data using Pydantic model
                player_in = schemas.PlayerCreate(**player_data)
                
                # Create player in database
                db_player = models.Player(**player_in.dict())
                db.add(db_player)
                db.commit()
                db.refresh(db_player)
                created_players.append(db_player)
                
            except HTTPException as e:
                raise e
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error processing row: {str(e)}"
                )
        
        return created_players
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV file: {str(e)}")
    finally:
        await file.close() 