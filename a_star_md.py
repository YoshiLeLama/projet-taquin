# *************************
#
# resolveur taquin 3x3 utilisant A* et l'heuristique distance de Manhattan pondéré et linear conflict.
#
# *************************
import threading
import time
from collections import namedtuple
from collections import deque
from bisect import insort
from enum import Enum
import random
import numpy as np
import taquin as tq


# ********** Ce qui est nécessaire à la partie exp du prog********
import teste_prog as tp
import psutil
import os
import gc
nombre_etats_explo = 0
nb_etat_genere = 0
utilisation_CPU = 0
utilisation_RAM = 0
nb_etat_max_ds_frontiere = 0
# **************************************************************

DIM_GRILLE: int
NOMBRE_TUILES: int
NOMBRE_CASES: int
LINEAR_CONFLICT = False


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
COEF_NORM = [4, 1, 4, 1, 4, 1]

writing_in_frontiere_semaphore = threading.Semaphore(1)

should_quit = False


def reset_solving():
    global should_quit
    should_quit = False


def quit_solving():
    global should_quit
    should_quit = True


# COEFF_NORMAL = [4, 1, 4, 1, 4, 1]


def set_weight_set(new_value):
    global K
    K = new_value % (len(POIDS_TUILES) // NOMBRE_TUILES)
    if K == 0:
        K = 6

# **************************************************
#                       Algo A*                    #
# **************************************************
# la fonction expanse permettra de calculer toutes les directions possible et les coûts à partir de l'état choisi.


def expanse(plateau_initial: list[int], etat_choisi: tq.Etat):
    result: list[tq.Etat] = []

    for d in [tq.Card.NORD, tq.Card.SUD, tq.Card.OUEST, tq.Card.EST]:
        nouveaux_deplacements = etat_choisi.liste_deplacement[:]
        nouveaux_deplacements.append(d)
        depl = deplacement(nouveaux_deplacements, plateau_initial)
        if depl is not None:
            result.append(tq.Etat(liste_deplacement=nouveaux_deplacements,
                                  cout=len(nouveaux_deplacements) + (heuristique(K, depl) if not LINEAR_CONFLICT else linear_conflict(depl))))
    return result


# permet d'inserer les états trié en fonction de leurs coûts.


def f(etat: tq.Etat):
    return etat.cout + len(etat.liste_deplacement)


def inserer_etat(file_etat: list[tq.Etat], etat: tq.Etat):
    # global nb_etat_genere
    for i in range(0, len(file_etat)):
        if file_etat[i].cout > etat.cout:
            file_etat.insert(i, etat)
            return i

    file_etat.append(etat)
    # nb_etat_genere += 1
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
                # frontiere.pop(duplicate)
                frontiere.remove(frontiere[duplicate])
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


def astar(plateau_initial) -> tq.Etat | None:
    # # var pour  la partie exp
    # global nombre_etats_explo, nb_etat_max_ds_frontiere, utilisation_RAM,  nb_etat_genere
    # nombre_etats_explo = 0
    # nb_etat_max_ds_frontiere = 0
    # utilisation_RAM = 0
    # nb_etat_genere = 0
    # # ****************************
    frontiere = deque()
    frontiere.append(tq.Etat(liste_deplacement=[],
                             cout=heuristique(K, plateau_initial) if not LINEAR_CONFLICT else linear_conflict(plateau_initial)))
    # stocke les grilles déjà trouvés synchronisé avec la frontière.
    grilles_frontiere = [tuple(plateau_initial[:])]
    explored = set()
    # l'état finale à une heuristique de 0 : toutes les cases sont à la bonnes position.
    calculating_threads = [threading.Thread()] * 4

    while len(frontiere) != 0:
        etat_choisi = frontiere.popleft()
        grilles_frontiere.pop(0)
        plateau = deplacement(etat_choisi.liste_deplacement, plateau_initial)
        if tuple(plateau) not in explored:
            if heuristique(K, plateau) == 0:
                # utilisation_RAM = (psutil.Process(
                #     os.getpid()).memory_info().rss) / 1024 ** 2
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

                for i in range(len(S)):
                    calculating_threads[i].join()

            explored.add(tuple(plateau))
            # # var pour la partie exp ***
            # nombre_etats_explo += 1
            # nb_etat_max_ds_frontiere = nb_etat_max_ds_frontiere if nb_etat_max_ds_frontiere > len(
            #     frontiere) else len(frontiere)
            # # *************************
        if should_quit:
            return None
    return None

# **************************************************
#                                                  #
# **************************************************


# **************************************************
#                       Heuristique                #
# **************************************************
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
    res_final = 0
    if k == 0:
        for poids in range(0, 6):
            for i in range(0, NOMBRE_CASES):
                if etat_courant[i] != -1:
                    resultat += get_poids_tuile(poids, etat_courant[i]) * distance_elem(
                        (i % DIM_GRILLE, i // DIM_GRILLE), etat_courant[i])
            res_final = resultat//COEF_NORM[poids -
                                            1] if resultat//COEF_NORM[poids-1] > res_final else res_final
        return res_final

    for i in range(0, NOMBRE_CASES):
        if etat_courant[i] != -1:
            resultat += get_poids_tuile(k, etat_courant[i]) * distance_elem(
                (i % DIM_GRILLE, i // DIM_GRILLE), etat_courant[i])
    return resultat // COEF_NORM[k-1]


# heuristique linear conflict
# On regarde le nombre de conflit liéaire pour la ligne donné

def row_conflict(row, deb_intervale):
    end = DIM_GRILLE
    end2 = deb_intervale + DIM_GRILLE
    res = 0
    for i in range(0, end):
        # on vérifie que la position final de la case est bien sur la ligne et qu'elle ne se situe pas dessus
        if deb_intervale <= row[i] < end2 and row[i] != deb_intervale+i:
            for y in range(i+1, end):
                # si une des tuiles à sa position final sur la ligne alors elles sont en conflits
                if deb_intervale <= row[y] < end2:
                    res += 1
    return res

# pour un taquin 3x3 row_number peut être 0,1 ou 2.


def col_conflict(col, row_number):
    res = 0
    for i in range(0, DIM_GRILLE):
        # on vérifie que la position final de la case est bien sur la colone et qu'elle ne se situe pas dessus.
        if col[i] % 3 == row_number and col[i] != row_number+i*DIM_GRILLE:
            for y in range(i+1, DIM_GRILLE):
                if col[y] % 3 == row_number:
                    res += 1
    return res


def linear_conflict(plateau_courant):
    res = 0

    # conflit linéaire ligne :
    for i in range(0, NOMBRE_CASES, DIM_GRILLE):
        res += row_conflict(plateau_courant[i:i+DIM_GRILLE], i)

    # confli linéaire colone
    for i in range(0, DIM_GRILLE):
        res += col_conflict(plateau_courant[i:NOMBRE_CASES:DIM_GRILLE], i)
    return heuristique(6, plateau_courant) + 2*res

# **************************************************
#                                                  #
# **************************************************


# **************************************************
#             Deplacement de la case vide           #
# **************************************************

# la fonction swap permet de  calculer le nouveau plateau en fonction des de la direction qu'on aura trouver dans le deplacement sans les cas limites.
# i : la position de la case vide
# j : la position de la case à changer.
def swap(l, i, j):
    l[i], l[j] = l[j], l[i]


# la fonction permet de déplacer la case vide sur notre taquin.
# directions est une liste de direction. Une direction peut être N,S,E,O. Ou N=Nord, S=Sud, O=Ouest, E=Est
# Dans chaque déplacement, on identifiera si on est sur un cas "limite". Par exemple si on est sur la ligen 0 du taleau et qu'on veut se déplacer vers le nord on doit déplacer toutes les cases vers le haut et déscendre la case vide tout en base. On doit donc soit déplacer la colone, soit la ligne en fonction de la direction du déplacement.


def deplacement(directions, plateau_initial):
    n = DIM_GRILLE
    plateau = plateau_initial[:]
    for dir in directions:
        pos_case_vide = plateau.index(-1)
        if dir == tq.Card.NORD:
            if 0 <= pos_case_vide < n:
                return None
            else:
                swap(plateau, pos_case_vide, pos_case_vide - n)
        elif dir == tq.Card.SUD:
            if n * n - n <= pos_case_vide < n * n:
                return None
            else:
                swap(plateau, pos_case_vide, pos_case_vide + n)
        elif dir == tq.Card.OUEST:
            if pos_case_vide in [x for x in range(0, n * n, n)]:
                return None
                # [x for x in range(0, n*n, n)] -> permet de créer une liste par palier de n si n =3 on aura: [0,3,6]
            else:
                swap(plateau, pos_case_vide, pos_case_vide - 1)
        elif dir == tq.Card.EST:
            if pos_case_vide in [x for x in range(n - 1, n * n, n)]:
                return None
                # [x for x in range(n-1, n*n, n)] -> permet de créer une liste par palier de n en commençant par n-1 : si n =3 on aura: [2,5,8]
            else:
                swap(plateau, pos_case_vide, pos_case_vide + 1)
    return plateau

# **************************************************
#                                                  #
# **************************************************


# **************************************************
#    Verification de la solvabilité d'un plateau   #
# **************************************************
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


# **************************************************
#                                                  #
# **************************************************

# **************************************************
#                Grille résolue                    #
# **************************************************

def generer_grille_resolue():
    grille = []
    for i in range(0, DIM_GRILLE * DIM_GRILLE - 1):
        grille.append(i)
    grille.append(-1)
    return grille

# **************************************************
#                                                  #
# **************************************************

# **************************************************
#                  Gille aléatoire                 #
# **************************************************


def generer_grille_aleatoire(resolvable: bool = False):
    grille = generer_grille_resolue()
    while True:
        random.shuffle(grille)
        if not resolvable or solvable(grille):
            return grille

# pour la partie expérimentation du programme *******************************
# n est le nombre de taquin à résoudre


def experiment(poids: list[int], n) -> None:
    global nb_etat_genere, nb_etat_max_ds_frontiere, nombre_etats_explo, utilisation_RAM
    nb_etat_genere, nb_etat_max_ds_frontiere, nombre_etats_explo, utilisation_RAM = 0
    tp.init_bd_data(tp.file)
    poids = [8]
    for _ in range(n):
        plateau = generer_grille_aleatoire()
        while not solvable(plateau):
            plateau = generer_grille_aleatoire()
        for k in poids:
            # gc est le garbage collector. Il permettrait clear la ram
            gc.collect()
            utilisation_CPU = psutil.cpu_percent(None)
            res = astar(plateau)
            utilisation_CPU = (utilisation_CPU+psutil.cpu_percent(None))//2
            tp.panda_data(tp.file,
                          nb_etat_genere,
                          res.cout,
                          utilisation_CPU,
                          utilisation_RAM,
                          nb_etat_max_ds_frontiere,
                          nombre_etats_explo,
                          k)

    tp.linear_reg(tp.file, poids)
    tp.multi_graphe(tp.file, poids, 'nb_etat_frontiere', 'nb_etats_explorer',
                    'scatter', "nb d'état exploré en fonction du nombre d'état dans la frontière en utilisant l'heuristique conflit linéaire pour 500 taquins")
    tp.multi_graphe(tp.file, poids, 'nb_etats_generer', 'utilisation_CPU',
                    'scatter', "Utilisation CPU (en %) en fonction du nombre d'état générer en utilisant l'heuristique conflit linéaire pour 500 taquins")
    tp.multi_graphe(tp.file, poids, 'nb_etats_generer', 'utilisation_RAM',
                    'scatter', "Utilisation RAM (en MiB) en fonction du nombre d'état généré en utilisant l'heuristique conflit linéaire pour 500 taquins")
    tp.multi_graphe(tp.file, poids, 'nb_de_coup', 'nb_etats_generer',
                    'scatter', "nb d'états générés en fonction du nombre de coups en utilisant l'heuristique conflit linéaire pour 500 taquins")
    tp.multi_graphe(tp.file, poids, 'nb_de_coup', 'nb_etat_frontiere',
                    'scatter', "nb d'état max dans la frontière en fonction du nombre de coups en utilisant l'heuristique conflit linéaire pour 500 taquins")
    tp.multi_graphe(tp.file, poids, 'nb_de_coup', 'nb_etats_explorer',
                    'scatter', "nb d'état exploré en fonction du nombre de coups en utilisant l'heuristique conflit linéaire pour 500 taquins")
    tp.multi_graphe(tp.file, poids, 'nb_etats_generer', 'nb_etats_explorer',
                    'scatter', "nb d'état exploré en fonction du nombre d'états générés en utilisant l'heuristique conflit linéaire pour 500 taquins")


# main
if __name__ == '__main__':
    K = 6
    LINEAR_CONFLICT = True
    plateau = generer_grille_aleatoire()
    while not solvable(plateau):
        plateau = generer_grille_aleatoire()

    print(plateau)
    print(solvable(plateau))
    if solvable(plateau):
        beg = time.time_ns()
        res = astar(plateau)
        print(time.time_ns() - beg, '\n', res)
