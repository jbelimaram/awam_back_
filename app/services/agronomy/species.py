"""
Espèces cultivées référencées.

Une espèce porte son type (pérenne ou annuelle) et la liste ordonnée de
ses stades. C'est le point d'entrée du référentiel : calendrier, seuils,
Kc et références de sol sont tous indexés sur ces codes.

Les stades suivent la nomenclature du document agronomique AWAM.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CropType(str, Enum):
    """
    Pérenne  : le couvert persiste ou revient d'une année sur l'autre.
    Annuelle : cycle complet depuis le semis, replantée chaque saison.
    """

    PERENNIAL = "perennial"
    ANNUAL = "annual"


@dataclass(frozen=True)
class SpeciesSpec:
    code: str
    label: str
    crop_type: CropType
    #: Stades dans l'ordre du cycle, codes utilisés par le calendrier
    stages: tuple[str, ...]
    #: Vrai si l'espèce perd son feuillage l'hiver : un indice bas y est
    #: alors normal, à ne pas confondre avec un stress.
    deciduous: bool = False
    #: Vrai pour les arbres fruitiers : leur première récolte n'arrive
    #: qu'après plusieurs années. La récolte prévue n'est alors calculée
    #: que si l'utilisateur indique que le verger est en production.
    orchard: bool = False


SPECIES: dict[str, SpeciesSpec] = {
    # ---------------- Arboriculture ----------------
    "olivier": SpeciesSpec(
        code="olivier", label="Olivier", crop_type=CropType.PERENNIAL,
        orchard=True,
        stages=("repos", "debourrement", "floraison", "nouaison",
                "maturation", "recolte"),
    ),
    "amandier": SpeciesSpec(
        code="amandier", label="Amandier", crop_type=CropType.PERENNIAL,
        deciduous=True, orchard=True,
        stages=("dormance", "debourrement", "floraison", "grossissement",
                "maturation", "recolte", "post_recolte"),
    ),
    "caroubier": SpeciesSpec(
        code="caroubier", label="Caroubier", crop_type=CropType.PERENNIAL,
        orchard=True,
        stages=("repos", "croissance", "floraison", "formation_gousses",
                "maturation", "recolte"),
    ),

    # ---------------- Plantes aromatiques et médicinales ----------------
    "romarin": SpeciesSpec(
        code="romarin", label="Romarin", crop_type=CropType.PERENNIAL,
        stages=("repos", "croissance", "floraison", "pre_recolte",
                "recolte", "reprise_coupe"),
    ),
    "lavande": SpeciesSpec(
        code="lavande", label="Lavande", crop_type=CropType.PERENNIAL,
        stages=("repos", "reprise", "floraison", "recolte", "reprise_coupe"),
    ),
    "sauge": SpeciesSpec(
        code="sauge", label="Sauge officinale", crop_type=CropType.PERENNIAL,
        stages=("repos", "croissance", "floraison", "pre_recolte",
                "recolte", "reprise_coupe"),
    ),
    "menthe": SpeciesSpec(
        code="menthe", label="Menthe", crop_type=CropType.PERENNIAL,
        stages=("repos", "croissance", "pre_recolte", "recolte"),
    ),
    "geranium": SpeciesSpec(
        code="geranium", label="Géranium rosat", crop_type=CropType.PERENNIAL,
        stages=("repos", "croissance", "recolte", "reprise_coupe"),
    ),
    "verveine": SpeciesSpec(
        code="verveine", label="Verveine odorante", crop_type=CropType.PERENNIAL,
        deciduous=True,
        stages=("repos", "croissance", "floraison", "recolte", "reprise_coupe"),
    ),
    "citronnelle": SpeciesSpec(
        code="citronnelle", label="Citronnelle", crop_type=CropType.PERENNIAL,
        stages=("ralentissement", "croissance", "pre_recolte", "recolte"),
    ),
    "thym": SpeciesSpec(
        code="thym", label="Thym", crop_type=CropType.PERENNIAL,
        stages=("repos", "croissance", "prefloraison", "floraison",
                "recolte", "reprise_coupe"),
    ),

    # ---------------- Cultures annuelles ----------------
    "basilic": SpeciesSpec(
        code="basilic", label="Basilic", crop_type=CropType.ANNUAL,
        stages=("semis", "croissance", "pre_recolte", "recolte", "fin_cycle"),
    ),
}


#: Libellés lisibles des stades, partagés par toutes les espèces
STAGE_LABELS: dict[str, str] = {
    "repos": "Repos hivernal",
    "dormance": "Dormance",
    "ralentissement": "Ralentissement",
    "debourrement": "Débourrement",
    "reprise": "Reprise végétative",
    "croissance": "Croissance active",
    "prefloraison": "Pré-floraison",
    "floraison": "Floraison",
    "nouaison": "Nouaison et grossissement",
    "formation_gousses": "Développement des gousses",
    "grossissement": "Grossissement du fruit",
    "maturation": "Maturation",
    "pre_recolte": "Pré-récolte",
    "recolte": "Récolte",
    "post_recolte": "Après récolte",
    "reprise_coupe": "Reprise après coupe",
    "semis": "Semis ou plantation",
    "fin_cycle": "Fin de cycle",
}


def get_species(code: str) -> SpeciesSpec | None:
    return SPECIES.get(code.lower())


def list_species() -> list[SpeciesSpec]:
    return sorted(SPECIES.values(), key=lambda s: s.label)


def stage_label(stage: str) -> str:
    return STAGE_LABELS.get(stage, stage.replace("_", " ").capitalize())

def is_orchard(code: str) -> bool:
    """Vrai pour les arbres fruitiers (olivier, amandier, caroubier)."""
    spec = SPECIES.get(code.lower())
    return bool(spec and spec.orchard)

    
def is_deciduous(code: str) -> bool:
    """
    Vrai si l'espèce perd ses feuilles l'hiver. Un NDVI bas en saison
    froide y est alors normal et ne doit pas déclencher d'alerte.
    """
    spec = SPECIES.get(code.lower())
    return bool(spec and spec.deciduous)