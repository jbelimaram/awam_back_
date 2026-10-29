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