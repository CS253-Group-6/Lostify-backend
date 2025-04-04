INSERT INTO users (id, username, password, role) VALUES
    (0, 'test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', 0),
    (1, 'other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79', 0);

INSERT INTO profiles (userid, name, phone, email, address, designation, roll) VALUES
    (0, 'test_name', '123', 'test@example.com', '10 Downing Street', 'Student', 23829)