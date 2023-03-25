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
PATERN = [[1, 2, 3, 5, 6], [4, 7, 8, 11, 12], [9, 10, 13, 14, 15]]


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


def heuristique(etat_courant: list[int]) -> int:
    resultat = 0
    for i in range(0, NOMBRE_CASES):
        if etat_courant[i] != -1:
            resultat += distance_elem(
                (i % DIM_GRILLE, i // DIM_GRILLE), etat_courant[i])
    return resultat


def expanse(etat_choisi: Etat) -> list[Etat]:
    result: list[Etat] = []
    c = 0
    for element in etat_choisi.patterne_table:
        if element != -1:
            for d in [Card.NORD, Card.SUD, Card.OUEST, Card.EST]:
                depl = deplacement(d,
                                   etat_choisi.patterne_table, element)
                c = heuristique(depl)
                if depl is not None and c == etat_choisi.cout+1:
                    result.append(Etat(patterne_table=depl,
                                       cout=heuristique(depl)))
    return result


def swap(l, i, j):
    l[i], l[j] = l[j], l[i]


def deplacement(dir, plateau_courant, case_deplace) -> list:
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


def pattern_sudy(grille_resolue: list[int], pattern_number) -> list[int]:
    tab_pattern = grille_resolue[:]
    pattern = PATERN[pattern_number]
    for i in range(0, NOMBRE_TUILES):
        if tab_pattern[i] not in pattern:
            tab_pattern[i] = -1
    return tab_pattern


def bfs(root) -> None:
    queue: list[Etat] = []
    queue.append(root)
    explored: list[Etat] = []
    s: list[Etat] = []
    cout = 0
    while queue != []:
        for element in queue:
            print(element[0:4])
            print(element[5:8])
            print(element[9:12])
            print(element[13:16])
        v = queue.pop(0)
        explored.append(v)
        s = expanse(v)
        for element in s:
            if s not in explored:
                ...
        queue.append(s)


def generer_grille_resolue():
    grille = []
    for i in range(0, DIM_GRILLE * DIM_GRILLE - 1):
        grille.append(i)
    grille.append(-1)
    return grille


if __name__ == '__main__':
    set_dim_grille(4)
    initial_state = Etat(generer_grille_resolue(), 0)
    bfs(initial_state)
