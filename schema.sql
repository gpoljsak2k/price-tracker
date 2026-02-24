PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS store (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS product (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  brand TEXT NOT NULL DEFAULT '',   ---tako mora biti
  UNIQUE(name, brand)
);

CREATE TABLE IF NOT EXISTS product_pack (
  id INTEGER PRIMARY KEY,
  product_id INTEGER NOT NULL,
  pack_size REAL NOT NULL CHECK (pack_size > 0),
  base_unit TEXT NOT NULL CHECK (base_unit IN ('g','kg','ml','l','pcs')),
  note TEXT NOT NULL DEFAULT '',        ---isto tukaj
  UNIQUE(product_id, pack_size, base_unit, note),
  FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS price_observation (
  id INTEGER PRIMARY KEY,
  store_id INTEGER NOT NULL,
  product_pack_id INTEGER NOT NULL,
  price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
  observed_on TEXT NOT NULL, -- YYYY-MM-DD
  source TEXT NOT NULL DEFAULT 'manual',
  UNIQUE(store_id, product_pack_id, observed_on),
  FOREIGN KEY (store_id) REFERENCES store(id) ON DELETE CASCADE,
  FOREIGN KEY (product_pack_id) REFERENCES product_pack(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_price_store_date ON price_observation(store_id, observed_on);
CREATE INDEX IF NOT EXISTS idx_price_pack_date ON price_observation(product_pack_id, observed_on);
