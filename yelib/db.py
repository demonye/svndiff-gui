class DB:
    def __init__(self, db_module, keywords):
        self._conn = db_module.connect(**keywords)
        self._code = 0
        self._msg = ""

    def __del__(self):
        if self._conn != None:
            self._conn.close()

    def _exec(self, func, *args, **kwargs):
        """
        For catching exceptions in different databases, please reimplement in drived classes
        """
        pass

    def _query(self, sql, args=(), arrsize=0):
        ret = None
        try:
            c = self._conn.cursor()
            if arrsize > 0: c.arraysize = arrsize
            c.execute(sql, args)
            ret = c.fetchall()
        except self._db.DatabaseError:
            raise
        finally:
            c.close()
        return ret

    def _query2(self, callback, sql, args=(), arrsize=0):
        try:
            c = self._conn.cursor()
            if arrsize > 0: c.arraysize = arrsize
            c.execute(sql, args)
            while True:
                ret = c.fetchmany()
                if len(ret) == 0: break
                callback(ret)
        except self._db.DatabaseError:
            raise
        finally:
            c.close()

    def _execute(self, sql, args=(), arrsize=0):
        ret = None
        try:
            c = self._conn.cursor()
            c.execute(sql, args)
            ret = c.rowcount
        except self._db.DatabaseError:
            raise
        finally:
            c.close()
        return ret

    def _executemany(self, sql, args=(), arrsize=0):
        ret = None
        try:
            c = self._conn.cursor()
            c.executemany(sql, args)
            ret = c.rowcount
        except self._db.DatabaseError:
            raise
        finally:
            c.close()
        return ret

    def query(self, sql, args=(), arrsize=1):
        return self._exec(self._query, sql, args, arrsize)

    def query2(self, callback, sql, args=(), arrsize=1):
        return self._exec(self._query2, callback, sql, args, arrsize)

    def execute(self, sql, args=()):
        return self._exec(self._execute, sql, args)

    def executemany(self, sql, args=()):
        return self._exec(self._executemany, sql, args)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

class OracleDB(DB):
    def __init__(self, **keywords):
        self._db = __import__('cx_Oracle')
        if 'pw' in keywords:
            keywords['password'] = keywords.pop('pw')
        keywords['dsn'] = keywords.pop('db')

        self.dbname = 'oracle'
        self._arrsize = 0
        DB.__init__(self, self._db, keywords)

    def _exec(self, func, *args, **kwargs):
        ret = None
        try:
            ret = func(*args, **kwargs)
        except self._db.DatabaseError as exc:
            error, = exc.args
            self._code = error.code
            self._msg = error.message.rstrip()
        return ret

    def _executemany(self, sql, args=(), arrsize=0):
        ret = None
        try:
            c = self._conn.cursor()
            c.prepare(sql)
            c.executemany(None, args)
            ret = c.rowcount
        except self._db.DatabaseError as exc:
            error, = exc.args
            self._code = error.code
            self._msg = error.message.rstrip()
        finally:
            c.close()
        return ret

class MySQLDB(DB):
    def __init__(self, **keywords):
        self._db = __import__('MySQLdb')
        if 'pw' in keywords:
            keywords['passwd'] = keywords.pop('pw')
        if 'charset' not in keywords:
            keywords['charset'] = 'gbk'

        self.dbname = 'mysql'
        DB.__init__(self, self._db, keywords)

    def _exec(self, func, *args, **kwargs):
        ret = -1
        try:
            ret = func(*args, **kwargs)
        except self._db.MySQLError as exc:
            self._code = exc[0]
            self._msg = exc[1]
        return ret

_databases = {}

def database(dburl=None, **params):
    dbn = params.pop('dbn')
    if dbn in _databases:
        return _databases[dbn](**params)
    else:
        raise UnknownDB(dbn)

def register_database(name, clazz):
    _databases[name] = clazz

register_database('oracle', OracleDB)
register_database('mysql', MySQLDB)

if __name__ == "__main__":
    db = database(dbn='mysql', host='localhost', user='root', pw='root', db='devdb', charset='gbk')
    print(db.execute('insert into test1 values (%s, %s)', (1, 'world')))

    db = database(dbn='oracle', user='devdb', pw='devdb', db='XE')
    for v in db.query('select * from t1'):
        print(v[0], v[1])
    print(db.execute('insert into t1 values (:1, :2)', (1, 'world')))

