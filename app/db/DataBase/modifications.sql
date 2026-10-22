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
SET user_id = (SELECT id FROM utilisateur WHERE email = 'TON_EMAIL')
WHERE user_id IS NULL;