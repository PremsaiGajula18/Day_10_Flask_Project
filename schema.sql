-- =============================================================================
-- Database Schema for Movie Night Planner (MySQL Edition)
-- =============================================================================
-- Description:
--   Creates the required MySQL database schema with relational tables,
--   foreign key constraints, cascade rules, and unique constraints.
--
-- How to run in MySQL CLI or MySQL Workbench:
--   mysql -u root -p < schema.sql
-- =============================================================================

-- Create the database if it does not already exist
CREATE DATABASE IF NOT EXISTS movie_night_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Select the database
USE movie_night_db;

-- -----------------------------------------------------------------------------
-- 1. Table: users
-- -----------------------------------------------------------------------------
-- Stores registered application users with securely hashed credentials.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. Table: movie_nights
-- -----------------------------------------------------------------------------
-- Represents each movie night event hosted by a user.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movie_nights (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    date DATE NOT NULL,
    category ENUM('Action', 'Comedy', 'Animation', 'Other') NOT NULL,
    description TEXT NOT NULL,
    creator_id INT NOT NULL,
    final_choice_id INT NULL,
    is_finalized TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_nights_creator FOREIGN KEY (creator_id) 
        REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. Table: movie_choices
-- -----------------------------------------------------------------------------
-- Nominated candidate films that attendees can vote on.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movie_choices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    movie_night_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    genre VARCHAR(80) NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_choices_night FOREIGN KEY (movie_night_id) 
        REFERENCES movie_nights(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add foreign key linking final_choice_id to movie_choices
ALTER TABLE movie_nights
    ADD CONSTRAINT fk_nights_final_choice
    FOREIGN KEY (final_choice_id) 
    REFERENCES movie_choices(id) ON DELETE SET NULL;

-- -----------------------------------------------------------------------------
-- 4. Table: votes
-- -----------------------------------------------------------------------------
-- Tracks attendee votes. Guarantees 1 vote per user per movie night via
-- the unique key `uk_user_night_vote`.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS votes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    movie_night_id INT NOT NULL,
    choice_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_night_vote (user_id, movie_night_id),
    CONSTRAINT fk_votes_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_votes_night FOREIGN KEY (movie_night_id) 
        REFERENCES movie_nights(id) ON DELETE CASCADE,
    CONSTRAINT fk_votes_choice FOREIGN KEY (choice_id) 
        REFERENCES movie_choices(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
