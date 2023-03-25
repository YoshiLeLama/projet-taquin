# **************************************
# pattern databases generation
# **************************************

from collections import namedtuple
from enum import Enum


Etat = namedtuple('Etat', ['patterne_table', 'cout'])
Etat.__annotations__ = {
    'patterne_table': list[int], 'cout': int}

DIM_GRILLE: int
NOMBRE_TUILES: int
NOMBRE_CASES: int
# Patern pour un 4x4
PATERN = [[0, 1, 2, 4, 5], [3, 6, 7, 10, 11], [8, 9, 12, 13, 14]]


def set_dim_grille(new_dim: int):
    global DIM_GRILLE, NOMBRE_TUILES, NOMBRE_CASES
    DIM_GRILLE = new_dim
    NOMBRE_TUILES = DIM_GRILLE ** 2 - 1
    NOMBRE_CASES = NOMBRE_TUILES + 1


class Card(Enum):
    NORD = 0
    SUD = 1
    OUEST = 2
    EST = 3


def distance_elem(position: tuple[int, int], i: int) -> int:
    return abs(position[1] - i // DIM_GRILLE) + abs(position[0] - i % DIM_GRILLE)

# Distance de manhattan pondéré. On veut juste vérifié que le nb de "déplacement" ou le coût et bien de 1 + le coût du parent.


def heuristique(etat_courant: list[int]) -> int:
    resultat = 0
    for i in range(0, NOMBRE_CASES):
        if etat_courant[i] != -1:
            resultat += distance_elem(
                (i % DIM_GRILLE, i // DIM_GRILLE), etat_courant[i])
    return resultat

# On calcul tous les états qu'on peut générer à partir de l'état choisie. Pour cela on devra faire tous les déplacement possible pour chaque tuile du paterne. De plus pour que l'état soit considéré il faut respecter la condition que le cout augmente de 1 comme on est sur une expension en largeur d'abord.


def expanse(etat_choisi: Etat) -> list[Etat]:
    result: list[Etat] = []
    c = 0
    # variable qui permet de vérifier qu'un plateau n'est pas déjà généré.
    alrdy_generate = set()
    for element in etat_choisi.patterne_table:
        if element != -1:
            for d in [Card.NORD, Card.SUD, Card.OUEST, Card.EST]:
                depl = deplacement(d,
                                   etat_choisi.patterne_table, element)
                if depl is not None:
                    c = heuristique(depl)
                    if c == etat_choisi.cout+1 and tuple(depl) not in alrdy_generate:
                        result.append(Etat(patterne_table=depl,
                                           cout=heuristique(depl)))
                        alrdy_generate.add(tuple(depl))
    return result


def swap(l, i, j):
    l[i], l[j] = l[j], l[i]

# On va déplacer notre tuile cible et non la case vide. La tuile à déplacer dépend de notre paterne.


def deplacement(dir, plateau_courant, case_deplace) -> list[int]:
    n = DIM_GRILLE
    plateau = plateau_courant[:]

    pos_case_a_deplace = plateau.index(case_deplace)
    if dir == Card.NORD:
        if 0 <= pos_case_a_deplace < n:
            return None
        else:
            swap(plateau, pos_case_a_deplace, pos_case_a_deplace - n)
    elif dir == Card.SUD:
        if n * n - n <= pos_case_a_deplace < n * n:
            return None
        else:
            swap(plateau, pos_case_a_deplace, pos_case_a_deplace + n)
    elif dir == Card.OUEST:
        if pos_case_a_deplace in [x for x in range(0, n * n, n)]:
            return None
            # [x for x in range(0, n*n, n)] -> permet de créer une liste par palier de n si n =3 on aura: [0,3,6]
        else:
            swap(plateau, pos_case_a_deplace, pos_case_a_deplace - 1)
    elif dir == Card.EST:
        if pos_case_a_deplace in [x for x in range(n - 1, n * n, n)]:
            return None
            # [x for x in range(n-1, n*n, n)] -> permet de créer une liste par palier de n en commençant par n-1 : si n =3 on aura: [2,5,8]
        else:
            swap(plateau, pos_case_a_deplace, pos_case_a_deplace + 1)
    return plateau

# générer le plateau en fct du parterne utilisé. On place toutes les tuiles comme des tuiles vides pour celles qui ne sont pas dans le patterne


def pattern_study(grille_resolue: list[int], pattern: list[int]) -> list[int]:
    tab_pattern = grille_resolue[:]
    for i in range(0, NOMBRE_TUILES):
        if tab_pattern[i] not in pattern:
            tab_pattern[i] = -1
    return tab_pattern

# Pour générer tous les coûts possible pour tous les paternes on utilisera une stratégie de largeur d'abord.


def bfs(root: list[int]) -> None:
    queue: list[Etat] = []
    explored: list[Etat] = []
    plate_explored = set()
    s: list[Etat] = []
    for pattern in PATERN:
        c = 0
        queue.append(
            Etat(pattern_study(root, pattern), c))
        while queue != []:
            v = queue.pop(0)
            plate_explored.add(tuple(v.patterne_table))
            s = expanse(v)
            for element in s:
                if tuple(element.patterne_table) not in plate_explored:
                    queue.append(element)
            explored.append(v)


def generer_grille_resolue() -> list[int]:
    grille = []
    for i in range(0, DIM_GRILLE * DIM_GRILLE - 1):
        grille.append(i)
    grille.append(-1)
    return grille


if __name__ == '__main__':
    set_dim_grille(4)
    bfs(generer_grille_resolue())
