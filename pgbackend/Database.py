from psycopg import *
from shadow import hide

from .cursor import AsyncConnection

connect = hide(AsyncConnection.connect)
