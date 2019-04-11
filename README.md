# FastAPI-SQLAlchemy
Full-stack, asynchronous Python3 framework.

## Getting started

```python
from starlette.requests import Request

from fastapi_sqlalchemy import FastAPI_SQLAlchemy, crud
from fastapi_sqlalchemy.models import BASE, User

# Define our model
class MyUser(User):
    pass
    

# Instantiate the application
app = FastAPI_SQLAlchemy("sqlite:///sqlite.db?check_same_thread=False")
app.create_all()

# Load some data
session = app.Session()
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