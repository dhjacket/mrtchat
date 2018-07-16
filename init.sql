
CREATE TABLE IF NOT EXISTS users (
	user_id SERIAL NOT NULL,
	login VARCHAR(150) NOT NULL,
	password VARCHAR(64) NOT NULL,
	PRIMARY KEY (user_id),
	UNIQUE (login)
);



CREATE TABLE IF NOT EXISTS chats (
	chat_id SERIAL NOT NULL,
	PRIMARY KEY (chat_id)
);



CREATE TABLE IF NOT EXISTS chat_users (
	chat_user_id SERIAL NOT NULL,
	chat_id INTEGER NOT NULL,
	user_id INTEGER NOT NULL,
	PRIMARY KEY (chat_user_id),
	FOREIGN KEY(chat_id) REFERENCES chats (chat_id),
	FOREIGN KEY(user_id) REFERENCES users (user_id)
);



CREATE TABLE IF NOT EXISTS messages (
	message_id SERIAL NOT NULL,
	text TEXT,
	user_id INTEGER NOT NULL,
	chat_id INTEGER,
	PRIMARY KEY (message_id),
	FOREIGN KEY(user_id) REFERENCES users (user_id),
	FOREIGN KEY(chat_id) REFERENCES chats (chat_id)
);


