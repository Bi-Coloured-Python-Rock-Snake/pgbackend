from psycopg import *
from greenhack import exempt

from .cursor import AsyncConnection

connect = exempt(AsyncConnection.connect)
