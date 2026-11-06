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

-- ---------------------------------------------------------------------
-- 2026-10-21 · Alertes : épisode d'anomalie d'une culture
-- Modèle : app/models/alert.py
-- ---------------------------------------------------------------------
ALTER TABLE alert ADD COLUMN IF NOT EXISTS crop_id INTEGER REFERENCES crop(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS ix_alert_crop_id ON alert (crop_id);
ALTER TABLE alert ADD COLUMN IF NOT EXISTS cause VARCHAR(200);
ALTER TABLE alert ADD COLUMN IF NOT EXISTS evidence TEXT;
ALTER TABLE alert ADD COLUMN IF NOT EXISTS action TEXT;
ALTER TABLE alert ADD COLUMN IF NOT EXISTS valid_ratio DOUBLE PRECISION;
ALTER TABLE alert ADD COLUMN IF NOT EXISTS first_scene_date DATE;
ALTER TABLE alert ADD COLUMN IF NOT EXISTS last_scene_date DATE;
ALTER TABLE alert ADD COLUMN IF NOT EXISTS resolution VARCHAR(20);
ALTER TABLE alert ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE alert ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now();

-- ---------------------------------------------------------------------
-- 2026-10-22 · Employés : chaque employé appartient à un compte
-- Modèle : app/models/employee.py
-- ---------------------------------------------------------------------
ALTER TABLE employee ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES utilisateur(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS ix_employee_user_id ON employee (user_id);

-- Employés déjà rattachés à une ferme : propriétaire de la ferme
UPDATE employee e
SET user_id = f.user_id
FROM farm_employee fe
JOIN farm f ON f.id = fe.farm_id
WHERE fe.employee_id = e.id AND e.user_id IS NULL;

-- Employés sans aucune ferme : rattachés à ton compte
UPDATE employee
SET user_id = (SELECT id FROM utilisateur WHERE email = 'yasmine4klai48@gmail.com')
WHERE user_id IS NULL;

-- ---------------------------------------------------------------------
-- 2026-10-22 · Équipes : l'équipe d'un employé dans chaque ferme
-- Modèle : app/models/farm_employee.py
-- ---------------------------------------------------------------------
ALTER TABLE farm_employee ADD COLUMN IF NOT EXISTS team VARCHAR(60);

-- 2026-10-23 · Les types de tâche personnalisés n'ont plus de table : ils
-- vivent dans activity.activity_type et farm_employee.team.
DROP TABLE IF EXISTS task_type;

-- ---------------------------------------------------------------------
-- 2026-10-23 · Employé inactif, dans toutes ses fermes
-- Modèle : app/models/employee.py
-- ---------------------------------------------------------------------
ALTER TABLE employee ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- ---------------------------------------------------------------------
-- 2026-10-23 · Planification : état, date prévue, équipe et tâches attachées
-- Modèle : app/models/activity.py
-- ---------------------------------------------------------------------
ALTER TABLE activity ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'realisee';
ALTER TABLE activity ADD COLUMN IF NOT EXISTS planned_for DATE;
ALTER TABLE activity ALTER COLUMN performed_at DROP NOT NULL;
ALTER TABLE activity ALTER COLUMN performed_at DROP DEFAULT;
ALTER TABLE activity ADD COLUMN IF NOT EXISTS team VARCHAR(60);
ALTER TABLE activity ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES activity(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS ix_activity_parent_id ON activity (parent_id);
-- ---------------------------------------------------------------------
-- 2026-10-27 · Suppression en cascade des activités
-- Modèle : app/models/activity.py
--   - supprimer une parcelle supprime ses activités ;
--   - supprimer une activité supprime ses liens avec les employés ;
--   - supprimer un employé supprime ses liens avec les activités
--     (les activités elles-mêmes restent).
-- Chaque clé est retrouvée par son nom réel, supprimée, puis recréée avec
-- ON DELETE CASCADE : le bloc peut être relancé sans risque.
-- ---------------------------------------------------------------------
DO $$
DECLARE
  cible record;
  nom text;
BEGIN
  FOR cible IN
    SELECT * FROM (VALUES
      ('activity',          'parcel_id',   'parcel',   'activity_parcel_id_fkey'),
      ('activity_employee', 'activity_id', 'activity', 'activity_employee_activity_id_fkey'),
      ('activity_employee', 'employee_id', 'employee', 'activity_employee_employee_id_fkey')
    ) AS t(tbl, col, ref, cle)
  LOOP
    FOR nom IN
      SELECT con.conname
      FROM pg_constraint con
      JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = ANY (con.conkey)
      WHERE con.conrelid = cible.tbl::regclass AND con.contype = 'f' AND att.attname = cible.col
    LOOP
      EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', cible.tbl, nom);
    END LOOP;
    EXECUTE format(
      'ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %I(id) ON DELETE CASCADE',
      cible.tbl, cible.cle, cible.col, cible.ref
    );
  END LOOP;
END $$;


-- 2026-10-29 · Heure prévue des tâches (facultative)
ALTER TABLE activity ADD COLUMN IF NOT EXISTS planned_time TIME;

-- =====================================================================
-- 2026-11-04 · Irrigation : arrosages
-- Modèle : app/models/irrigation_watering.py
-- Un arrosage est une tâche (activity) de type « irrigation » ; cette table
-- garde ses détails d'eau : équipement, façon de mesurer, quantité. Une
-- ligne par tâche, supprimée avec elle. Le bloc peut être relancé sans risque.
-- =====================================================================
CREATE TABLE IF NOT EXISTS irrigation_watering (
    id               SERIAL PRIMARY KEY,
    activity_id      INTEGER NOT NULL UNIQUE REFERENCES activity(id) ON DELETE CASCADE,
    -- Équipement utilisé ; vide s'il a été supprimé depuis (le volume reste)
    equipment_id     INTEGER REFERENCES irrigation_equipment(id) ON DELETE SET NULL,
    -- arrosoirs | duree | compteur | volume
    method           VARCHAR(20) NOT NULL,
    can_count        INTEGER,
    start_time       TIME,
    end_time         TIME,
    duration_min     DOUBLE PRECISION,
    meter_volume_l   DOUBLE PRECISION,
    -- Volume d'eau apporté (L), calculé à l'enregistrement
    volume_l         DOUBLE PRECISION,
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at       TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT ck_irrigation_watering_method CHECK (method IN ('arrosoirs', 'duree', 'compteur', 'volume')),
    CONSTRAINT ck_irrigation_watering_positive CHECK (
        (can_count IS NULL OR can_count > 0)
        AND (duration_min IS NULL OR duration_min > 0)
        AND (meter_volume_l IS NULL OR meter_volume_l > 0)
        AND (volume_l IS NULL OR volume_l >= 0)
    )
);
CREATE INDEX IF NOT EXISTS ix_irrigation_watering_equipment_id ON irrigation_watering (equipment_id);
-- =====================================================================
-- 2026-11-06 · Climat et cultures · Étape 1 : les données
--   1. weather_daily : 3 paramètres de plus, chaque jour depuis 2020 ;
--   2. weather_forecast : les prévisions des prochains jours, à part,
--      pour ne jamais mélanger des jours futurs avec le climat réel.
-- Le bloc peut être relancé sans risque.
-- =====================================================================
ALTER TABLE weather_daily ADD COLUMN IF NOT EXISTS temperature_mean_c DOUBLE PRECISION;
ALTER TABLE weather_daily ADD COLUMN IF NOT EXISTS humidity_mean_pct DOUBLE PRECISION;
ALTER TABLE weather_daily ADD COLUMN IF NOT EXISTS wind_speed_mean_kmh DOUBLE PRECISION;

CREATE TABLE IF NOT EXISTS weather_forecast (
    id                  SERIAL PRIMARY KEY,
    farm_id             INTEGER NOT NULL REFERENCES farm(id) ON DELETE CASCADE,
    day                 DATE NOT NULL,
    temperature_min_c   DOUBLE PRECISION,
    temperature_max_c   DOUBLE PRECISION,
    temperature_mean_c  DOUBLE PRECISION,
    precipitation_mm    DOUBLE PRECISION,
    et0_mm              DOUBLE PRECISION,
    wind_speed_max_kmh  DOUBLE PRECISION,
    wind_speed_mean_kmh DOUBLE PRECISION,
    humidity_mean_pct   DOUBLE PRECISION,
    radiation_mj_m2     DOUBLE PRECISION,
    fetched_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_weather_forecast_farm_day UNIQUE (farm_id, day)
);
CREATE INDEX IF NOT EXISTS ix_weather_forecast_farm ON weather_forecast (farm_id);