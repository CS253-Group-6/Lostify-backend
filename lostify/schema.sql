PRAGMA foreign_keys = ON;

-- Order matters. The tables with the least foreign key dependencies
-- should be deleted first.
DROP TABLE IF EXISTS awaitOTP;
DROP TABLE IF EXISTS profiles;
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS confirmations;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS users;

-- Table of users awaiting OTP
CREATE TABLE awaitOTP (
    username    TEXT PRIMARY KEY NOT NULL,          -- The email address is then username@iitk.ac.in
    password    TEXT NOT NULL,
    otp         INTEGER NOT NULL,                   -- The OTP sent to username@iitk.ac.in
    created     INTEGER NOT NULL,                   -- Time of generation of OTP (Unix timestamp)
    profile     TEXT NOT NULL                       -- Profile details as JSON
) WITHOUT ROWID, STRICT;

-- Table of registered users
CREATE TABLE users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,               -- The email address is then username@iitk.ac.in
    password    TEXT NOT NULL,
    role        INTEGER NOT NULL,                   -- 0 for normal user, 1 for admin
    counter     INTEGER NOT NULL DEFAULT 0,         -- Number of failed login attempts
    lastAttempt INTEGER DEFAULT 0                   -- Time of last unsuccessful login attempt (Unix timestamp)
) STRICT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users (username);

-- Table of profile details
CREATE TABLE profiles (
    userid      INTEGER PRIMARY KEY,                -- The user id of the user in users table
    name        TEXT NOT NULL,
    phone       TEXT,
    email       TEXT,
    address     TEXT,
    designation TEXT,
    roll        INTEGER UNIQUE NOT NULL,            -- Roll number of the user
    image       BLOB,
    playerId    TEXT,                               -- Token for push notifications
    online      INTEGER NOT NULL,                   -- 0 for offline, 1 for online
    FOREIGN KEY (userid) REFERENCES users (id) ON DELETE CASCADE
) STRICT;

-- Table of posts
CREATE TABLE posts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        INTEGER NOT NULL,           -- 0 for lost, 1 for found
    creator     INTEGER NOT NULL,           -- User id of the post creator
    title       TEXT NOT NULL,              -- Post title
    description TEXT,                       -- Post description
    location1   TEXT NOT NULL,              -- Coarse location of find/loss
    location2   TEXT,                       -- Fine location of find/loss
    image       BLOB,                       -- Image of post
    date        INTEGER NOT NULL,           -- Date of loss/find
    closedBy    INTEGER,                    -- User id of claimant
    closedDate  INTEGER,                    -- Date of closing post
    reportCount INTEGER NOT NULL DEFAULT 0, -- Count of reports
    FOREIGN KEY (creator) REFERENCES users (id),
    FOREIGN KEY (closedBy) REFERENCES users (id)
) STRICT;

-- Table of reported posts
CREATE TABLE reports (
    postid    INTEGER NOT NULL,             -- Id of the post
    userid    INTEGER NOT NULL,             -- User id of the reporter
    PRIMARY KEY (postid, userid),
    FOREIGN KEY (postid) REFERENCES posts (id) ON DELETE CASCADE,
    FOREIGN KEY (userid) REFERENCES users (id)
) WITHOUT ROWID, STRICT;

-- Table of post confirmations
CREATE TABLE confirmations (
    postid    INTEGER NOT NULL,             -- Id of the post
    initid    INTEGER NOT NULL,             -- User id of the initiator
    otherid   INTEGER NOT NULL,             -- User id of the user yet to confirm
    PRIMARY KEY (postid, initid) ON CONFLICT REPLACE,
    FOREIGN KEY (postid) REFERENCES posts (id) ON DELETE CASCADE,
    FOREIGN KEY (initid) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (otherid) REFERENCES users (id) ON DELETE CASCADE
) WITHOUT ROWID, STRICT;
