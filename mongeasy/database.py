
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

from pymongo.change_stream import ChangeStream
from pymongo import MongoClient
from pymongo.collection import Collection


class Database:
    # Class-level variable to store the connection information for the database
    connection_info = None
    client = None
    db = None
    collection = None
    instances = {}
    
    def __init__(self, name):
        self.name = name

    @classmethod
    def connect(cls):
        # Establish a connection to the database using the stored connection information
        if cls.connection_info is not None:
            cls.client = MongoClient(cls.connection_info)
            cls.db = cls.client.get_database()

    @classmethod
    def set_connection_info(cls, connection_info):
        # Set the connection information for the database
        cls.connection_info = connection_info
        
    @classmethod
    def is_connected(cls):
        return cls.client is not None        

 