import math
import sqlite3
import threading
import time
from collections import namedtuple
from bisect import insort
from enum import Enum
import random

import numpy as np


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
        self.path = [root]
        self.grilles_rencontrees = {tuple(root)}
        self.nb_noeud_explo = 0
        self.chemin = []
        bound = self.h(list(root))
        while True:
            t = self.search(0, bound)
            if t == -1:
                return self.path[-1], bound
            print(t)
            if t == math.inf:
                return -1
            bound = t
            print(bound)

    def successors(self, node):
        values = self.deplacement(node)
        for i in range(len(values)):
            x = values[i]
            j = i
            while j > 0 and self.h(list(values[j - 1][0])) > self.h(list(x[0])):
                values[j] = values[j - 1]
                j = j - 1
                values[j] = x
        return values

    def search(self, g, bound):
        self.nb_noeud_explo += 1
        node = self.path[-1]
        h = self.h(list(node))
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
                if t == -1:
                    return -1
                if t < min_val:
                    min_val = t
                self.path.pop()
                self.grilles_rencontrees.pop()
        return min_val


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


def pa_db():
    db = dict()
    try:
        databases = sqlite3.connect("pa5-5-5_db.db")
    except sqlite3.Error as e:
        print(e)
    cur = databases.cursor()

    cur.execute(
        "SELECT * FROM paterne ")
    rows = cur.fetchall()
    for row in rows:
        db.update({row[0]: row[1]})

    def pattern_study(grille_etudier: list[int], pattern: list[int]) -> list[int]:
        tab_pattern = grille_etudier[:]
        for i in range(0, NOMBRE_CASES):
            if tab_pattern[i] not in pattern:
                tab_pattern[i] = -1
        return tuple(tab_pattern)

    def heuristique(etat_courant: list[int]):
        template = [[0, 1, 2, 4, 5], [3, 6, 7, 10, 11], [8, 9, 12, 13, 14]]
        result = 0
        for i in template:
            teste = pattern_study(etat_courant, i)
            result += db.get(str(teste))
        databases.close()
        return result
    return heuristique


def generer_grille_resolue():
    n = DIM_GRILLE
    grille = [i % (n*n) for i in range(0, n*n)]
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


# main
if __name__ == '__main__':
    set_dim_grille(4)
    plateau = generer_grille_aleatoire()
    while not solvable(plateau):
        plateau = generer_grille_aleatoire()
    # plateau = [12, 1, -1, 5,
    #            11, 9, 7, 13,
    #            0, 10, 3, 2,
    #            4, 8, 14, 6]
    plateau = [12, 1, -1, 5,
               11, 9, 7, 13,
               0, 10, 3, 2,
               4, 8, 14, 6]
    solver = IDA_star(pa_db(), deplacement(DIM_GRILLE))
    print(plateau)
    if solvable(plateau):
        beg = time.time_ns()
        res = solver.ida_star(plateau)
        print("solution trouvé en ", (time.time_ns() - beg)*10**(-9), "s", res)

    # experimet(50)
