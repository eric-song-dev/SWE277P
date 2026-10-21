from pydantic import BaseModel


class CurrentUser(BaseModel):
    id: int
    username: str
    display_name: str


class MeResponse(CurrentUser):
    auth_mode: str
