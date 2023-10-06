-- Create role types enum
CREATE TYPE role_types AS ENUM ('ADMIN', 'USER', 'PAID_USER');

-- Create the users table without foreign key for profile_pic
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  email TEXT NOT NULL,
  username TEXT NOT NULL,
  password TEXT NOT NULL,
  profile_pic INTEGER,
  role role_types
);

-- Create the conversions table
CREATE TABLE conversions (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  user_id INTEGER NOT NULL,
  user_parameters JSON
);

-- Create the file_conversions table
CREATE TABLE file_conversions (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  conversion_id INTEGER NOT NULL,
  input_file_id INTEGER NOT NULL,
  output_file_id INTEGER NOT NULL
);

-- Create the files table without foreign key for user_id
CREATE TABLE files (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  user_id INTEGER,
  path TEXT NOT NULL,
  type TEXT NOT NULL
);

-- Create the transactions table
CREATE TABLE transactions (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  user_id INTEGER NOT NULL,
  amount INTEGER
);

-- Now add foreign key constraints
ALTER TABLE conversions ADD FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE file_conversions ADD FOREIGN KEY (conversion_id) REFERENCES conversions(id);
ALTER TABLE file_conversions ADD FOREIGN KEY (input_file_id) REFERENCES files(id);
ALTER TABLE file_conversions ADD FOREIGN KEY (output_file_id) REFERENCES files(id);
ALTER TABLE transactions ADD FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE files ADD FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE users ADD FOREIGN KEY (profile_pic) REFERENCES files(id);
