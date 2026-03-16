CREATE TABLE IF NOT EXISTS dishes (
    id SERIAL PRIMARY KEY,
    category TEXT,
    name TEXT,
    price DECIMAL(10, 2),
    calories DECIMAL (10, 2),
    picture_id TEXT,
    is_in_storage BOOLEAN
);

