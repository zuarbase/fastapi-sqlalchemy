# FastAPI-SQLAlchemy
Full-stack, asynchronous Python3 framework.

## Design goals
* Fast, full-service framework
* Modular approach that does not force any design decisions

## Getting started

```python
from fastapi import FastAPI, Request

from fastapi_sqlalchemy import crud, db_registry
from fastapi_sqlalchemy.middleware import SessionMiddleware
from fastapi_sqlalchemy.models import BASE, Session, User

DATABASE_URL = "sqlite:///sqlite.db?check_same_thread=False"


# Define our model
class MyUser(User):
    pass


# Instantiate the application
app = FastAPI()
app.add_middleware(SessionMiddleware, bind=DATABASE_URL)

# Create all tables
bind = db_registry.get_or_create(DATABASE_URL)
BASE.metadata.create_all(bind=bind)

# Load some data
session = Session()
for name in ["alice", "bob", "charlie", "david"]:
    user = MyUser.get_by_username(session, name)
    if user is None:
        user = MyUser(username=name)
        session.add(user)
session.commit()

# Add an endpoint
@app.get("/users")
async def list_users(
        request: Request
):
    return await crud.list_instances(MyUser, request.state.session)
```

Assuming the above code is stored in the file `main.py`, then run it via:
```bash
uvicorn main:app --reload
```

Call the endpoint:
```bash
curl -s localhost:8000/users | jq .
```

The output should contain a list of 4 users,
each with the attributes `id`, `username`, `updated_at` and `created_at`.
 
<aside class="warning">
NOTE: Sqlite3 really doesn't like multiple threads using the same connection (hence <i>check_same_thread=False</i>).
In this case, it's safe but in production a different database should be used.
</aside>
