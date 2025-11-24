-- test.sql
DROP TABLE IF EXISTS questions;

CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL
);

INSERT INTO questions (question, answer) VALUES
("What is the capital of Taiwan?", "Taipei"),
("What year was NTUST founded?", "1974"),
("What is NTUST also known as?", "Taiwan Tech"),
("What is the motto of NTUST?", "Strength, Perseverance, Practicality, Innovation"),
("What city is NTUST located in?", "Taipei City");
