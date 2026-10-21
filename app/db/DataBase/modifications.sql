-- =====================================================================
-- Modifications de la base AWAM, faites à la main (ALTER TABLE)
-- =====================================================================
-- Alembic n'est plus utilisé depuis le 08/10/2026. Chaque changement d'un
-- modèle (app/models/) est noté ici, avec sa date et sa raison, et envoyé
-- sur GitHub avec le code.
--
-- Ce fichier peut être relancé sans risque : grâce à IF NOT EXISTS, les
-- colonnes déjà présentes sont ignorées.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 2026-10-12 · Production réelle d'une culture récoltée
-- Modèle : app/models/crop.py
-- ---------------------------------------------------------------------
ALTER TABLE crop ADD COLUMN IF NOT EXISTS actual_yield DOUBLE PRECISION;
ALTER TABLE crop ADD COLUMN IF NOT EXISTS yield_unit VARCHAR(10);


-- ---------------------------------------------------------------------
-- 2026-10-20 · Date de fin d'une culture « Terminée » (fin de vie)
-- Modèle : app/models/crop.py
-- ---------------------------------------------------------------------
ALTER TABLE crop ADD COLUMN IF NOT EXISTS end_date DATE;