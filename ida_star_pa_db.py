import math
import sqlite3
import time
import random
import numpy as np
import walking_distance as wd
import taquin as tq

#########################################################
# résolveur taquin 4x4 utilisant l'heuristique de pattern db additive.
#########################################################

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
        """On définit des fct qu'aura besoin notre algo pour fonctionner. 

        Args:
            heuristique (liste[int]): retourne le cout de l'état courant. 
            deplacement (list[int]): retourne une liste de tuple avec (nouvelle disposition des tuiles, déplacement réalisé)
        """
        self.h = heuristique
        self.deplacement = deplacement

    def ida_star(self, root):
        """ida_star est la fonction mère de l'ago ida*. Il est mis en applicaion pour résoudre le jeu du taquin. 

        Args:
            root (list[int]): Racine de l'arbre

        Returns:
            tuple(list[str],bound): retourne le plus cort chemein de la racine à l'état final. 
        """
        global nombre_etats_explo
        self.path = [root]
        self.grilles_rencontrees = {tuple(root)}
        self.nb_noeud_explo = 0
        self.chemin = []
        bound = self.h(list(root))
        while True:
            t = self.search(0, bound)
            if t == -1:
                nombre_etats_explo = self.nb_noeud_explo
                return tuple(self.chemin), bound
            print(t)
            if t == math.inf:
                return -1
            bound = t

    def search(self, g, bound):
        """fonction réccursive Search pour chercher le meilleur noeud à expenser 

        Args:
            g (int): cout du déplacement du noeud u vers v (actuellement +1 (ce qui correspond à la profondeur))
            bound (_type_): profondeur limite

        Returns:
            int: le prochain coût minimal pour résoudre le taquin.
        """
        # var pour le teste *******************************
        global nb_etat_max_ds_frontiere
        self.nb_noeud_explo += 1
        # **************************************************
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
        """successors permet de trier par ordre de coût les noeuds trouvés lors de l'expansion du noeud étudié

        Args:
            node (list[int]): plateau courant

        Returns:
            _type_: liste de tuple (plateau, déplacement) trié par ordre de coût.
        """
        global nb_etat_genere
        values = self.deplacement(node)
        for i in range(len(values)):
            x = values[i]
            j = i
            while j > 0 and self.h(list(values[j - 1][0])) > self.h(list(x[0])):
                values[j] = values[j - 1]
                j = j - 1
                values[j] = x
        nb_etat_genere += len(values)
        return values


def deplacement(n):
    """deplacement permet de genenrer une liste des déplacements possibles de la case vide puis retourne la fonction qui permet de la déplacer.
    Args:
        n (int): taille du taquin (n x n)

    Returns:
        function : la fonction depl pour générer tous les déplacements possibles de la case vide
    """
    liste_deplacement = (1, -1, n, -n)

    def swap(l, i, j):
        l[i], l[j] = l[j], l[i]

    def depl(plateau_courant):
        """depl permet de genenrer une liste de tuple pour tous les deplacements(N,S,E,O) possibles de la case vide.

        Args:
            plateau_courant (list[int]): disposition des tuiles du noeud étudié

        Returns:
            list(list[int],Card): (nouvelle disposition des tuiles, déplacement)
        """
        expansion = []
        pos_case_vide = plateau_courant.index(-1)
        for d in liste_deplacement:
            plateau = plateau_courant[:]
            if d == -n:
                if not (0 <= pos_case_vide < n):
                    swap(plateau, pos_case_vide, pos_case_vide - n)
                    expansion.append((plateau, tq.Card.NORD))
            elif d == n:
                if not (n * n - n <= pos_case_vide < n * n):
                    swap(plateau, pos_case_vide, pos_case_vide + n)
                    expansion.append((plateau, tq.Card.SUD))
            elif d == -1:
                if not (pos_case_vide in [x for x in range(0, n * n, n)]):
                    # [x for x in range(0, n*n, n)] -> permet de créer une liste par palier de n si n =3 on aura: [0,3,6]
                    swap(plateau, pos_case_vide, pos_case_vide - 1)
                    expansion.append((plateau, tq.Card.OUEST))
            elif d == 1:
                if not (pos_case_vide in [x for x in range(n - 1, n * n, n)]):
                    # [x for x in range(n-1, n*n, n)] -> permet de créer une liste par palier de n en commençant par n-1 : si n =3 on aura: [2,5,8]
                    swap(plateau, pos_case_vide, pos_case_vide + 1)
                    expansion.append((plateau, tq.Card.EST))
        return expansion

    return depl


def pa_db(file):
    """permet de récupérer la base de donées du groupe de paternes étudiés dans un dictionnaire pour ensuite retourner la foction pour utiliser ce dictionnaire. 
    Args:
        file (str) : le chein de la bd
    Returns:
        function: fonction qui calcul l'heuristique de la disposition des tuile du noeud étudié.
    """
    db = dict()

    databases = sqlite3.connect(file)
    cur = databases.cursor()

    cur.execute("SELECT * FROM paterne;")

    rows = cur.fetchall()
    for row in rows:
        db.update({row[0]: row[1]})

    def pattern_study(grille_etudier: list[int], pattern: list[int]) -> list[int]:
        """dans le dictionnaire toutes les tuiles en dehors du paterne ne sont pas étudiées (même la case vide). Dans la bd une tuile non étudiée est égale à -1

        Args:
            grille_etudier (list[int]): disposition des tuiles du noeud étudié.
            pattern (list[int]): le paterne qu'on étudie

        Returns:
            list[int]: notre plateau avec seulement les tuiles présentent dans le paterne avec le reste mis à -1
        """
        tab_pattern = grille_etudier[:]
        for i in range(0, NOMBRE_CASES):
            if tab_pattern[i] not in pattern:
                tab_pattern[i] = -1
        return tuple(tab_pattern)

    def heuristique(etat_courant: list[int]):
        """calcul l'heuristique de la disposition des tuiles du noeud étudié à l'aide d'une bd de paterne statique et additif. 

        Args:
            etat_courant (list[int]): disposition des tuiles du noeud étudié.

        Returns:
            int: la valeur de l'heuristique calculée.
        """
        template = [[0, 1, 2, 4, 5], [3, 6, 7, 10, 11], [8, 9, 12, 13, 14]]
        result = 0
        for i in template:
            teste = pattern_study(etat_courant, i)
            result += db.get(str(teste))
        databases.close()
        return result

    return heuristique


def wd_db():
    """ permet de récup la bd de walking distance et de retourner la fonction permettant de retourner l'heuristique en utilisant wd """
    table_dict = wd.table_dict.copy()
    u64 = np.ulonglong
    U64_SEVEN = u64(7)
    U64_THREE = u64(3)
    U64_EIGHT = u64(8)

    def heuristique(t):
        t = np.ndarray(t[:])
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
    # global nb_etat_genere, nb_etat_max_ds_frontiere, nombre_etats_explo
    # tp.init_bd_data(tp.file3)
    # for _ in range(n):
    #     plateau = generer_grille_aleatoire()
    #     while not solvable(plateau):
    #         plateau = generer_grille_aleatoire()
    #     # gc est le garbage collector. Il permettrait clear la ram
    #     gc.collect()
    #     nb_etat_genere = 0
    #     nb_etat_max_ds_frontiere = 0
    #     nombre_etats_explo = 0
    #     solver = IDA_star(pa_db("bd_resolver/pa5-5-5_db.db"),
    #                       deplacement(DIM_GRILLE))
    #     res = solver.ida_star(plateau)
    #     tp.panda_data(tp.file3,
    #                   nb_etat_genere,
    #                   res[1],
    #                   0,
    #                   0,
    #                   nb_etat_max_ds_frontiere,
    #                   nombre_etats_explo,
    #                   0)
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


set_dim_grille(4)

# main
if __name__ == '__main__':
    # plateau = generer_grille_aleatoire()
    # while not solvable(plateau):
    #     plateau = generer_grille_aleatoire()
    # plateau = [13, 8, 4, 1, 3, -1, 6, 11, 9, 12, 7, 2, 5, 10, 0, 14]
    # solver = IDA_star(pa_db("bd_resolver/pa5-5-5_db.db"),
    #                   deplacement(DIM_GRILLE))
    # print(plateau)
    # if solvable(plateau):
    #     beg = time.time_ns()
    #     res = solver.ida_star(plateau)
    #     print(nb_etat_genere, nb_etat_max_ds_frontiere, nombre_etats_explo)
    #     print("solution trouvé en ", (time.time_ns() - beg)*10**(-9), "s", res)

    experimet(50)
