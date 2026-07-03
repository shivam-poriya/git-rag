from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from apps.utils.utils import PyObjectId
from fastapi import UploadFile, File


class BaseUser(BaseModel):
    username: str = Field(..., description="Please Provide a unique Username.", max_length=32, min_length=3)
    email: EmailStr = Field(..., description="Please Provide a unique email.", max_length=70, min_length=5)
    password: str = Field(None, description="Please Provide a password ex.Example@123.", max_length=32, min_length=8)
    address: Optional[str] = Field("", description="Please Provide a address.", max_length=32)


class UserLogin(BaseModel):
    username: str = Field(..., description="Please Provide a unique Username.", max_length=32, min_length=3)
    password: str = Field(None, description="Please Provide a password ex.Example@123.", max_length=32, min_length=8)


class UserUpdate(BaseModel):
    # id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')
    first_name: Optional[str]
    last_name: Optional[str]
    organization_name: Optional[str]
    location: Optional[str]
    phone: Optional[str]
    birthday: Optional[str]
    username: Optional[str]
    email: Optional[str]
    # photo: UploadFile = File(...)

    # class Config:
    #     json_encoders = {
    #         ObjectId: lambda x: str(x)
    #     }
    #     populate_by_name = True
