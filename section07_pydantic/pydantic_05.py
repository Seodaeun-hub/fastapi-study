from pydantic import BaseModel,  ValidationError, field_validator, model_validator
from typing import Optional
#valiation을 custom 하는 법.

class User(BaseModel):
    username: str
    password: str
    confirm_password: str
    
    @field_validator('username')
    #class method다 라고 선언할 때는 cls 넣어줘야함.
    def username_must_not_be_empty(cls, value: str):
        if not value.strip():
            #"   "-> None
            raise ValueError("username must not be empty")
        return value
  
    @field_validator('password')
    def password_must_be_strong(cls, value: str):
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in value):
            #예 : sec012345 (isdigit(숫자냐))
            #     00011111 -> 하나라도 1이 있으면 1, 다 0이면 0 (any)
            raise ValueError('Password must contain at least one digit')
        if not any(char.isalpha() for char in value):
            raise ValueError('Password must contain at least one letter')
        return value
    
    @model_validator(mode='after')
    def check_passwords_match(cls, values):
        password = values.password
        confirm_password = values.confirm_password
        if password != confirm_password:
            raise ValueError("Password do not match")
        return values
 
    
# 검증 테스트    
try:
    user = User(username="john_doe", password="Secret123", confirm_password="Secret123")
    print(user)
except ValidationError as e:
    print(e)