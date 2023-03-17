import threading
from collections import namedtuple
from bisect import insort
from enum import Enum
import random

DIM_GRILLE: int
NOMBRE_TUILES: int
NOMBRE_CASES: int


def set_dim_grille(new_dim: int):
    global DIM_GRILLE, NOMBRE_TUILES, NOMBRE_CASES
    DIM_GRILLE = new_dim
    NOMBRE_TUILES = DIM_GRILLE ** 2 - 1
    NOMBRE_CASES = NOMBRE_TUILES + 1


set_dim_grille(3)

POIDS_TUILES = [
    36, 12, 12, 4, 1, 1, 4, 1,
    8, 7, 6, 5, 4, 3, 2, 1,
    8, 7, 6, 5, 4, 3, 2, 1,
    8, 7, 6, 5, 3, 2, 4, 1,
    8, 7, 6, 5, 3, 2, 4, 1,
    1, 1, 1, 1, 1, 1, 1, 1,
]

K = 6

nombre_etats_explo = 0

writing_in_frontiere_semaphore = threading.Semaphore(1)

should_quit = False


def reset_solving():
    global should_quit
    should_quit = False


def quit_solving():
    global should_quit
    should_quit = True


class Card(Enum):
    NORD = 0
    SUD = 1
    OUEST = 2
    EST = 3


# COEFF_NORMAL = [4, 1, 4, 1, 4, 1]


# Nous représentons un état comme étant un objet. Il stoquera son parent, la liste des déplacement à faire atteindre l'état final et son coût: le coût f(E)= g(E)+h(E) où g(E) et la profondeur de l'état actuelle et h(E) et l'heuristique calculée.
Etat = namedtuple('Etat', ['parent', 'liste_deplacement',
                           'cout'])
Etat.__annotations__ = {
    'parent': Etat, 'liste_deplacement': list[str], 'cout': int}


def set_weight_set(new_value):
    global K
    K = new_value % (len(POIDS_TUILES) // NOMBRE_TUILES)
    if K == 0:
        K = 6


# la fonction expanse permettra de calculer toutes les directions possible et les coûts à partir de l'état choisi.
def expanse(plateau_initial: list[int], etat_choisi: Etat):
    result: list[Etat] = []

    for d in [Card.NORD, Card.SUD, Card.OUEST, Card.EST]:
        nouveaux_deplacements = etat_choisi.liste_deplacement[:]
        nouveaux_deplacements.append(d)
        result.append(Etat(parent=etat_choisi,
                           liste_deplacement=nouveaux_deplacements,
                           cout=len(nouveaux_deplacements) + heuristique(K, deplacement(nouveaux_deplacements,
                                                                                        plateau_initial))))
    return result


# permet d'inserer les états trié en fonction de leurs coûts.


def f(etat: Etat):
    return etat.cout + len(etat.liste_deplacement)


def inserer_etat(file_etat: list[Etat], etat: Etat):
    for i in range(0, len(file_etat)):
        if file_etat[i].cout > etat.cout:
            file_etat.insert(i, etat)
            return i

    file_etat.append(etat)
    return -1


def calculate_if_valid(etat_cree, plateau_initial, explored, frontiere, grilles_frontiere: list[tuple]):
    grille_atteinte = tuple(deplacement(
        etat_cree.liste_deplacement, plateau_initial))
    # a condition permet de savoir si on est en présence d'un état déjà expensé.
    if grille_atteinte not in explored:
        try:
            duplicate = grilles_frontiere.index(grille_atteinte)
        except ValueError:
            ...
        else:
            if f(etat_cree) < f(frontiere[duplicate]):
                writing_in_frontiere_semaphore.acquire()
                frontiere.pop(duplicate)
                grilles_frontiere.pop(duplicate)
                writing_in_frontiere_semaphore.release()
            # l'état sera inséré par ordre de coût à l'aide de la fonction inserer_etat.
        writing_in_frontiere_semaphore.acquire()
        indice = inserer_etat(frontiere, etat_cree)
        if indice == -1:
            grilles_frontiere.append(grille_atteinte)
        else:
            grilles_frontiere.insert(indice, grille_atteinte)
        writing_in_frontiere_semaphore.release()


def astar(plateau_initial):
    global nombre_etats_explo
    nombre_etats_explo = 0
    # n est la taille du taquin
    frontiere = [Etat(parent=None, liste_deplacement=[],
                      cout=heuristique(K, plateau_initial))]
    grilles_frontiere = [tuple(plateau_initial[:])]
    explored = set()
    # l'état finale à une heuristique de 0 : toutes les cases sont à la bonnes position.
    calculating_threads = [threading.Thread()] * 4

    while len(frontiere) != 0:
        etat_choisi = frontiere.pop(0)
        grilles_frontiere.pop(0)
        plateau = deplacement(etat_choisi.liste_deplacement, plateau_initial)

        if heuristique(K, plateau) == 0:
            return etat_choisi
            # ici on retroune la solution. Faire une fct qui calcul la solution si besoins.
        else:
            # S est une liste contenant tous les états trouvé après l'expention
            S = expanse(plateau_initial, etat_choisi)
            for i in range(0, len(S)):
                calculating_threads[i] = threading.Thread(target=lambda: calculate_if_valid(
                    S[i], plateau_initial, explored, frontiere, grilles_frontiere
                ))
                calculating_threads[i].start()

            for t in calculating_threads:
                t.join()

        explored.add(tuple(plateau))

        nombre_etats_explo = len(frontiere)

        if should_quit:
            return None
    return None


def get_poids_tuile(k: int, i: int):
    if i > NOMBRE_TUILES:
        return 0
    if DIM_GRILLE != 3:
        return 1
    return POIDS_TUILES[(k - 1) * NOMBRE_TUILES + i]


def distance_elem(position: tuple[int, int], i: int):
    return abs(position[1] - i // DIM_GRILLE) + abs(position[0] - i % DIM_GRILLE)


# l'heuristique sera une distance de Manhattan pondéré.


def heuristique(k: int, etat_courant: list[int]):
    resultat = 0
    for i in range(0, NOMBRE_CASES):
        if etat_courant[i] != -1:
            resultat += get_poids_tuile(k, etat_courant[i]) * distance_elem(
                (i % DIM_GRILLE, i // DIM_GRILLE), etat_courant[i])
    return resultat


# la fonction swap permet de  calculer le nouveau plateau en fonction des de la direction qu'on aura trouver dans le deplacement sans les cas limites.
# i : la position de la case vide
# j : la position de la case à changer.
def swap(l, i, j):
    l[i], l[j] = l[j], l[i]


# move_line et la fonction qui gère le cas limite des direction Est et Ouest.
# dir = 1 => Vers l'Est
# dir = -1 => Vers l'Ouest
def move_line(plateau, ligne, dir: int):
    n = DIM_GRILLE

    if dir == 1:
        for i in reversed(range(ligne * n, (ligne + 1) * n - 1)):
            plateau[i + 1] = plateau[i]
        plateau[ligne * n] = -1
    elif dir == -1:
        for i in range(ligne * n, (ligne + 1) * n - 1):
            plateau[i] = plateau[i + 1]
        plateau[(ligne + 1) * n - 1] = -1


# move_colone et la fonction qui gère les cas limite des directions Nord et sud
# dir = -1 => Vers le Sud
# dir = 1 => Vers le Nord
def move_colonne(plateau, colone, dir: int):
    n = DIM_GRILLE

    if dir == 1:
        for i in range(colone + n, n * n, n):
            plateau[i - n] = plateau[i]
        plateau[n * (n - 1) + colone] = -1
    elif dir == -1:
        for i in reversed(range(colone + n, n * (n), n)):
            plateau[i] = plateau[i - n]
        plateau[colone] = -1


# la fonction permet de déplacer la case vide sur notre taquin.
# directions est une liste de direction. Une direction peut être N,S,E,O. Ou N=Nord, S=Sud, O=Ouest, E=Est
# Dans chaque déplacement, on identifiera si on est sur un cas "limite". Par exemple si on est sur la ligen 0 du taleau et qu'on veut se déplacer vers le nord on doit déplacer toutes les cases vers le haut et déscendre la case vide tout en base. On doit donc soit déplacer la colone, soit la ligne en fonction de la direction du déplacement.


def deplacement(directions, plateau_initial):
    n = DIM_GRILLE
    plateau = plateau_initial[:]
    for dir in directions:
        pos_case_vide = plateau.index(-1)
        if dir == Card.NORD:
            if 0 <= pos_case_vide < n:
                move_colonne(plateau, pos_case_vide, 1)
            else:
                swap(plateau, pos_case_vide, pos_case_vide - n)
        elif dir == Card.SUD:
            if n * n - n <= pos_case_vide < n * n:
                move_colonne(plateau, pos_case_vide % n, -1)
            else:
                swap(plateau, pos_case_vide, pos_case_vide + n)
        elif dir == Card.OUEST:
            if pos_case_vide in [x for x in range(0, n * n, n)]:
                move_line(plateau, pos_case_vide // n, -1)
                # [x for x in range(0, n*n, n)] -> permet de créer une liste par palier de n si n =3 on aura: [0,3,6]
            else:
                swap(plateau, pos_case_vide, pos_case_vide - 1)
        elif dir == Card.EST:
            if pos_case_vide in [x for x in range(n - 1, n * n, n)]:
                move_line(plateau, pos_case_vide // n, 1)
                # [x for x in range(n-1, n*n, n)] -> permet de créer une liste par palier de n en commençant par n-1 : si n =3 on aura: [2,5,8]
            else:
                swap(plateau, pos_case_vide, pos_case_vide + 1)
    return plateau


# permet de savoir si un taquin est sovlable.
# Si il est non solvable la fonction retournera false.


def solvable(plateau_initial):
    n = DIM_GRILLE
    plateau = plateau_initial[:]
    nb_permutations = 0
    # On s'arrête avant la dernière case car la grille sera forcément déjà ordonnée
    for i in range(0, n * n - 1):
        # Si la valeur ne correspond pas à la case, on cherche la bonne valeur dans plateau et on la permute avec la valeur de la case actuelle
        if plateau[i] != i:
            swap(plateau, plateau.index(i), i)
            # On compte le nombre de permutations effectuées
            nb_permutations += 1
    # On vérifie si la parité du nombre de permutations à effectuer et celle de l'indice de la case vide (-1) sont les mêmes
    # => condition de solvabilité du taquin, cf. la page Wikipedia du taquin

    i = plateau_initial.index(-1)
    return nb_permutations % 2 == (DIM_GRILLE - (i % DIM_GRILLE) + DIM_GRILLE - (i // DIM_GRILLE) - 2) % 2


def generer_grille_resolue():
    grille = []
    for i in range(0, DIM_GRILLE * DIM_GRILLE - 1):
        grille.append(i)
    grille.append(-1)
    return grille


def generer_grille_aleatoire(resolvable: bool = False):
    grille = generer_grille_resolue()
    while True:
        random.shuffle(grille)
        if not resolvable or solvable(grille):
            return grille


# main
if __name__ == '__main__':
    K = 0
    set_dim_grille(4)
    plateau = generer_grille_aleatoire(True)
    print(solvable(plateau))
    if solvable(plateau):
        etat_final = astar(plateau)
        if etat_final is not None:
            print(etat_final.liste_deplacement)

            for i in range(0, len(etat_final.liste_deplacement)):
                dep = deplacement(
                    etat_final.liste_deplacement[:i + 1], plateau)
                print()
                print(dep[:3])
                print(dep[3:6])
                print(dep[6:])
    else:
        print("pas de solution à ce taquin possible")
