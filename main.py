from collections import namedtuple
from bisect import insort
from enum import Enum

NOMBRE_TUILES = 8
NOMBRE_CASES = 9
DIM_GRILLE = 3

POIDS_TUILES = [
    36, 12, 12, 4, 1, 1, 4, 1,
    8, 7, 6, 5, 4, 3, 2, 1,
    8, 7, 6, 5, 4, 3, 2, 1,
    8, 7, 6, 5, 3, 2, 4, 1,
    8, 7, 6, 5, 3, 2, 4, 1,
    1, 1, 1, 1, 1, 1, 1, 1,
]

K = 1

# COEFF_NORMAL = [4, 1, 4, 1, 4, 1]

Etat = namedtuple('Etat', ['parent', 'liste_deplacement',
                           'heuristique', 'profondeur'])
Etat.__annotations__ = {
    'parent': Etat, 'liste_deplacement': list[str], 'heuristique': int, 'profondeur': int}

def expanse(plateau_initial: list[int], etat_choisi: Etat):
    # régle et mouvement à définir.
    result: list[Etat] = []

    grille = deplacement(etat_choisi.liste_deplacement, plateau_initial)

    for d in ['N', 'S', 'O', 'E']:
        nouveaux_deplacements = etat_choisi.liste_deplacement[:]
        nouveaux_deplacements.append(d)
        result.append(Etat(parent=etat_choisi,
                           liste_deplacement=nouveaux_deplacements,
                           heuristique=heuristique(K, deplacement(d, grille)),
                           profondeur=etat_choisi.profondeur+1))

    return result

def inserer_etat(file_etat: list[Etat], etat: Etat):
    for i in range(0, len(file_etat)):
        if file_etat[i].heuristique + file_etat[i].profondeur > etat.heuristique + etat.profondeur:
            file_etat.insert(i, etat)
            return
        
    file_etat.append(etat)

def astar(plateau_initial):
    # n est la taille du taquin
    frontiere = [Etat(parent=None, liste_deplacement=[], heuristique=heuristique(K, plateau_initial), profondeur=0)]
    # l'état finale à une heuristique de 0 : toutes les cases sont à la bonnes position.

    explored = set()

    min_heuri = 2000

    while True:
        if frontiere == []:
            return None

        print(frontiere)

        etat_choisi = frontiere.pop(0)

        if etat_choisi.heuristique == 0:
            return etat_choisi
            # ici on retroune la solution. Faire une fct qui calcul la solution si besoins.
        else:
            # S est une liste contenant tous les états trouvé après l'expention
            S = expanse(plateau_initial, etat_choisi)
            for etat_cree in S:
                inserer_etat(frontiere, etat_cree)

def get_poids_tuile(k: int, i: int):
    if i > NOMBRE_TUILES:
        return 0
    return POIDS_TUILES[(k - 1) * NOMBRE_TUILES + i]


def distance_elem(position: tuple[int, int], i: int):
    return abs(position[1] - i // DIM_GRILLE) + abs(position[0] - i % DIM_GRILLE)


def heuristique(k: int, etat_courant: list[int]):
    resultat = 0
    for i in range(0, NOMBRE_CASES):
        if etat_courant[i] != -1:
            resultat += get_poids_tuile(k, etat_courant[i]) * distance_elem(
                (i % 3, i // 3), etat_courant[i])
    return resultat


# la fonction swap permet de  calculer le nouveau plateau en fonction des de la direction qu'on aura trouver dans le deplacement sans les cas limites.
# i : la position de la case vide
# j : la position de la case à changer.
def swap(l, i, j):
    l[i], l[j] = l[j], l[i]

# dir = 1 => Vers l'Est
# dir = -1 => Vers l'Ouest


def move_line(plateau, ligne, dir: int):
    n = DIM_GRILLE
    r = range(ligne*n+1, ligne*n + n)
    if dir > 0:
        r = reversed(r)

    for i in r:
        swap(plateau, i-1, i % n)

# dir = -1 => Vers le Sud
# dir = 1 => Vers le Nord


def move_colone(plateau, colone, dir: int):
    n = DIM_GRILLE
    r = range(colone + n, n*n, n)
    if dir < 0:
        r = reversed(r)

    for i in r:
        swap(plateau, i, (i + n) % (n*n))


# la fonction permet de déplacer la case vide sur notre taquin.
# directions est une liste de direction. Une direction peut être N,S,E,O. Ou N=Nord, S=Sud, O=Ouest, E=Est
# n est la taille du tableau nxn ou 3x3 par exemple
def deplacement(directions, plateau_initial):
    n = DIM_GRILLE
    plateau = plateau_initial
    for dir in directions:
        pos_case_vide = plateau_initial.index(-1)
        if dir == 'N':
            if 0 <= pos_case_vide < n:
                move_colone(plateau, pos_case_vide, 1)
            else:
                swap(plateau, pos_case_vide, pos_case_vide-n)
        elif dir == 'S':
            if n*n-n <= pos_case_vide < n*n:
                move_colone(plateau, pos_case_vide % n, -1)
            else:
                swap(plateau, pos_case_vide, pos_case_vide+n)
        elif dir == 'O':
            if pos_case_vide in [x for x in range(0, n*n, n)]:
                move_line(plateau, pos_case_vide//n, -1)
                # [x for x in range(0, n*n, n)] -> permet de créer une liste par palier de n si n =3 on aura: [0,3,6]
            else:
                swap(plateau, pos_case_vide, pos_case_vide-1)
        elif dir == 'E':
            if pos_case_vide in [x for x in range(n-1, n*n, n)]:
                move_line(plateau, pos_case_vide // n, 1)
                # [x for x in range(n-1, n*n, n)] -> permet de créer une liste par palier de n en commençant par n-1 : si n =3 on aura: [2,5,8]
            else:
                swap(plateau, pos_case_vide, pos_case_vide+1)
    return plateau


# main
if __name__ == '__main__':
    plateau = [1, 3, 0, 5, 7, 6, 4, 2, -1]
    print(astar(plateau))
