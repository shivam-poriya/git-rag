import os
from typing import Optional
from uuid import uuid4
import shutil
from fastapi import APIRouter, HTTPException, Depends
from fastapi import Form
from apps.custom_auth.models.v1_model import UserLogin, BaseUser as User, UserUpdate
from apps.custom_auth.utils import (
    get_password_hash,
    pwd_context,
    create_access_token,
    create_refresh_token,
)
from apps.utils.send_email import register_user_send_email
from apps.utils.permission import verify_user_token
from main import settings
from fastapi import UploadFile, File, Request, BackgroundTasks
# pyrefly: ignore [missing-import]
from jinja2 import Environment, FileSystemLoader, select_autoescape
from apps.db_models import User as DBUser
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter()


@router.get("/test")
async def custom_auth_root():
    return {"message": "Custom Auth API Root"}


@router.post("/register/")
async def register_user(
        user: User,
        background_tasks: BackgroundTasks
):
    # Check if user already exists
    session = settings.db.SessionLocal()
    try:
        existing_user = session.query(DBUser).filter(
            (DBUser.username == user.username) | (DBUser.email == user.email)
        ).first()
        if existing_user:
            if existing_user.username == user.username:
                raise HTTPException(status_code=400, detail="Username already exists")
            if existing_user.email == user.email:
                raise HTTPException(status_code=400, detail="Email already exists")

        # Hash the password before storing
        hashed_password = get_password_hash(user.password)

        # Create a user object with hashed password
        db_user = DBUser(
            username=user.username,
            email=user.email,
            password=hashed_password,
            address=user.address or ""
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        user_id = db_user.id
    finally:
        session.close()

    # Adjust template path relative to the current file location
    template_path = os.path.join(os.path.dirname(__file__), '../templates')

    template_loader = FileSystemLoader(searchpath=template_path)
    template_env = Environment(loader=template_loader, autoescape=select_autoescape(['html', 'xml']))

    try:
        template = template_env.get_template("welcome_email.html")
    except Exception as e:
        print(f"Error loading template: {e}")
        raise HTTPException(status_code=500, detail="Template not found")

    html_content = template.render(username=user.username)
    background_tasks.add_task(register_user_send_email, user.email, "Welcome to Our Platform!", html_content)

    return {
        "message": "User registered successfully",
        "user_id": str(user_id),
    }


@router.post("/login/")
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    session = settings.db.SessionLocal()

    try:
        user = session.query(DBUser).filter(
            DBUser.username == form_data.username
        ).first()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )

        if not pwd_context.verify(
            form_data.password,
            user.password
        ):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )

        access_token = create_access_token(
            data={"sub": str(user.id)}
        )

        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": str(user.id),
            "refresh_token": refresh_token,
        }

    finally:
        session.close()


@router.get("/get-user-profile/")
async def read_protected(
        request: Request, current_user: dict = Depends(verify_user_token)
):
    session = settings.db.SessionLocal()
    try:
        user = session.query(DBUser).filter(DBUser.id == int(current_user.get("_id"))).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = {
            "username": user.username,
            "email": user.email,
            "address": user.address,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "organization_name": user.organization_name,
            "location": user.location,
            "phone": user.phone,
            "birthday": user.birthday,
            "profile_photo": user.profile_photo,
        }
        if user.profile_photo:
            user_data["profile_photo_path"] = (
                f"{request.base_url}media/user_profile/{user.profile_photo}"
            )
        return user_data
    finally:
        session.close()


@router.post("/update-user-profile/")
async def update_user_profile(
        first_name: str = Form(
            "", description="Please provide name,", max_length=70, min_length=3
        ),
        last_name: str = Form(
            "", description="Please provide name,", max_length=70, min_length=3
        ),
        organization_name: str = Form(
            "", description="Please provide name,", max_length=70, min_length=3
        ),
        location: str = Form(
            "", description="Please provide name,", max_length=70, min_length=3
        ),
        phone: str = Form(
            ..., description="Please provide name,", max_length=70, min_length=3
        ),
        birthday: str = Form(
            "", description="Please provide name,", max_length=70, min_length=3
        ),
        username: str = Form(
            ..., description="Please provide name,", max_length=70, min_length=3
        ),
        email: str = Form(
            ..., description="Please provide name,", max_length=70, min_length=3
        ),
        photo: Optional[UploadFile] = File(""),
        current_user: dict = Depends(verify_user_token),
):
    session = settings.db.SessionLocal()
    try:
        user = session.query(DBUser).filter(DBUser.id == int(current_user.get("_id"))).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        if photo:
            user_profile_folder = os.path.join(settings.UPLOAD_DIR, "user_profile")
            os.makedirs(user_profile_folder, exist_ok=True)

            # Save the photo to the product's subfolder
            photo_filename = f"{uuid4()}_{photo.filename}"
            photo_path = os.path.join(user_profile_folder, photo_filename)
            with open(photo_path, "wb") as buffer:
                shutil.copyfileobj(photo.file, buffer)
        else:
            photo_filename = user.profile_photo

        user.first_name = first_name
        user.last_name = last_name
        user.organization_name = organization_name
        user.location = location
        user.phone = phone
        user.birthday = birthday
        user.username = username
        user.email = email
        user.profile_photo = photo_filename

        session.commit()
        session.refresh(user)

        user_data = {
            "username": user.username,
            "email": user.email,
            "address": user.address,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "organization_name": user.organization_name,
            "location": user.location,
            "phone": user.phone,
            "birthday": user.birthday,
            "profile_photo": user.profile_photo,
        }
        return user_data
    finally:
        session.close()
