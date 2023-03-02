# Mongeasy

Mongeasy is a simple and easy-to-use Python wrapper around the pymongo library, designed to make it easier to work with MongoDB databases.

## Installation

You can install Mongeasy using pip:

```bash
pip install mongeasy
```

Mongeasy requires Python 3.6 or higher.
## Usage

To use Mongeasy, you can create a new document class using the `create_document_class()` function, which takes two arguments: the name of the document class and the name of the collection it should be associated with. The new class will automatically inherit from the `Document` base class and will be associated with the specified collection.

Here's an example:

```python
from mongeasy import create_document_class

create_document_class('User', 'users')

# Create a new user object and save it to the database
data = {
    'first_name': 'Alice',
    'last_name': 'Smith'
}
u1 = User(data)
u1.save()

# Create another user object and save it to the database
u2 = User(first_name='Bob', last_name='Jones')
u2.save()

# Find a user by a query
u3 = User.find(first_name='Alice').first_or_none()
if u3 is not None:
    print(u3)

    # Update a document
    u3.last_name = 'Anderson'
    u3.save()
```

In this example, we create a new User document class that is associated with the users collection. We create two new user objects and save them to the database using the save() method. We then find a user object using the find() method and update it using the save() method.

Mongeasy provides high-level classes for working with databases, collections, and documents, as well as custom field types for common data types such as passwords and email addresses.

## Classes
Mongeasy provides the following classes:

*Database*: A class for working with MongoDB databases.
*Collection*: A class for working with MongoDB collections.
*Document*: A base class for dynamically created document classes.
*Dict*: A custom dictionary class that supports both dictionary-style and dot-notation access to its members.
*ResultList*: A custom list class that adds two methods for getting the first or last item in the list if it exists, or None otherwise.

### Custom Field Types
Mongeasy provides the following custom field types:

*PasswordType*: A field type that stores passwords securely using the bcrypt library.
*EmailType*: A field type that validates email addresses using a regular expression.

### Contributing
Contributions to Mongeasy are welcome! To contribute, please follow the steps below:

Fork the repository on GitHub.
Create a new branch with your changes.
Write tests for your changes and make sure all existing tests pass.
Submit a pull request.

### License
Mongeasy is released under the MIT License. See the LICENSE file for more information.