import psycopg2
from werkzeug.security import generate_password_hash

from config import DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD


if __name__ == "__main__":

    conn = psycopg2.connect(database="postgres", host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD)
    cur = conn.cursor()
    conn.autocommit = True

    cur.execute(f"SELECT datname FROM pg_database WHERE datname = '{DB_NAME}';")
    res = cur.fetchone()
    if not res:
        print(f"--- Create database: {DB_NAME}")
        cur.execute(f"CREATE DATABASE {DB_NAME};")

    cur.close()
    conn.close()

    conn = psycopg2.connect(database=DB_NAME, host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD)
    cur = conn.cursor()

    print("--- Activate PostGIS")
    cur.execute(f"CREATE EXTENSION IF NOT EXISTS postgis;")

    # print("--- Drop tables if exist: users, networks, maps, features")
    # cur.execute(f'DROP TABLE IF EXISTS users CASCADE;')
    # cur.execute(f'DROP TABLE IF EXISTS networks CASCADE;')
    # cur.execute(f'DROP TABLE IF EXISTS maps CASCADE;')
    # cur.execute(f'DROP TABLE IF EXISTS features CASCADE;')
    conn.commit()

    print("--- Create tables: users, networks, maps, features")
    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(32) NOT NULL UNIQUE,
            password_hash VARCHAR(192) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        ); 
    ''')

    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS networks (
            id SERIAL PRIMARY KEY,
            name VARCHAR(128) NOT NULL UNIQUE,
            owner_id INTEGER REFERENCES users(id),
            latest_version INTEGER NOT NULL DEFAULT 1,
            public BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        );
    ''')

    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS maps (
            id SERIAL PRIMARY KEY,
            network_id INTEGER REFERENCES networks(id) ON DELETE CASCADE,
            version INTEGER NOT NULL DEFAULT 1,
            type VARCHAR(32),
            name VARCHAR(128),
            crs JSONB,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        );
    ''')

    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS features (
            id SERIAL PRIMARY KEY,
            map_id INTEGER REFERENCES maps(id) ON DELETE CASCADE,
            type VARCHAR(32),
            props JSONB,
            geom geometry(GEOMETRY, 4326)
        );
    ''')

    conn.commit()

    print("--- Create admin user (admin:admin)")
    cur.execute(f'''
        INSERT INTO users (username, password_hash, is_admin)
        VALUES ('admin', '{generate_password_hash('admin')}', TRUE)
        ON CONFLICT (username) DO NOTHING;
    ''')
    conn.commit()
    print("----- Done")
    cur.close()
    conn.close()
