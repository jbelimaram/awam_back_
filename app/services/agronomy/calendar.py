"""
Calendrier phénologique tunisien.

Pour chaque espèce, la période de l'année de chaque stade, exprimée en
mois. C'est ce fichier qui répond à : « quel est le stade de cette
culture aujourd'hui ? », sans quoi aucun seuil ne peut être appliqué.

SOURCE : document de référence agronomique AWAM, colonne "Période
indicative", complété pour les stades de repos non décrits.

Les périodes peuvent se chevaucher (récolte et maturation par exemple) :
le stade retenu est le dernier déclaré qui couvre la date, les stades
étant listés dans l'ordre du cycle.

Une période peut passer d'une année sur l'autre (novembre → février) :
`start_month` est alors supérieur à `end_month`.

DATE DE PLANTATION — elle est prise en compte de deux façons :
  - Avant la date de plantation, la culture n'a pas de stade : une image
    satellite antérieure ne la concerne pas.
  - Culture ANNUELLE (basilic) : le calendrier décrit un cycle qui part
    du semis. Quand la date de semis est connue, ce cycle est DÉCALÉ pour
    commencer au mois du semis, en gardant la durée de chaque stade donnée
    par le document. Un basilic semé en septembre est donc en croissance
    en octobre, et non en « fin de cycle » comme un basilic semé en mars.
    Au-delà de la fin du cycle, la culture reste en fin de cycle.
    Limite : les durées du document correspondent à un semis de printemps ;
    hors saison, la croissance réelle peut être plus lente.
  - Culture PÉRENNE (arbres, aromatiques vivaces) : le stade suit les
    saisons, le calendrier s'applique tel quel quelle que soit l'année de
    plantation ; l'âge agit sur les seuils, pas sur le stade.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.services.agronomy.species import CropType, get_species


@dataclass(frozen=True)
class StagePeriod:
    stage: str
    start_month: int   # 1 = janvier
    end_month: int     # inclus ; < start_month si la période passe l'hiver
    #: Vrai si une baisse d'indice y est normale (coupe, récolte, taille)
    cultural_drop: bool = False

    def covers(self, month: int) -> bool:
        if self.start_month <= self.end_month:
            return self.start_month <= month <= self.end_month
        # Période à cheval sur deux années : novembre → février
        return month >= self.start_month or month <= self.end_month

    @property
    def label(self) -> str:
        months = ["janvier", "février", "mars", "avril", "mai", "juin",
                  "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        if self.start_month == self.end_month:
            return months[self.start_month - 1]
        return f"{months[self.start_month - 1]}–{months[self.end_month - 1]}"


PHENOLOGY: dict[str, tuple[StagePeriod, ...]] = {

    # Olivier : débourrement mars-avril, floraison avril-mai,
    # nouaison mai-septembre, maturation sept-nov, récolte oct-déc
    "olivier": (
        StagePeriod("repos", 12, 2),
        StagePeriod("debourrement", 3, 4),
        StagePeriod("floraison", 4, 5),
        StagePeriod("nouaison", 5, 9),
        StagePeriod("maturation", 9, 11),
        StagePeriod("recolte", 10, 12, cultural_drop=True),
    ),

    # Amandier : débourrement janv-fév, floraison fév-mars,
    # grossissement avril-juin (caduc : NDVI bas en hiver = normal)
    "amandier": (
        StagePeriod("dormance", 11, 1),
        StagePeriod("debourrement", 1, 2),
        StagePeriod("floraison", 2, 3),
        StagePeriod("grossissement", 4, 6),
        StagePeriod("maturation", 6, 7),
        StagePeriod("recolte", 6, 8, cultural_drop=True),
        StagePeriod("post_recolte", 8, 10),
    ),

    # Caroubier : croissance mars-mai, gousses juin-septembre
    "caroubier": (
        StagePeriod("repos", 11, 2),
        StagePeriod("croissance", 3, 5),
        StagePeriod("floraison", 5, 6),
        StagePeriod("formation_gousses", 6, 9),
        StagePeriod("maturation", 9, 10),
        StagePeriod("recolte", 9, 11, cultural_drop=True),
    ),

    # Romarin : croissance fév-mai, pré-récolte juin-juillet
    "romarin": (
        StagePeriod("repos", 12, 1),
        StagePeriod("croissance", 2, 5),
        StagePeriod("floraison", 3, 6),
        StagePeriod("pre_recolte", 6, 7),
        StagePeriod("recolte", 6, 7, cultural_drop=True),
        StagePeriod("reprise_coupe", 8, 11),
    ),

    # Lavande : reprise fév-mars, floraison mai-juillet
    "lavande": (
        StagePeriod("repos", 11, 1),
        StagePeriod("reprise", 2, 4),
        StagePeriod("floraison", 5, 7),
        StagePeriod("recolte", 6, 7, cultural_drop=True),
        StagePeriod("reprise_coupe", 8, 10),
    ),

    # Sauge : croissance mars-mai, pré-récolte juin
    "sauge": (
        StagePeriod("repos", 11, 2),
        StagePeriod("croissance", 3, 5),
        StagePeriod("floraison", 5, 7),
        StagePeriod("pre_recolte", 6, 6),
        StagePeriod("recolte", 6, 7, cultural_drop=True),
        StagePeriod("reprise_coupe", 8, 10),
    ),
        # Menthe : croissance mars-juin, récoltes mai-octobre
    "menthe": (
        StagePeriod("repos", 11, 2),
        StagePeriod("croissance", 3, 6),
        StagePeriod("pre_recolte", 5, 10),
        StagePeriod("recolte", 5, 10, cultural_drop=True),
    ),

    # Géranium rosat : croissance mars-septembre
    "geranium": (
        StagePeriod("repos", 12, 2),
        StagePeriod("croissance", 3, 9),
        StagePeriod("recolte", 6, 7, cultural_drop=True),
        StagePeriod("reprise_coupe", 8, 8),
        StagePeriod("recolte", 9, 11, cultural_drop=True),
    ),

    # Verveine : croissance mars-août (caduc)
    "verveine": (
        StagePeriod("repos", 11, 2),
        StagePeriod("croissance", 3, 8),
        StagePeriod("floraison", 6, 8),
        StagePeriod("recolte", 6, 8, cultural_drop=True),
        StagePeriod("reprise_coupe", 9, 10),
    ),

    # Citronnelle : croissance avril-septembre, récolte juin-octobre
    "citronnelle": (
        StagePeriod("ralentissement", 11, 3),
        StagePeriod("croissance", 4, 9),
        StagePeriod("pre_recolte", 6, 10),
        StagePeriod("recolte", 6, 10, cultural_drop=True),
    ),

    # Thym : croissance mars-mai, pré-floraison avril-mai, récolte mai-juil
    "thym": (
        StagePeriod("repos", 12, 2),
        StagePeriod("croissance", 3, 5),
        StagePeriod("prefloraison", 4, 5),
        StagePeriod("floraison", 5, 7),
        StagePeriod("recolte", 5, 7, cultural_drop=True),
        StagePeriod("reprise_coupe", 8, 11),
    ),

    # Basilic : annuel, croissance avril-juillet, récoltes juin-septembre
    "basilic": (
        StagePeriod("semis", 3, 4),
        StagePeriod("croissance", 4, 7),
        StagePeriod("pre_recolte", 6, 9),
        StagePeriod("recolte", 6, 9, cultural_drop=True),
        StagePeriod("fin_cycle", 10, 10),
        StagePeriod("repos", 11, 2),
    ),
}


#: Stade qui clôt le cycle d'une culture annuelle
END_OF_CYCLE_STAGE = "fin_cycle"


def _is_annual(species: str) -> bool:
    spec = get_species(species)
    return spec is not None and spec.crop_type == CropType.ANNUAL


def _shift(period: StagePeriod, months: int) -> StagePeriod:
    """La même période, décalée de `months` mois (avec passage d'année)."""
    wrap = lambda m: (m - 1 + months) % 12 + 1
    return StagePeriod(period.stage, wrap(period.start_month), wrap(period.end_month), period.cultural_drop)


def _months_between(start: date, end: date) -> int:
    """Nombre de mois calendaires de `start` à `end` (0 = même mois)."""
    return (end.year - start.year) * 12 + end.month - start.month


def get_periods(species: str, planting_date: date | None = None) -> tuple[StagePeriod, ...]:
    """
    Toutes les périodes d'une espèce, dans l'ordre du cycle.

    Culture annuelle avec date de semis : le cycle est décalé pour
    commencer au mois du semis (voir l'en-tête du module).
    """
    periods = PHENOLOGY.get(species.lower(), ())
    if not periods or planting_date is None or not _is_annual(species):
        return periods
    offset = planting_date.month - periods[0].start_month
    return tuple(_shift(p, offset) for p in periods)


def get_stage_at(
    species: str, when: date, planting_date: date | None = None
) -> StagePeriod | None:
    """
    Stade de l'espèce à une date donnée.

    Les périodes se chevauchant, on retient le dernier stade déclaré qui
    couvre le mois : les stades étant listés dans l'ordre du cycle, c'est
    le plus avancé (ex. en juillet pour la lavande : récolte, pas floraison).

    Avec la date de plantation : aucun stade avant elle, et pour une
    culture annuelle, cycle décalé au mois du semis.
    """
    if planting_date is not None and when < planting_date:
        return None   # pas encore plantée à cette date

    periods = get_periods(species, planting_date)
    if not periods:
        return None

    if planting_date is not None and _is_annual(species):
        end = next((p for p in periods if p.stage == END_OF_CYCLE_STAGE), None)
        if end is not None:
            # Durée du cycle, en mois, du début du semis à la fin de cycle
            cycle_months = (end.end_month - periods[0].start_month) % 12
            if _months_between(planting_date, when) > cycle_months:
                return end   # cycle terminé : la culture reste en fin de cycle

    matching = [p for p in periods if p.covers(when.month)]
    return matching[-1] if matching else None


def is_cultural_period(
    species: str, when: date, planting_date: date | None = None
) -> bool:
    """
    Vrai si une baisse d'indice est attendue à cette date (coupe, récolte,
    taille). Sert à neutraliser les fausses alertes.
    """
    if planting_date is not None and when < planting_date:
        return False
    periods = get_periods(species, planting_date)
    if not periods:
        return False
    return any(p.covers(when.month) and p.cultural_drop for p in periods)

    

#: Stades qui marquent une récolte dans le calendrier
HARVEST_STAGES = ("recolte", "recoltes")


def first_harvest_period(species: str, planting_date: date | None = None) -> StagePeriod | None:
    """Première période de récolte de l'espèce dans le cycle."""
    for period in get_periods(species, planting_date):
        if period.stage in HARVEST_STAGES:
            return period
    return None


def _next_harvest_start(periods: list[StagePeriod], ref: date) -> date:
    """
    Prochaine date de récolte à partir de `ref`. Si `ref` tombe dans une
    saison de récolte, c'est `ref` lui-même : la plante est prête et la
    saison est ouverte. Sinon, le début de la saison suivante. Plusieurs
    saisons possibles (ex. géranium).
    """
    candidates = []
    for period in periods:
        if period.covers(ref.month):
            candidates.append(ref)
        elif period.start_month > ref.month:
            candidates.append(date(ref.year, period.start_month, 1))
        else:
            candidates.append(date(ref.year + 1, period.start_month, 1))
    return min(candidates)


def expected_harvest_date(
    species: str,
    planting_date: date | None,
    *,
    orchard: bool = False,
    in_production: bool = False,
    today: date | None = None,
) -> date | None:
    """
    Date de récolte prévue, calculée À PARTIR DE LA DATE DE PLANTATION.

    - Culture annuelle (basilic) : plantation + délai avant la première
      récolte (app/services/agronomy/species.py, FIRST_HARVEST_DELAYS).
    - Plante pérenne : plantation + délai avant la première récolte, puis
      première saison de récolte de l'espèce à partir de cette date. Si
      cette date est déjà passée (plante adulte), c'est la prochaine saison
      à partir d'aujourd'hui : une plante pérenne se récolte chaque année.
      Une jeune plantation est donc récoltée plus tard qu'une plante adulte.
    - Arbre fruitier : uniquement si le verger est en production (case
      saisie par l'utilisateur), prochaine saison de récolte. Sinon None :
      le système n'invente pas une année de première récolte.

    Sans date de plantation : None.
    """
    if planting_date is None:
        return None
    today = today or date.today()

    if orchard:
        if not in_production:
            return None
        periods = [p for p in get_periods(species, None) if p.stage in HARVEST_STAGES]
        return _next_harvest_start(periods, max(planting_date, today)) if periods else None

    from app.services.agronomy.species import first_harvest_delay, is_annual

    delay = first_harvest_delay(species)
    earliest = planting_date + timedelta(days=delay.days if delay else 0)

    # Culture annuelle : la date découle directement de la plantation
    if is_annual(species):
        return earliest

    periods = [p for p in get_periods(species, None) if p.stage in HARVEST_STAGES]
    if not periods:
        return None
    # Jamais avant la date au plus tôt, ni dans une saison déjà passée
    return _next_harvest_start(periods, max(earliest, today))