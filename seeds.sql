-- =============================================================================
-- Sample Seeds for Movie Night Planner (MySQL Edition)
-- =============================================================================
-- Password for all sample users ('alex', 'sarah', 'marcus') is: password123
-- =============================================================================

USE movie_night_db;

-- 1. Insert Sample Users
INSERT INTO users (id, name, username, password_hash) VALUES
(1, 'Alex Rivera', 'alex', 'scrypt:32768:8:1$WqSdDQk93Kgo0ubi$b7cbbe7177f26110608897d229f59f2c8dd2016aaf7bafd8f22a79f182502a4d1f7af24eab0e7afbd1ac31a184d38002b3f7dadaa780423f37b84de015cc28b4'),
(2, 'Sarah Chen', 'sarah', 'scrypt:32768:8:1$WqSdDQk93Kgo0ubi$b7cbbe7177f26110608897d229f59f2c8dd2016aaf7bafd8f22a79f182502a4d1f7af24eab0e7afbd1ac31a184d38002b3f7dadaa780423f37b84de015cc28b4'),
(3, 'Marcus Brody', 'marcus', 'scrypt:32768:8:1$WqSdDQk93Kgo0ubi$b7cbbe7177f26110608897d229f59f2c8dd2016aaf7bafd8f22a79f182502a4d1f7af24eab0e7afbd1ac31a184d38002b3f7dadaa780423f37b84de015cc28b4')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 2. Insert Sample Movie Nights
INSERT INTO movie_nights (id, title, date, category, description, creator_id, final_choice_id, is_finalized) VALUES
(1, '90s Sci-Fi & Action Spectacular', '2026-10-17', 'Action', 'Grab the popcorn and strap in! We are having an adrenaline-filled marathon celebrating the golden age of practical effects, cyberpunk philosophy, and legendary synth soundtracks.', 1, NULL, 0),
(2, 'Laugh Riot: Nostalgic Comedy Night', '2026-10-24', 'Comedy', 'After a long working week, we need pure laughs, hilarious one-liners, and comfort cinema. Bring your favorite snacks and vote for the funniest pick!', 2, NULL, 0),
(3, 'Studio Ghibli & Visual Masterpieces', '2026-10-11', 'Animation', 'A cozy evening dedicated to breathtaking hand-drawn and stylized animation. The votes are in and our winner has been crowned!', 1, 7, 1),
(4, 'Spooky Indie Thrillers & Whodunits', '2026-10-31', 'Other', 'Halloween special! Mystery, suspense, high tension, and unexpected plot twists to keep everyone on the edge of their seats.', 3, NULL, 0)
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- 3. Insert Movie Choices
INSERT INTO movie_choices (id, movie_night_id, title, genre, reason) VALUES
(1, 1, 'The Matrix (1999)', 'Sci-Fi / Cyberpunk', 'Mind-bending action choreography and revolutionary bullet-time visual effects that defined a generation.'),
(2, 1, 'Terminator 2: Judgment Day (1991)', 'Action / Sci-Fi', 'Peak James Cameron storytelling, unmatched truck chases, and ground-breaking liquid metal CGI.'),
(3, 1, 'Jurassic Park (1993)', 'Adventure / Sci-Fi', 'Spielberg masterpiece that will make you feel the ground shake when the T-Rex roars.'),

(4, 2, 'The Big Lebowski (1998)', 'Comedy / Crime', 'The Dude abides. Unforgettable dialogue, bowling shenanigans, and quirky dream sequences.'),
(5, 2, 'Superbad (2007)', 'Coming-of-Age Comedy', 'Endlessly quotable high school comedy with McLovins legendary adventure.'),
(6, 2, 'Ferris Buellers Day Off (1986)', 'Classic Teen Comedy', 'Life moves pretty fast. A timeless celebration of breaking rules and seizing the day.'),

(7, 3, 'Spirited Away (2001)', 'Animation / Fantasy', 'Hayao Miyazakis Oscar-winning fantasy journey into a spirit realm bathhouse.'),
(8, 3, 'Spider-Man: Into the Spider-Verse (2018)', 'Superhero / Stylized Animation', 'Revolutionary comic-book art style and an incredible hip-hop soundtrack.'),
(9, 3, 'WALL-E (2008)', 'Sci-Fi / Animation', 'Pixars poignant, virtually wordless romantic eco-adventure in space.'),

(10, 4, 'Knives Out (2019)', 'Mystery / Comedy Drama', 'Benoit Blanc unravels a wealthy familys eccentric murder mystery with wit and style.'),
(11, 4, 'Get Out (2017)', 'Psychological Horror / Thriller', 'Jordan Peeles masterclass in suspense, tension, and social commentary.'),
(12, 4, 'Parasite (2019)', 'Thriller / Black Comedy', 'Bong Joon-hos historic Palme dOr and Best Picture winner about class and deception.')
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- Update final_choice_id for Night 3
UPDATE movie_nights SET final_choice_id = 7, is_finalized = 1 WHERE id = 3;

-- 4. Insert Votes
INSERT INTO votes (user_id, movie_night_id, choice_id) VALUES
(1, 1, 1),
(2, 1, 2),
(3, 1, 1),
(2, 2, 4),
(1, 2, 5),
(1, 3, 7),
(2, 3, 7),
(3, 3, 8),
(3, 4, 10)
ON DUPLICATE KEY UPDATE choice_id=VALUES(choice_id);
