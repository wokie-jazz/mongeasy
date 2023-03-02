"""
This module contains the Document class for interacting with MongoDB collections.

MIT License

Copyright (c) 2023 Joakim Wassberg

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation 
files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, 
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom 
the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE 
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, 
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from typing import Callable, Union, Any
from functools import wraps
import os
import time
from .document import Document
from .database import Database
from .mongeasy_exceptions import MongoDBConnectionError, MongoFieldError
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


# *******************
# Helper functions
# *******************
def mongo_check_and_connect(func: Callable) -> Callable:
    """
    Decorator to check if the database is connected and connect if not
    :param func: The function to decorate
    :return: Callable
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        Wrapper function to check if the database is connected and connect if not
        If the database is not connected, 
        the MONGO_DB_CONNECTION_STRING and MONGO_DB_NAME environment variables must be set
        """
        if not Database.is_connected():
            if os.environ.get('MONGO_DB_CONNECTION_STRING') and os.environ.get('MONGO_DB_NAME'):
                init_db(os.environ.get('MONGO_DB_CONNECTION_STRING'), os.environ.get('MONGO_DB_NAME'))
            else:
                msg = 'init_db function must be called before creation of collection classes.\n' 
                msg += 'Another option is to set the MONGO_DB_CONNECTION_STRING and MONGO_DB_NAME environment variables'
                raise MongoDBConnectionError(msg)
        return func(*args, **kwargs)
    return wrapper

def _validate(self):
    """
    Method to validate the document against the schema.
    Only injected in the class if a schema is provided
    """
    for field_name, field_schema in self.schema.items():
        field_value = self.__dict__.get(field_name)
        field_type = field_schema.get('type')
        field_required = field_schema.get('required', False)
        # If we have a custom validator, use it
        if 'validator' in field_schema and not field_schema['validator'](field_value):
            raise ValueError(f"Field '{field_name}' is invalid")

        # Check that required fields are present
        if field_required and field_value is None:
            raise ValueError(f"Required field '{field_name}' is missing")

        # Check that the field has the correct type
        if field_value is not None and not isinstance(field_value, field_type):
            raise TypeError(f"Field '{field_name}' has invalid type. Expected {field_type}, got {type(field_value)}")

    # Check that all fields in the document are present in the schema
    for field_name in self.__dict__.keys():
        if field_name != '_id' and field_name not in self.schema:
            raise MongoFieldError(f"Field '{field_name}' is not in the schema")

@mongo_check_and_connect
def create_document_class(class_name: str, collection_name: Union[str, None] = None, schema: dict[str, Any] = None):
    """
    Factory function for creating document classes
    :param class_name: str, name of docuent class
    :param collection_name: str or None, name of collection in database. If None, the class name will be used
    :param schema: dict or None, document schema. If None, no schema validation will be performed.
    :return: The newly created collection class
    """
    if collection_name is None:
        collection_name = class_name

    
    # Get the collection object from the database
    collection = Database.db[collection_name]

    # Define the collection class
    document_class = type(class_name, (Document,), {'collection': collection})

    # Add the class to the instances dict
    Database.instances[class_name] = document_class

    # Define the validate method if a schema is provided
    if schema is not None:
        # Add the validate method to the collection class
        document_class.validate = _validate
        document_class.schema = schema

    return document_class


def add_base_class(cls, base_class: type) -> None:
    """
    Helper function to add a base class to a collection class
    :param cls: The collection class
    :param base_class: The base class to add
    :return: None
    """
    cls.__bases__ = (base_class,) + cls.__bases__

def add_collection_method(cls, method: Callable) -> None:
    """
    Helper function to add methods to a collection class.
    Usage:
    def method(self):
        print(self.name)

    user = create_collection_class('User')
    add_collection_method(User, method)
    user.method()
    :param cls: The collection class
    :param method: The method to add to the class
    :return: None
    """
    setattr(cls, method.__name__, method)


def init_db(connection_str: str, database: str, retries: int = 3, retry_delay: int = 2) -> None:
    """
    Function to initialize database connection. Must be called before any use of the library
    :param connection_str: str, the database connection string
    :param database: str, the name of the database to use
    :param retries: int, the number of times to retry connection, defaults to 3
    :param retry_delay: int, the delay between retries, defeults to 2 seconds
    :return: None
    """
    for i in range(retries):
        try:
            client = MongoClient(connection_str)
            client.server_info()
            break
        except ServerSelectionTimeoutError as e:
            if i == retries - 1:
                raise MongoDBConnectionError("Could not connect to database") from e
            else:
                time.sleep(retry_delay ** i)
    Database.db = client[database]
    Database.client = client
    
    