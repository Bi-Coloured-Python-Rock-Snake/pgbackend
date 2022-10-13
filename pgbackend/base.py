from django.conf import settings
from psycopg import IsolationLevel

import pgbackend.cursor

from django.db.backends.postgresql import base

class DatabaseWrapper(base.DatabaseWrapper):
    from . import Database

    # a copy of the inherited method
    def get_new_connection(self, conn_params):
        Database = self.Database
        assert self.is_psycopg3
        ctx = base.get_adapters_template(settings.USE_TZ, self.timezone)
        connection = Database.connect(**conn_params, context=ctx)

        # self.isolation_level must be set:
        # - after connecting to the database in order to obtain the database's
        #   default when no value is explicitly specified in options.
        # - before calling _set_autocommit() because if autocommit is on, that
        #   will set connection.isolation_level to ISOLATION_LEVEL_AUTOCOMMIT.
        options = self.settings_dict["OPTIONS"]
        try:
            isolevel = options["isolation_level"]
        except KeyError:
            self.isolation_level = IsolationLevel.READ_COMMITTED
        else:
            try:
                self.isolation_level = IsolationLevel(isolevel)
            except ValueError:
                raise base.ImproperlyConfigured(
                    "bad isolation_level: %s. Choose one of the "
                    "'psycopg.IsolationLevel' values" % (options["isolation_level"],)
                )
            connection.isolation_level = self.isolation_level

        connection.cursor_factory = base.Cursor

        return connection

    def get_new_connection(self, conn_params,
                           get_new_connection=get_new_connection):
        connection = get_new_connection(self, conn_params)
        connection.cursor_factory = pgbackend.cursor.AsyncCursor
        return connection