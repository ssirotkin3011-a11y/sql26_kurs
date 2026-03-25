CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL
);

CREATE TABLE words (
    id SERIAL PRIMARY KEY,
    en_word VARCHAR(100),
    ru_word VARCHAR(100)
);

CREATE TABLE user_words (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    en_word VARCHAR(100),
    ru_word VARCHAR(100)
);

CREATE TABLE deleted_words (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    word_id INTEGER REFERENCES words(id)
);
