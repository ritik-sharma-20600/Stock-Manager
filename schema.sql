CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, cash NUMERIC NOT NULL DEFAULT 10000.00);
CREATE TABLE sqlite_sequence(name,seq);
CREATE UNIQUE INDEX username ON users (username);
CREATE TABLE transactions (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, symbol TEXT NOT NULL, shares INTEGER NOT NULL, time TEXT NOT NULL);
CREATE UNIQUE INDEX trans_id_index ON transactions (id);
CREATE INDEX trans_user_index ON transactions (username);
CREATE TABLE stocks(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, symbol TEXT NOT NULL, shares INTEGER NOT NULL);
CREATE INDEX stocks_user_index ON stocks (username);
