from collections import namedtuple
from bisect import insort
from enum import Enum
import random

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

K = 6

class Card(Enum):
    N = 0
    S = 1
    O = 2
    E = 3

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

    for d in [Card.N, Card.S, Card.O, Card.E]:
        nouveaux_deplacements = etat_choisi.liste_deplacement[:]
        nouveaux_deplacements.append(d)
        result.append(Etat(parent=etat_choisi,
                           liste_deplacement=nouveaux_deplacements,
                           cout=len(nouveaux_deplacements) + heuristique(K, deplacement(nouveaux_deplacements, plateau_initial))))
    return result

# permet d'inserer les états trié en fonction de leurs coûts.


def inserer_etat(file_etat: list[Etat], etat: Etat):
    for i in range(0, len(file_etat)):
        if file_etat[i].cout > etat.cout:
            file_etat.insert(i, etat)
            return

    file_etat.append(etat)


def astar(plateau_initial):
    # n est la taille du taquin
    frontiere = [Etat(parent=None, liste_deplacement=[],
                      cout=heuristique(K, plateau_initial))]
    explored = set()
    # l'état finale à une heuristique de 0 : toutes les cases sont à la bonnes position.

    while len(frontiere) != 0:
        etat_choisi = frontiere.pop(0)
        plateau = deplacement(etat_choisi.liste_deplacement, plateau_initial)

        if heuristique(K, plateau) == 0:
            return etat_choisi
            # ici on retroune la solution. Faire une fct qui calcul la solution si besoins.
        else:
            # S est une liste contenant tous les états trouvé après l'expention
            S = expanse(plateau_initial, etat_choisi)
            for etat_cree in S:
                # a condition permet de savoir si on est en présence d'un état déjà expensé.
                if tuple(deplacement(etat_cree.liste_deplacement, plateau_initial)) not in explored:
                    # l'état sera inséré par odre de coût à l'aide de la fonction inserer_etat.
                    inserer_etat(frontiere, etat_cree)

        explored.add(tuple(plateau))
    return None


def get_poids_tuile(k: int, i: int):
    if i > NOMBRE_TUILES:
        return 0
    return POIDS_TUILES[(k - 1) * NOMBRE_TUILES + i]


def distance_elem(position: tuple[int, int], i: int):
    return abs(position[1] - i // DIM_GRILLE) + abs(position[0] - i % DIM_GRILLE)

# l'heuristique sera une distance de Manhattan pondéré.


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


# move_line et la fonction qui gère le cas limite des direction Est et Ouest.
# dir = 1 => Vers l'Est
# dir = -1 => Vers l'Ouest
def move_line(plateau, ligne, dir: int):
    n = DIM_GRILLE

    if dir == 1:
        for i in reversed(range(ligne * n, (ligne + 1)*n - 1)):
            plateau[i+1] = plateau[i]
        plateau[ligne*n] = -1
    elif dir == -1:
        for i in range(ligne * n, (ligne + 1)*n - 1):
            plateau[i] = plateau[i+1]
        plateau[(ligne + 1)*n - 1] = -1


# move_colone et la fonction qui gère les cas limite des directions Nord et sud
# dir = -1 => Vers le Sud
# dir = 1 => Vers le Nord
def move_colonne(plateau, colone, dir: int):
    n = DIM_GRILLE

    if dir == 1:
        for i in range(colone + n, n*n, n):
            plateau[i-n] = plateau[i]
        plateau[n*(n-1) + colone] = -1
    elif dir == -1:
        for i in reversed(range(colone + n, n * (n), n)):
            plateau[i] = plateau[i-n]
        plateau[colone] = -1

# la fonction permet de déplacer la case vide sur notre taquin.
# directions est une liste de direction. Une direction peut être N,S,E,O. Ou N=Nord, S=Sud, O=Ouest, E=Est
# Dans chaque déplacement, on identifiera si on est sur un cas "limite". Par exemple si on est sur la ligen 0 du taleau et qu'on veut se déplacer vers le nord on doit déplacer toutes les cases vers le haut et déscendre la case vide tout en base. On doit donc soit déplacer la colone, soit la ligne en fonction de la direction du déplacement.


def deplacement(directions, plateau_initial):
    n = DIM_GRILLE
    plateau = plateau_initial[:]
    for dir in directions:
        pos_case_vide = plateau.index(-1)
        if dir == Card.N:
            if 0 <= pos_case_vide < n:
                move_colonne(plateau, pos_case_vide, 1)
            else:
                swap(plateau, pos_case_vide, pos_case_vide-n)
        elif dir == Card.S:
            if n*n-n <= pos_case_vide < n*n:
                move_colonne(plateau, pos_case_vide % n, -1)
            else:
                swap(plateau, pos_case_vide, pos_case_vide+n)
        elif dir == Card.O:
            if pos_case_vide in [x for x in range(0, n*n, n)]:
                move_line(plateau, pos_case_vide // n, -1)
                # [x for x in range(0, n*n, n)] -> permet de créer une liste par palier de n si n =3 on aura: [0,3,6]
            else:
                swap(plateau, pos_case_vide, pos_case_vide-1)
        elif dir == Card.E:
            if pos_case_vide in [x for x in range(n-1, n*n, n)]:
                move_line(plateau, pos_case_vide // n, 1)
                # [x for x in range(n-1, n*n, n)] -> permet de créer une liste par palier de n en commençant par n-1 : si n =3 on aura: [2,5,8]
            else:
                swap(plateau, pos_case_vide, pos_case_vide+1)
    return plateau

# permet de savoir si un taquin est sovlable.
# Si il est non solvable la fonction retournera false.
def solvable(plateau_initial):
    n = DIM_GRILLE
    plateau = plateau_initial[:]
    nb_permutations = 0
    # On s'arrête avant la dernière case car la grille sera forcément déjà ordonnée
    for i in range(0, n*n-1):
        # Si la valeur ne correspond pas à la case, on cherche la bonne valeur dans plateau et on la permute avec la valeur de la case actuelle
        if plateau[i] != i:
            swap(plateau, plateau.index(i), i)
            # On compte le nombre de permutations effectuées
            nb_permutations += 1
    # On vérifie si la parité du nombre de permutations à effectuer et celle de l'indice de la case vide (-1) sont les mêmes 
    # => condition de solvabilité du taquin, cf. la page Wikipedia du taquin
    return nb_permutations % 2 == plateau_initial.index(-1) % 2

def generer_grille_resolue():
    grille = []
    for i in range(0, DIM_GRILLE*DIM_GRILLE - 1):
        grille.append(i)
    grille.append(-1)
    return grille

def generer_grille_aleatoire(resolvable: bool=False):
    grille = generer_grille_resolue()
    while True:
        random.shuffle(grille)
        if not resolvable or solvable(grille):
            return grille

# main
if __name__ == '__main__':
    K = 0
    plateau = [1, 3, -1, 
               5, 7, 6, 
               4, 2, 0]
    if solvable(plateau):
        etat_final = astar(plateau)
        if etat_final is not None:
            print(etat_final.liste_deplacement)

            for i in range(0, len(etat_final.liste_deplacement)):
                dep = deplacement(etat_final.liste_deplacement[:i+1], plateau)
                print()
                print(dep[:3])
                print(dep[3:6])
                print(dep[6:])
    else:
        print("pas de solution à ce taquin possible")
