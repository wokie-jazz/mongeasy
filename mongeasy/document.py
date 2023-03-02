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

import datetime
from copy import copy, deepcopy
from typing import Union
import logging
import json
import bson
from .mongeasy_exceptions import MongoDBCollectionError, MongoFieldError
from .base_dict import BaseDict
from .database import Database
from .result_list import ResultList
import pymongo


class Document(BaseDict, Database):
    """
    This class acts as the base class for collection classes. Each instance of the subclasses
    will represent a single document
    """
    collection = None
    schema = None
    logger = logging.getLogger('mongeasy')

    def __init__(self, *args, **kwargs):
        super().__init__()

        # Handle positional arguments
        if len(args) == 1 and isinstance(args[0], dict):
            as_dict = copy(args[0])
        elif len(args) == 0:
            as_dict = copy(kwargs)
        else:
            raise TypeError(f'Document() takes 1 positional argument or keyword arguments but {len(args) + len(kwargs)} were given')

        # Convert embedded Documents to dictionaries
        for key, value in as_dict.items():
            if isinstance(value, Document):
                try:
                    as_dict[key] = value.to_dict()
                except Exception as e:
                    Document.logger.error(f'Failed to convert embedded Document to dictionary: {str(e)}')
                    del as_dict[key]

        # If _id is not present we add the _id attribute
        if '_id' not in as_dict:
            self._id = None
        else:
            try:
                self._id = bson.ObjectId(str(as_dict['_id']))
            except bson.errors.InvalidId:
                raise ValueError(f'Invalid _id: {as_dict["_id"]}')

        # Update the object
        self.__dict__.update(as_dict)
    
    def has_changed(self) -> dict:
        """
        Checks if any of the fields in this document has changed
        :return: dict, a dict with the changed fields, empty if no fields have changed
        """
        if self._id is None:
            return {}

        changed_fields = {}
        for key, value in self.__dict__.items():
            if key != '_id':
                try:
                    result = self.collection.find_one({'_id': self._id}, {key: 1})
                except (pymongo.errors.OperationFailure, pymongo.errors.ServerSelectionTimeoutError) as e:
                    Document.logger.error(f"Error querying the database: {e}")
                    return {}

                if result and key in result and result[key] != value:
                    changed_fields[key] = value
        return changed_fields

    def is_saved(self) -> bool:
        """
        Checks if this document has been saved to the database
        :return: bool, True if the document has been saved, False otherwise
        """
        return not bool(self.has_changed())
    
    def save(self):
        """
        Saves the current object to the database
        :return: The saved object
        """
        if self.collection is None:
            Document.logger.error("The collection does not exist")
            raise MongoDBCollectionError('The collection does not exist')

        if self.schema is not None:
            self.validate()
        
        # If _id is None, this is a new document
        if self._id is None:
            del self._id
            res = self.collection.insert_one(self.__dict__)
            self._id = res.inserted_id
            return self

        # if no fields have changed, return the document unchanged
        if not (changed_fields := self.has_changed()):
            return self

        # update the document
        update_result = self.collection.update_one({'_id': self._id}, {'$set': changed_fields})
        if update_result.matched_count == 0:
            Document.logger.error(f"Document with _id {self._id} does not exist")
            raise ValueError(f"Document with _id {self._id} does not exist")
        else:
            return self

    def reload(self):
        """
        Fetches the latest state of the document from the database and updates the current instance with the changes.
        """
        if self._id is None:
            raise ValueError('Cannot reload unsaved document')

        # fetch the latest state of the document from the database
        db_doc = self.collection.find_one({'_id': self._id})
        if db_doc is None:
            raise ValueError(f"Document with _id {self._id} does not exist")

        # update the current instance with the changes
        for key, value in db_doc.items():
            if isinstance(value, dict) and not isinstance(value, Document):
                # convert any embedded dictionary to an instance of BaseDict
                self[key] = BaseDict(value)
            else:
                self[key] = value

    def delete_field(self, field: str):
        """
        Removes a field from this document
        :param field: str, the field to remove
        :return: None
        """
        try:
            self.collection.update_one({'_id': self._id}, {"$unset": {field: ""}})
        except Exception as e:
            Document.logger.error(f"Error deleting field '{field}' from document with id '{self._id}': {e}")
        else:
            Document.logger.info(f"Field '{field}' deleted from document with id '{self._id}'")

    def delete(self):
        """
        Delete the current object from the database
        :return: None
        """
        if self.collection is None:
            raise MongoDBCollectionError('The collection does not exist')

        if self._id is None:
            raise ValueError('Cannot delete unsaved document')

        self.collection.delete_one({'_id': self._id})

    def to_json(self):
        """
        Converts the current object to a JSON string
        :return: str, the JSON string representation of the object
        """
        return json.dumps(self.to_json_type())

    @classmethod
    def create_index(cls, keys: list[str], index_type: str = 'asc', unique: bool = False, name: Union[str, None] = None) -> None:
        """
        Creates an index on the specified keys
        :param keys: The keys to index on
        :param index_type: The index type, either 'asc' (default) or 'desc'
        :param unique: Whether the index should be unique
        :param name: The name of the index
        :return: None
        """
        # Check that keys is a non-empty list of strings
        if not isinstance(keys, list) or not all(isinstance(key, str) for key in keys) or len(keys) == 0:
            raise ValueError('keys must be a non-empty list of strings')

        # Check that index_type is either 'asc' or 'desc'
        if index_type not in ['asc', 'desc']:
            raise ValueError('index_type must be either "asc" or "desc"')

        # Check that name is either None or a non-empty string
        if name is not None and not isinstance(name, str):
            raise ValueError('name must be either None or a non-empty string')

        index_name = name or '_'.join(keys) + '_' + index_type.lower()
        index_type = pymongo.ASCENDING if index_type == 'asc' else pymongo.DESCENDING
        cls.collection.create_index([(key, index_type) for key in keys], name=index_name, unique=unique)

    @classmethod
    def get_by_id(cls, _id:str) -> Union['Document', None]:
        """
        Get a document by its _id
        :param _id: str, the id of the document
        :return: The retrieved document or None
        """
        try:
            return cls(cls.collection.find_one({'_id': bson.ObjectId(_id)}))
        except bson.errors.InvalidId:
            return None

    @classmethod
    def insert_many(cls, items: list[dict]) -> None:
        """
        Inserts a list of dictionaries into the database
        :param items: list of dict, items to insert
        :return: None
        """
        for item in items:
            try:
                cls(item).save()
            except pymongo.errors.PyMongoError as e:
                Document.logger.exception(f"Error inserting item: {item}. Exception: {e}")

    @classmethod
    def find(cls, **kwargs):
        """
        Find a document that matches the keywords
        :param kwargs: keyword arguments or dict to match
        :return: ResultList
        """
        if len(kwargs) == 1 and isinstance(kwargs.get(list(kwargs.keys())[0]), dict):
            query_params = copy(kwargs.get(list(kwargs.keys())[0]))
        else:
            query_params = copy(kwargs)
        return ResultList(cls(item) for item in cls.collection.find(query_params))

    @classmethod
    def find_in(cls, field:str, values:list) -> ResultList:
        """
        Find a document that matches the keywords
        :param field: str, the field to search in
        :param values: list, the values to search for
        :return: ResultList
        """
        return ResultList(cls(item) for item in cls.collection.find({field: {"$in": values}}))

    @classmethod
    def delete(cls, **kwargs) -> None:
        """
        Delete the document that matches the keywords
        :param kwargs: keyword arguments or dict to match
        :return: None
        """
        if len(kwargs) == 1 and isinstance(kwargs.get(list(kwargs.keys())[0]), dict):
            query_params = copy(kwargs.get(list(kwargs.keys())[0]))
        else:
            query_params = copy(kwargs)
        cls.collection.delete_many(query_params)

    @classmethod
    def document_count(cls) -> int:
        """
        Returns the total number of documents in the collection
        :return: int
        """
        return cls.collection.count_documents({})

def _convert_to_json(struct):
    """
    Converts all datetime to a timestamp from epoch.
    """
    for key, value in struct.items():
        if isinstance(value, datetime.datetime):
            struct[key] = value.timestamp()
        elif isinstance(value, bson.ObjectId):
            struct[key] = str(value)
        elif isinstance(value, dict):
            _convert_dict_to_json(value)
        elif isinstance(value, list) and len(value) > 0:
            _convert_list_to_json(value)

def _convert_list_to_json(struct_list):
    """
    Converts a list of values to JSON types
    """
    for i in range(len(struct_list)):
        value = struct_list[i]
        if isinstance(value, dict):
            _convert_dict_to_json(value)
        elif isinstance(value, datetime.datetime):
            struct_list[i] = value.timestamp()
        elif isinstance(value, bson.ObjectId):
            struct_list[i] = str(value)

def _convert_dict_to_json(struct):
    """
    Converts a dictionary to JSON types
    """
    for key, value in struct.items():
        if isinstance(value, dict):
            _convert_dict_to_json(value)
        elif isinstance(value, list) and len(value) > 0:
            _convert_list_to_json(value)
        elif isinstance(value, datetime.datetime):
            struct[key] = value.timestamp()
        elif isinstance(value, bson.ObjectId):
            struct[key] = str(value)


def _convert_datetime_list_to_json(struct_list):
    """
    Converts a list of datetimes to a list of timestamps
    """
    struct_list[:] = [dt.timestamp() for dt in struct_list]

def _convert_objectid_list_to_json(struct_list):
    """
    Converts a list of ObjectIds to a list of strings
    """
    struct_list[:] = [str(oid) for oid in struct_list]
    
  