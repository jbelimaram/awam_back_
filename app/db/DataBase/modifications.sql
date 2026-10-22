-- =====================================================================
-- Modifications de la base AWAM, faites à la main (ALTER TABLE)
-- =====================================================================
-- Alembic n'est plus utilisé depuis le 08/10/2026. Chaque changement d'un
-- modèle (app/models/) est noté ici, avec sa date et sa raison, et envoyé
-- sur GitHub avec le code.
--
-- À EXÉCUTER EN ENTIER sur la base de CHAQUE machine, après chaque
-- récupération du code. Il peut être relancé sans risque : grâce à
-- IF NOT EXISTS, ce qui existe déjà est ignoré.
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

-- Employés sans aucune ferme : rattachés au compte ci-dessous
-- ⚠ Remplacer TON_EMAIL par l'adresse de ton compte AWAM avant d'exécuter
UPDATE employee
SET user_id = (SELECT id FROM utilisateur WHERE email = 'TON_EMAIL')
WHERE user_id IS NULL;

-- ---------------------------------------------------------------------
-- 2026-10-22 · Équipes : l'équipe d'un employé dans chaque ferme,
--              et les types de tâche libres de chaque compte
-- Modèles : app/models/farm_employee.py, app/models/task_type.py
-- ---------------------------------------------------------------------
ALTER TABLE farm_employee ADD COLUMN IF NOT EXISTS team VARCHAR(60);

CREATE TABLE IF NOT EXISTS task_type (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    name VARCHAR(60) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT uq_task_type_user_name UNIQUE (user_id, name)
);
CREATE INDEX IF NOT EXISTS ix_task_type_user_id ON task_type (user_id);