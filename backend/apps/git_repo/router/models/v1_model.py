from typing import Optional
from pydantic import BaseModel, Field


class RepoCloneRequest(BaseModel):
    repo_url: str = Field(
        ...,
        description="Please Provide git repo url."
    )

    branch_name: Optional[str] = Field(
        None,
        description="Please Provide git repo branch name."
    )


class RepoPrivateCloneRequest(BaseModel):
    repo_url: str = Field(
        ...,
        description="Please Provide git repo url."
    )

    token: str = Field(
        ...,
        description="Please Provide git repo token."
    )

    branch_name: Optional[str] = Field(
        None,
        description="Please Provide git repo branch name."
    )