CREATE TABLE IF NOT EXISTS users(
  username TEXT PRIMARY KEY,
  displayname TEXT NOT NULL,
  password TEXT NOT NULL,
  permission INTEGER
);
CREATE TABLE IF NOT EXISTS flags(
  flag TEXT PRIMARY KEY,
  hash TEXT NOT NULL,
  value INTEGER NOT NULL,
  event_id INTEGER REFERENCES events(id),
  notes TEXT,
  user TEXT REFERENCES users(username)
);
CREATE TABLE IF NOT EXISTS flagsfound(
  flag_id TEXT NOT NULL REFERENCES flags(flag),
  user_id TEXT NOT NULL REFERENCES users(username),
  timestamp TEXT,
  PRIMARY KEY (flag_id, user_id)
);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, name TEXT NOT NULL, active BOOLEAN, has_teams BOOLEAN);
CREATE TABLE IF NOT EXISTS teams(
  slug TEXT NOT NULL,
  name TEXT NOT NULL,
  event_id INTEGER REFERENCES events(id),
  PRIMARY KEY (slug, event_id)
);
CREATE TABLE IF NOT EXISTS teamusers(
  team_slug TEXT NOT NULL REFERENCES teams(slug),
  event_id INTEGER NOT NULL REFERENCES teams(event_id),
  user_id TEXT NOT NULL REFERENCES users(username),
  PRIMARY KEY (team_slug, event_id, user_id)
);
CREATE TABLE IF NOT EXISTS ranks(rank TEXT PRIMARY KEY, score INTEGER NOT NULL);
