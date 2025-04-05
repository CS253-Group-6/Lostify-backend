INSERT INTO users (id, username, password, role) VALUES
    (0, 'test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', 0),
    (1, 'other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79', 1);

INSERT INTO profiles (userid, name, phone, email, address, designation, roll) VALUES
    (0, 'test_name', '123', 'test@example.com', '10 Downing Street', 'Student', 23829),
    (1, 'other_name', '456', 'other@example.com', '221 Baker Street', 'Faculty', 21355);

INSERT INTO posts (id, type, title, description, location1, creator, date) VALUES
    (0, 0, 'Test Post', 'This is a test post.', 'a', 0, 1743769999),
    (1, 1, 'Another Post', 'This is another post.', 'b', 0, 1743772944),
    (2, 0, 'Third Post', 'This is the third post.', 'c', 0, 1743777392),
    (3, 1, 'Fourth Post', 'This is the fourth post.', 'd', 0, 1743779232),
    (4, 0, 'Fifth Post', 'This is the fifth post.', 'e', 0, 1743779233),
    (5, 1, 'Sixth Post', 'This is the sixth post.', 'f', 1, 1743780123),
    (6, 0, 'Seventh Post', 'This is the seventh post.', 'g', 1, 1743781233),
    (7, 1, 'Eighth Post', 'This is the eighth post.', 'h', 1, 1743782123),
    (8, 0, 'Ninth Post', 'This is the ninth post.', 'i', 1, 1743782212),
    (9, 0, 'Tenth Post', 'This is the tenth post.', 'j', 1, 1743782268);

UPDATE posts SET reportCount = 18 WHERE id = 3;
UPDATE posts SET reportCount = 5 WHERE id = 4;