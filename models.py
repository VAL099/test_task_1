
from pydantic import BaseModel

class Register(BaseModel):
    username: str
    password: str

class Product(BaseModel):
    name: str

class Rating(BaseModel):
    mark: int
    text: str
    status: int