CREATE TABLE IF NOT EXISTS `blacklist` (
  `user_id` varchar(20) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `warns` (
  `id` int(11) NOT NULL,
  `user_id` varchar(20) NOT NULL,
  `server_id` varchar(20) NOT NULL,
  `moderator_id` varchar(20) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `channels` (
    `server_id` varchar(20) NOT NULL,
    `channel_id` varchar(20) NOT NULL,
    CONSTRAINT channels_pk PRIMARY KEY (server_id)
);

CREATE TABLE IF NOT EXISTS `boss_kills` (
    `boss_name` varchar(20) NOT NULL,
    `last_killed` timestamp NOT NULL,
    CONSTRAINT boss_kills_pk PRIMARY KEY (boss_name)
);