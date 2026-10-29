from pydantic import BaseModel


class TaskTypeResponse(BaseModel):
    """Un type de tâche, prédéfini ou personnalisé, tel qu'affiché."""

    #: Toujours vide : les types n'ont plus de table dédiée (champ gardé
    #: pour le front, qui l'attend)
    id: None = None
    #: Valeur enregistrée dans activity.activity_type et farm_employee.team
    code: str
    label: str
    predefined: bool