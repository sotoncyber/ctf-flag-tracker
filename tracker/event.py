import logging
import flask_login
import tracker.db as db
import tracker.leaderboard as leaderboard
import tracker.team as team

logger = logging.getLogger(__name__)


class Event():

    def __init__(self, id, name):
        self.id = id
        self.name = name

    # Get number of flags available in this event
    def get_num_flags(self):
        num = db.query_db('''
            SELECT COUNT(*)
            FROM flags f
            WHERE f.event_id = ?
            GROUP BY f.event_id
        ''', [self.id], one=True)
        if num is None:
            return 0
        return num[0]

    # Get number of points available in this event
    def get_num_points(self):
        num = db.query_db('''
            SELECT SUM(f.value)
            FROM events e
            LEFT JOIN flags f ON f.event_id = e.id
            WHERE e.id = ?
            GROUP BY e.id;
        ''', [self.id], one=True)[0]
        if num is None:
            return 0
        return num

    # Check if this event is the active event
    def is_active(self):
        teams = db.query_db('SELECT active FROM events WHERE id = ?', [self.id], one=True)[0]
        if teams is not None and teams == 1:
            return True
        return False

    # Check if teams enabled for this event
    def has_teams(self):
        teams = db.query_db('SELECT has_teams FROM events WHERE id = ?', [self.id], one=True)[0]
        if teams is not None and teams == 1:
            return True
        return False

    # Get Team given team_name in this event
    def get_team(self, team_slug):
        q = db.query_db('SELECT * FROM teams WHERE slug = ? AND event_id = ?', (team_slug, self.id), one=True)
        if q is None:
            return None
        return team.Team(q['name'], q['event_id'])

    # Add user to team in this event
    def add_user_to_team(self, user_id, team_slug):
        # Check team exists
        t = self.get_team(team_slug)
        if t is None:
            return False
        try:
            db.query_db('INSERT INTO teamusers (team_slug, event_id, user_id) VALUES (?, ?, ?)', (team_slug, self.id, user_id))
        except db.IntegrityError:
            return False
        return True

    # Get team from user_id in this event
    def get_users_team(self, user_id):
        q = db.query_db('''
            SELECT t.name AS name, t.event_id AS event_id
            FROM teams t
            LEFT JOIN teamusers tu ON t.slug = tu.team_slug AND t.event_id = tu.event_id
            WHERE tu.user_id = ?
            AND t.event_id = ?
        ''', (user_id, self.id), one=True)
        if q is None:
            return None
        return team.Team(q['name'], q['event_id'])

    # Get event individual leaderboard (from user leaderboard builder)
    def get_leaderboard(self, limit=None):
        q = '''
            SELECT u.username, u.displayname, SUM(f.value) AS score, COUNT(f.flag) as num_flags
            FROM flagsfound ff
            LEFT JOIN flags f ON f.flag = ff.flag_id
            LEFT JOIN users u ON u.username = ff.user_id
            WHERE f.event_id = ?
            GROUP BY u.username
            ORDER BY score DESC
        '''
        if limit is not None:  # Limit number of users returned
            return leaderboard.make_leaderboard(q + ' LIMIT ?', (self.id, limit))
        return leaderboard.make_leaderboard(q, [self.id])

    # Get team leaderboard (from team leaderboard builder)
    def get_team_leaderboard(self, limit=None):
        q = '''
            SELECT name, event_id, SUM(score) AS score, SUM(num_flags) as num_flags
            FROM (
                SELECT NULL as name, team_slug AS slug, event_id as event_id, SUM(value) AS score, COUNT(flag) as num_flags
                FROM (
                    SELECT DISTINCT flag, value, f.event_id, team_slug
                    FROM flagsfound ff
                    LEFT JOIN flags f ON f.flag = ff.flag_id
                    LEFT JOIN teamusers tu ON tu.event_id = f.event_id AND tu.user_id = ff.user_id
                    WHERE tu.event_id = ?
                )
                GROUP BY team_slug
                UNION
                SELECT name, slug, t.event_id as event_id, 0 AS score, 0 AS num_flags
                FROM teams t
                WHERE event_id = ?
            ) GROUP BY slug
            ORDER BY score DESC
        '''
        if limit is not None: # Limit number of teams returned
            return team.make_leaderboard(q + ' LIMIT ?', (self.id, self.id, limit))
        return team.make_leaderboard(q, (self.id, self.id))


# Check event exists given ID
def exists(id):
    if db.query_db('SELECT * FROM events WHERE id = ?', [id], one=True) is None:
        return False
    return True

# Get event from ID
def get_event(id):
    return make_event_from_row(db.query_db('''
        SELECT e.id AS id, e.name AS name
        FROM events e
        WHERE e.id = ?
    ''', [id], one=True))

# Create event
def create(id, name, teams, active):
    if (active is 1) and (get_active() is not None): # Deactive current active event
        db.query_db('UPDATE events SET active = 0 WHERE active = 1')
    # Insert new event
    db.query_db('''
        INSERT INTO events (id, name, has_teams, active)
        VALUES (?, ?, ?, ?)
    ''', (id, name, teams, active))
    logger.info("^%s^ added an event %d:'%s'.", flask_login.current_user.username, id, name)


# Update event
def update(id, name, teams, active):
    if (active is 1) and (get_active() is not None): # Deactive current active event
        db.query_db('UPDATE events SET active = 0 WHERE active = 1')
    # Update record
    db.query_db('''
        UPDATE events
        SET name = ?, has_teams = ?, active = ?
        WHERE id = ?
    ''', (name, teams, active, id))
    logger.info("^%s^ updated the %d:'%s' event.", flask_login.current_user.username, id, name)


# Delete event
def delete(id):
    event = get_event(id)
    db.query_db('''
        DELETE FROM events
        WHERE id = ?
    ''', [id])
    logger.info("^%s^ deleted event %d:'%s'.", flask_login.current_user.username, id, event.name)


#TODO Not happy with this being here, it ideally needs to be in user: u.get_events(), but this causes loop on event import.
# Get list of events attended by user (by looking at flags found)
def by_user(user_id):
    return make_list_from_query(db.query_db('''
        SELECT e.id AS id, e.name AS name
        FROM events e
        LEFT JOIN flags f ON f.event_id = e.id
        LEFT JOIN flagsfound ff ON ff.flag_id = f.flag
        LEFT JOIN users u ON u.username = ff.user_id
        WHERE u.username IS NOT NULL AND u.username = ?
        GROUP BY e.id
    ''', [user_id]))

# Get active event
def get_active():
    return make_event_from_row(db.query_db('SELECT * FROM events WHERE active = 1', one=True))

# Get all events
def get_all():
    return make_list_from_query(db.query_db('''
        SELECT e.id AS id, e.name AS name
        FROM events e
        ORDER BY e.id DESC
    '''))

# Make list of events from DB query result
def make_list_from_query(query):
    l = []
    if query is not None:
        for e in query:
            l.append(make_event_from_row(e))
    return l

# Make event object from DB row
def make_event_from_row(row):
    if row is None:
        return None
    return Event(row['id'], row['name'])
