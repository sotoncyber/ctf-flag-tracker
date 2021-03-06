import logging
import sqlite3
import flask
import tracker

logger = logging.getLogger(__name__)

IntegrityError = sqlite3.IntegrityError

# USAGE
# >>> from tracker.db import init_db
# >>> init_db()
def init_db():
    with tracker.app.app_context():
        db = get_db()
        with tracker.app.open_resource('../schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        with tracker.app.open_resource('../ranks.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        logger.info('Database setup complete.')

def get_db():
    db = getattr(flask.g, '_database', None)
    if db is None:
        db = flask.g._database = sqlite3.connect(tracker.app.config['SQLITE_URI'])
    db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    try:
        cur = get_db().execute(query, args)
    except IntegrityError as e:
        logger.error('Query failed on IntegrityError, dumping query and args:')
        logger.error("Query: '%s'", str(query))
        logger.error('Args: %s', str(args))
        raise e
    rv = cur.fetchall()
    cur.close()
    get_db().commit()
    return (rv[0] if rv else None) if one else rv

@tracker.app.teardown_appcontext
def close_connection(exception):
    db = getattr(flask.g, '_database', None)
    if db is not None:
        db.close()
