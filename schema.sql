-- Base des demandes d'inscription (Cloudflare D1)
--
-- Création :
--   npx wrangler d1 create educazur-demandes
--   npx wrangler d1 execute educazur-demandes --remote --file=schema.sql

CREATE TABLE IF NOT EXISTS demandes (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  recu_le   TEXT    NOT NULL,          -- horodatage ISO 8601 (UTC)
  parent    TEXT    NOT NULL,
  telephone TEXT    NOT NULL,
  email     TEXT,
  eleve     TEXT,
  niveau    TEXT    NOT NULL,
  message   TEXT,
  traite    INTEGER NOT NULL DEFAULT 0,
  -- empreinte de l'adresse IP, jamais l'adresse elle-même : sert uniquement
  -- à limiter les envois répétés
  ip_hash   TEXT
);

CREATE INDEX IF NOT EXISTS idx_demandes_recu ON demandes (recu_le DESC);
CREATE INDEX IF NOT EXISTS idx_demandes_ip   ON demandes (ip_hash, recu_le);
