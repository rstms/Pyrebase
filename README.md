# Pyrebase

A simple python wrapper for the [Firebase API](https://www.firebase.com/docs/rest/guide/).

## Installation

pip install pyrebase

## Usage

### Initialising your Firebase

```
ref = pyrebase.Firebase('https://yourfirebaseurl.firebaseio.com', 'yourfirebasesecret')
```

### Saving Data

#### POST

To save data with an unique, auto-generated, timestamp-based key, use the POST method.

```python
data = '{"name": "Marty Mcfly", "date_created": "05-11-1955"}'
post_this = ref.post("users", data, None)
print(post_this) # 200
```

Example of an autogenerated key: -JqSjGteC4SRzNJ2hH52

#### PUT

To create your own keys use the PUT method. The key in the example below is "Marty".

```python
data = '{"Marty": {"name": "Marty Mcfly", "date_created":"05-11-1955"}}'
put_this = ref.put("users", data)
print(put_this) # 200
```

#### PATCH

Update data for an existing entry.

```python
data = '{"name": "Marty McJunior"}'
patch_this = ref.patch("users", "Marty", data)
print(patch_this) # 200
```
Updates "Marty Mcfly" to "Marty McJunior".

### Reading Data

#### Simple Queries

##### all

Takes a database reference, returning all reference data.

```python
all_users = ref.all("users")
```

##### one

Takes a database reference and a key, returning a single entry.

```python
one_user = ref.one("users", "Marty Mcfly")
```

##### sort_by

Takes a database reference and a property, returning all reference data sorted by property.

```python
users_by_name = ref.sort_by("users", "name")

for i in users:
    print(i["name"])
```

#### Complex Queries

##### sort_by_first

Takes a database reference, a property, a starting value, and a return limit,
returning limited reference data sorted by property.

```python
results = ref.sort_by_first("users", "age", 25, 10)
```

This query returns 10 users with an age of 25 or more.

##### sort_by_last

Takes a database reference, a property, a starting value, and a return limit,
returning limited reference data sorted by property.


```python
results = ref.sort_by_last("users", "age", 25, 10)
```

This query returns 10 users with an age of 25 or less.


### Common Errors

#### Index not defined

Please make sure that the database references you are querying have indexing
[set up properly](https://www.firebase.com/docs/security/guide/indexing-data.html) on Firebase.

#### Property types don't match

Querying properties are not the same type.
Example: name: 0 and name: "hello".