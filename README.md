pgbackend
========

This is an async postgresql backend for django using `psycopg` driver.

Also, [kitchen](https://github.com/Bi-Coloured-Python-Rock-Snake/pgbackend/tree/main/kitchen)
is a simple django project to test it.

How to test kitchen:

```
uvicorn proj.asgi:application --port 8000
```

`GET http://localhost:8000/connect/` - to connect by websocket
`GET http://localhost:8000/` - to make an order

`./manage.py makemigrations --check` - console utilities