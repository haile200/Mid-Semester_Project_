class DummyCursor:
    def __init__(self, description=(), rows=None, fetchone_results=None, one=None):
        self.description = description
        self.rows = list(rows or [])
        self.fetchone_results = list(fetchone_results or [])
        if one is not None:
            self.fetchone_results.insert(0, one)
        self.queries = []
        self.lastrowid = 42

    def execute(self, query, params=None):
        self.queries.append((query, tuple(params) if params is not None else ()))

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        if self.rows:
            return self.rows.pop(0)
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None

    def close(self):
        pass


class DummyConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        pass