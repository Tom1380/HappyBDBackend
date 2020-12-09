CREATE TABLE users (
	id SERIAL,
	username TEXT NOT NULL UNIQUE,
	hashed_password BYTEA NOT NULL,
	default_wisher_displayed_name TEXT NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE targets (
	name TEXT NOT NULL,
	username TEXT NOT NULL,
	birthday date NOT NULL,
	-- If it's not null, then we never tweeted for them.
	last_wish_year INTEGER,
	-- If it's not null, then we use the default_wisher_displayed_name.
	wisher_displayed_name TEXT,
	wisher_id INTEGER NOT NULL REFERENCES users (id),
	PRIMARY KEY (username)
);