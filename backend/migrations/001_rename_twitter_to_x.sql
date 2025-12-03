-- Migration: Rename Twitter to X
-- Date: 2025-12-03
-- Description: Renames twitter_connections table to x_connections and tweets table to x_posts
--              Also renames related columns to use X naming convention

-- ============================================
-- Step 1: Rename tables
-- ============================================

-- Rename twitter_connections to x_connections
ALTER TABLE IF EXISTS twitter_connections RENAME TO x_connections;

-- Rename tweets to x_posts
ALTER TABLE IF EXISTS tweets RENAME TO x_posts;

-- ============================================
-- Step 2: Rename columns in x_connections
-- ============================================

-- Rename twitter_user_id to x_user_id
ALTER TABLE x_connections RENAME COLUMN twitter_user_id TO x_user_id;

-- Rename tweet_count to post_count
ALTER TABLE x_connections RENAME COLUMN tweet_count TO post_count;

-- ============================================
-- Step 3: Rename columns in x_posts
-- ============================================

-- Rename tweet_id to post_id
ALTER TABLE x_posts RENAME COLUMN tweet_id TO post_id;

-- Rename created_at_twitter to created_at_x
ALTER TABLE x_posts RENAME COLUMN created_at_twitter TO created_at_x;

-- Rename retweet_count to repost_count
ALTER TABLE x_posts RENAME COLUMN retweet_count TO repost_count;

-- Rename referenced_tweets to referenced_posts (if exists)
ALTER TABLE x_posts RENAME COLUMN referenced_tweets TO referenced_posts;

-- ============================================
-- Step 4: Update foreign key constraints
-- ============================================

-- Update foreign key constraint on x_posts to reference x_connections
-- First drop the old constraint
ALTER TABLE x_posts DROP CONSTRAINT IF EXISTS tweets_connection_id_fkey;
ALTER TABLE x_posts DROP CONSTRAINT IF EXISTS fk_tweets_connection_id;

-- Add the new constraint with updated name
ALTER TABLE x_posts
ADD CONSTRAINT fk_x_posts_connection_id
FOREIGN KEY (connection_id) REFERENCES x_connections(id) ON DELETE CASCADE;

-- ============================================
-- Step 5: Update indexes (if needed)
-- ============================================

-- Drop old indexes
DROP INDEX IF EXISTS ix_twitter_connections_twitter_user_id;
DROP INDEX IF EXISTS ix_twitter_connections_user_id;
DROP INDEX IF EXISTS ix_tweets_tweet_id;
DROP INDEX IF EXISTS ix_tweets_connection_id;

-- Create new indexes with updated names
CREATE INDEX IF NOT EXISTS ix_x_connections_x_user_id ON x_connections(x_user_id);
CREATE INDEX IF NOT EXISTS ix_x_connections_user_id ON x_connections(user_id);
CREATE INDEX IF NOT EXISTS ix_x_posts_post_id ON x_posts(post_id);
CREATE INDEX IF NOT EXISTS ix_x_posts_connection_id ON x_posts(connection_id);

-- ============================================
-- Verification queries (optional)
-- ============================================
-- SELECT table_name FROM information_schema.tables WHERE table_name IN ('x_connections', 'x_posts');
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'x_connections';
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'x_posts';
