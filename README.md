pgbackend
========

This is an async postgresql backend for django using the
[psycopg](https://github.com/psycopg/psycopg)
driver.

Also, [kitchen](https://github.com/Bi-Coloured-Python-Rock-Snake/pgbackend/tree/main/kitchen)
is a simple django app to test it.

How to test kitchen:

```commandline
pipenv install
```

Then run the ASGI application:

```commandline
uvicorn proj.asgi:application --port 8000
```

Endpoints:

`GET http://localhost:8000/connect/` - to connect by websocket

`GET http://localhost:8000/` - to make an order

`./manage.py makemigrations --check` - console utilities