from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, List, EmailStr, validator

class PasswordType(str):
    __name__ = 'PasswordType'

class EmailType(str):
    __name__ = 'EmailType'

class Document(BaseModel):
    first_name: str
    last_name: str
    email: EmailType
    password: PasswordType
    age: int
    is_active: bool
    created_at: datetime
    login_attempts: list

    @validator('email')
    def validate_email(cls, value):
        if not isinstance(value, EmailType):
            raise ValueError('Invalid email')
        return value

    @validator('password')
    def validate_password(cls, value):
        if not isinstance(value, PasswordType):
            raise ValueError('Invalid password')
        return value

def generate_mongeasy_schema(data: dict, schema_file_name: Optional[str] = None) -> Dict:
    schema = {}
    for key, value in data.items():
        if isinstance(value, bool):
            schema[key] = {'type': 'bool'}
        elif isinstance(value, int):
            schema[key] = {'type': 'int'}
        elif isinstance(value, float):
            schema[key] = {'type': 'float'}
        elif isinstance(value, str):
            if '@' in value:
                schema[key] = {'type': 'email'}
            elif 'password' in key.lower():
                schema[key] = {'type': 'password'}
            else:
                schema[key] = {'type': 'str'}
        elif isinstance(value, datetime):
            schema[key] = {'type': 'date'}
        elif isinstance(value, list) and value:
            schema[key] = {'type': 'list', 'schema': generate_mongeasy_schema(value[0])}
        elif isinstance(value, dict):
            schema[key] = {'type': 'dict', 'schema': generate_mongeasy_schema(value)}
    if schema_file_name:
        with open(schema_file_name, 'w') as f:
            f.write(str(schema))
    return schema


def generate_pydnatic_schema(data: dict, schema_file_name: Optional[str] = None):
    fields = {}
    for key, value in data.items():
        if isinstance(value, bool):
            fields[key] = (bool, ...)
        elif isinstance(value, int):
            fields[key] = (int, ...)
        elif isinstance(value, float):
            fields[key] = (float, ...)
        elif isinstance(value, str):
            if '@' in value:
                fields[key] = (EmailType, ...)
            elif 'password' in key.lower():
                fields[key] = (PasswordType, ...)
            else:
                fields[key] = (str, ...)
        elif isinstance(value, datetime):
            fields[key] = (datetime, ...)
        elif isinstance(value, List) and value:
            fields[key] = (List[generate_pydnatic_schema(value[0]).__class__], ...)
        elif isinstance(value, dict):
            fields[key] = (generate_pydnatic_schema(value), ...)
            
    schema_class = type('Document', (BaseModel,), {'__annotations__': fields})
    if schema_file_name:
        with open(schema_file_name, "w") as f:
            f.write(schema_class.schema_json(indent=2))
    return schema_class

