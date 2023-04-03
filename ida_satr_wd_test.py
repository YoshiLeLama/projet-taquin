import math
import sqlite3
import threading
import time
from collections import namedtuple
from bisect import insort
from enum import Enum
import random
import numpy as np

import walking_distance as wd

# ********** Variable globale pour la partie exp du prog********
import teste_prog as tp
import gc
nombre_etats_explo = 0
nb_etat_genere = 0
nb_etat_max_ds_frontiere = 0
# **************************************************************


def set_dim_grille(new_dim: int):
    global DIM_GRILLE, NOMBRE_TUILES, NOMBRE_CASES
    DIM_GRILLE = new_dim
    NOMBRE_TUILES = DIM_GRILLE ** 2 - 1
    NOMBRE_CASES = NOMBRE_TUILES + 1


class IDA_star:
    def __init__(self, heuristique, deplacement) -> None:
        self.h = heuristique
        self.deplacement = deplacement

    def ida_star(self, root):
        global nombre_etats_explo
        self.path = [root]
        self.grilles_rencontrees = {tuple(root)}
        self.nb_noeud_explo = 0
        self.chemin = []
        bound = self.h(np.array(root))
        while True:
            t = self.search(0, bound)
            if t == -1:
                nombre_etats_explo = self.nb_noeud_explo
                return tuple(self.chemin), bound
            print(t)
            if t == math.inf:
                return -1
            bound = t
            print(bound)

    def search(self, g, bound):
        # var pour le teste *******************************
        global nb_etat_max_ds_frontiere
        self.nb_noeud_explo += 1
        # **************************************************
        node = self.path[-1]
        h = self.h(np.array(node))
        f = g + h
        if f > bound:
            return f
        if h == 0:
            return -1
        min_val = math.inf
        for succ in self.successors(node):
            if tuple(succ[0]) not in self.grilles_rencontrees:
                self.path.append(succ[0])
                self.grilles_rencontrees.add(tuple(succ[0]))
                self.chemin.append(succ[1])
                t = self.search(g+1, bound)
                # variable pour le teste*******************
                nb_etat_max_ds_frontiere = len(self.path) if len(
                    self.path) > nb_etat_max_ds_frontiere else nb_etat_max_ds_frontiere
                # *********************************
                if t == -1:
                    return -1
                if t < min_val:
                    min_val = t
                # On supprime les valeurs trouver car ce n'est pas le bon noeuds. On remonte donc dans l'arbre
                self.path.pop()
                self.chemin.pop()
                self.grilles_rencontrees.pop()
        return min_val

    def successors(self, node):
        global nb_etat_genere
        values = self.deplacement(node)
        for i in range(len(values)):
            x = values[i]
            j = i
            while j > 0 and self.h(np.array(values[j - 1][0])) > self.h(np.array(x[0])):
                values[j] = values[j - 1]
                j = j - 1
                values[j] = x
        nb_etat_genere += len(values)
        return values


def deplacement(n):
    """n correspond à la taille du tableau : nxn. Pour un tableau 3x3 n=3"""
    liste_deplacement = (1, -1, n, -n)

    def swap(l, i, j):
        l[i], l[j] = l[j], l[i]

    def depl(plateau_courant):
        exansion = []
        pos_case_vide = plateau_courant.index(-1)
        for d in liste_deplacement:
            plateau = plateau_courant[:]
            if d == -n:
                if not (0 <= pos_case_vide < n):
                    swap(plateau, pos_case_vide, pos_case_vide - n)
                    exansion.append((plateau, 'N'))
            elif d == n:
                if not (n * n - n <= pos_case_vide < n * n):
                    swap(plateau, pos_case_vide, pos_case_vide + n)
                    exansion.append((plateau, 'S'))
            elif d == -1:
                if not (pos_case_vide in [x for x in range(0, n * n, n)]):
                    # [x for x in range(0, n*n, n)] -> permet de créer une liste par palier de n si n =3 on aura: [0,3,6]
                    swap(plateau, pos_case_vide, pos_case_vide - 1)
                    exansion.append((plateau, 'O'))
            elif d == 1:
                if not (pos_case_vide in [x for x in range(n - 1, n * n, n)]):
                    # [x for x in range(n-1, n*n, n)] -> permet de créer une liste par palier de n en commençant par n-1 : si n =3 on aura: [2,5,8]
                    swap(plateau, pos_case_vide, pos_case_vide + 1)
                    exansion.append((plateau, 'E'))
        return exansion

    return depl


def wd_db():

    table_dict = wd.table_dict.copy()
    u64 = np.ulonglong
    U64_SEVEN = u64(7)
    U64_THREE = u64(3)
    U64_EIGHT = u64(8)

    def heuristique(table: np.ndarray):
        if len(table) != 16:
            return -1

        table = table.reshape((4, 4))

        rows = np.zeros((4, 4), dtype=u64)
        columns = np.zeros((4, 4), dtype=u64)

        for i in range(0, 4):
            for j in range(0, 4):
                val = table[i][j]
                if val != -1:
                    rows[i][val // 4] += u64(1)
                val = table[j][i]
                if val != -1:
                    columns[i][val % 4] += u64(1)

        table_ids = np.zeros(2, dtype=u64)
        for i in range(0, 4):
            for j in range(0, 4):
                table_ids = np.bitwise_or(
                    np.left_shift(table_ids, U64_THREE), np.array([rows[i][j], columns[i][j]]))

        return table_dict[table_ids[0]] + table_dict[table_ids[1]]

    return heuristique


def generer_grille_resolue():
    n = DIM_GRILLE
    grille = [i % (n*n) for i in range(0, n*n-1)]
    grille.append(-1)
    return grille


def swap(l, i, j):
    l[i], l[j] = l[j], l[i]


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


def generer_grille_aleatoire(resolvable: bool = False):
    grille = generer_grille_resolue()
    while True:
        random.shuffle(grille)
        if not resolvable or solvable(grille):
            return grille


def experimet(n) -> None:
    global nb_etat_genere, nb_etat_max_ds_frontiere, nombre_etats_explo
    tp.init_bd_data(tp.file3)
    for _ in range(n):
        plateau = generer_grille_aleatoire()
        while not solvable(plateau):
            plateau = generer_grille_aleatoire()
        # gc est le garbage collector. Il permettrait clear la ram
        gc.collect()
        nb_etat_genere = 0
        nb_etat_max_ds_frontiere = 0
        nombre_etats_explo = 0
        solver = IDA_star(pa_db(), deplacement(DIM_GRILLE))
        res = solver.ida_star(plateau)
        tp.panda_data(tp.file3,
                      nb_etat_genere,
                      res[1],
                      0,
                      0,
                      nb_etat_max_ds_frontiere,
                      nombre_etats_explo,
                      0)
    tp.graphe_3d_sans_color_bar(tp.file3, "taquin 4x4 utilisant paterne db")
    tp.graphe(tp.file3,  'nb_etat_frontiere', 'nb_etats_explorer',
              'scatter', "nb d'état exploré en fonction du nombre d'état dans la frontière en utilisant l'heuristique paterne db pour 50 taquins")
    tp.graphe(tp.file3,  'nb_de_coup', 'nb_etats_generer',
              'scatter', "nb d'états générés en fonction du nombre de coups en utilisant l'heuristique paterne db pour 50 taquins")
    tp.graphe(tp.file3,  'nb_de_coup', 'nb_etat_frontiere',
              'scatter', "nb d'état max dans la frontière en fonction du nombre de coups en utilisant l'heuristique paterne db pour 50 taquins")
    tp.graphe(tp.file3,  'nb_de_coup', 'nb_etats_explorer',
              'scatter', "nb d'état exploré en fonction du nombre de coups en utilisant l'heuristique paterne db pour 50 taquins")
    tp.graphe(tp.file3,  'nb_etats_generer', 'nb_etats_explorer',
              'scatter', "nb d'état exploré en fonction du nombre d'états générés en utilisant l'heuristique paterne db pour 50 taquins")
# ********************************************************************************************


# main
if __name__ == '__main__':
    set_dim_grille(4)
    plateau = generer_grille_aleatoire()
    while not solvable(plateau):
        plateau = generer_grille_aleatoire()
    plateau = [13, 8, 4, 1, 3, -1, 6, 11, 9, 12, 7, 2, 5, 10, 0, 14]
    solver = IDA_star(pa_db(), deplacement(DIM_GRILLE))
    print(plateau)
    if solvable(plateau):
        beg = time.time_ns()
        res = solver.ida_star(plateau)
        print(nb_etat_genere, nb_etat_max_ds_frontiere, nombre_etats_explo)
        print("solution trouvé en ", (time.time_ns() - beg)*10**(-9), "s", res)

    # experimet(50)
