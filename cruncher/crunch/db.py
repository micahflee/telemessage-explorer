import os
import sys

import psycopg2

conn_params = {
    "dbname": os.environ.get("DB_NAME"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "host": os.environ.get("DB_HOST"),
    "port": os.environ.get("DB_PORT"),
}


def connect_db():
    try:
        conn = psycopg2.connect(**conn_params)
        print("Connected to the database")
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        sys.exit(1)


def create_tables(conn):
    try:
        with conn.cursor() as cursor:
            # an unknown object
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemessage_unknown (
                    id SERIAL PRIMARY KEY,
                    obj JSONB NOT NULL,
                    checksum TEXT UNIQUE,
                    filename TEXT
                )
            """)

            # a text message/chat log
            # obj_type is:
            # - "raw" is a RawMessage
            # - "raw_body" is the body of a "RawMessage"
            # - "short" is a short message
            # - "tmobile" is a TMobile message
            # - "tmobile_body" is the body of a TMobile message
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemessage_messages (
                    id SERIAL PRIMARY KEY,
                    obj JSONB NOT NULL,
                    checksum TEXT UNIQUE,
                    obj_type TEXT NOT NULL,
                    is_encrypted BOOLEAN DEFAULT FALSE,
                    has_attachments BOOLEAN DEFAULT FALSE,
                    subject TEXT,
                    text TEXT,
                    direction TEXT,
                    sender_user_id TEXT,
                    recipients_count INT,
                    group_name TEXT,
                    network_type TEXT,
                    source_type TEXT,
                    message_time BIGINT
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_checksum
                ON telemessage_messages (checksum);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_message_network_type
                ON telemessage_messages (network_type);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_message_source_type
                ON telemessage_messages (source_type);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_text
                ON telemessage_messages (text);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_obj_body_message_time
                ON telemessage_messages (message_time);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_obj_body_owner_value
                ON telemessage_messages USING GIN ((obj->'body'->'owner'->'value') jsonb_path_ops);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_obj_body_sender_value
                ON telemessage_messages USING GIN ((obj->'body'->'sender'->'value') jsonb_path_ops);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_obj_body_recipients_value
                ON telemessage_messages USING GIN (
                    (jsonb_path_query_array(obj->'body'->'recipients', '$[*].value'))
                );
            """)

            # an attachment
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemessage_attachments (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    content TEXT,
                    attach_size TEXT,
                    content_type TEXT,
                    message_id INT REFERENCES telemessage_messages(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_name
                ON telemessage_attachments (name);
            """)

            # a user
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemessage_users (
                    id SERIAL PRIMARY KEY,
                    type TEXT,
                    value TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    notes TEXT,
                    UNIQUE (type, value)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_value
                ON telemessage_users (value);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_first_name
                ON telemessage_users (first_name);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_last_name
                ON telemessage_users (last_name);
            """)

            # a group chat
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemessage_groups (
                    id SERIAL PRIMARY KEY,
                    group_name TEXT,
                    source_type TEXT,
                    network_type TEXT,
                    notes TEXT,
                    UNIQUE (group_name, source_type, network_type)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_groups_group_name
                ON telemessage_groups (group_name);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_groups_source_type
                ON telemessage_groups (source_type);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_groups_network_type
                ON telemessage_groups (network_type);
            """)

            # join table for users and groups
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemessage_users_groups (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES telemessage_users(id) ON DELETE CASCADE,
                    group_id INT REFERENCES telemessage_groups(id) ON DELETE CASCADE,
                    UNIQUE (user_id, group_id)
                )
            """)

            # join table for users and messages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemessage_users_messages (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES telemessage_users(id) ON DELETE CASCADE,
                    message_id INT REFERENCES telemessage_messages(id) ON DELETE CASCADE,
                    UNIQUE (user_id, message_id)
                )
            """)

            # join table for groups and messages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemessage_groups_messages (
                    id SERIAL PRIMARY KEY,
                    group_id INT REFERENCES telemessage_groups(id) ON DELETE CASCADE,
                    message_id INT REFERENCES telemessage_messages(id) ON DELETE CASCADE,
                    UNIQUE (group_id, message_id)
                )
            """)

            # credentials
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemessage_credentials (
                    id SERIAL PRIMARY KEY,
                    obj JSONB,
                    checksum TEXT UNIQUE,
                    username TEXT,
                    password TEXT
                )
            """)

            # validation objects
            # obj_type is:
            # - "full" is a RawMessage
            # - "enhancementData"
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemessage_validations (
                    id SERIAL PRIMARY KEY,
                    obj JSONB,
                    checksum TEXT UNIQUE,
                    obj_type TEXT NOT NULL,
                    username TEXT,
                    email TEXT,
                    email_domain TEXT,
                    active_identity_provider TEXT
                )
            """)
            conn.commit()
            print("Tables created successfully")
    except Exception as e:
        print(f"Error creating table: {e}")
        return

    return conn


def close_db(conn):
    try:
        conn.close()
        print("Database connection closed")
    except Exception as e:
        print(f"Error closing database connection: {e}")
