
from collections import OrderedDict, deque
import sqlite3
from sqlite3 import Error
import threading

# ###############################################################################
# Permet de générer la base de données pour l'heuristique de patteerne additif de manière static
# ###############################################################################


def set_dim_grille(new_dim: int):
    global DIM_GRILLE, NOMBRE_TUILES, NOMBRE_CASES
    DIM_GRILLE = new_dim
    NOMBRE_TUILES = DIM_GRILLE ** 2 - 1
    NOMBRE_CASES = NOMBRE_TUILES + 1


class Generation_paterne_db:
    def __init__(self, e) -> None:
        self.expanse = e
        pass

    def bfs(self, root: tuple, paterne: tuple):
        self.paterne = paterne
        self.queu = OrderedDict({root: 0})
        self.alrdy_found = {root}
        self.explored = dict()
        s = set()
        while bool(self.queu):
            # k permet de récuprer la position 0 du dictionnaire donc de la file. En vérité il donne la première clef
            position0 = next(iter(self.queu))
            selected = {position0: self.queu.pop(position0)}
            # s est le résultat de l'expension
            s = self.expanse(selected)
            for k in s:
                if tuple(k[0]) not in self.alrdy_found:
                    self.queu.update({tuple(k[0]): k[1]})
                    self.alrdy_found.add(tuple(k[0]))
            var = tuple(self.suppression_de_la_case_vide(
                list(position0)))
            if var not in self.explored:
                self.explored.update(
                    {var: selected.pop(position0)})
        return self.explored

    def suppression_de_la_case_vide(self, grille: list[int]) -> list[int]:
        tab_pattern = grille[:]
        for i in range(0, NOMBRE_CASES):
            if tab_pattern[i] not in self.paterne:
                tab_pattern[i] = -1
        return tab_pattern

    def pattern_study(self, grille_resolue: list[int]) -> list[int]:
        tab_pattern = grille_resolue[:]
        for i in range(0, NOMBRE_CASES):
            if tab_pattern[i] not in self.paterne and tab_pattern[i] != -1:
                tab_pattern[i] = -2
        return tab_pattern


def deplacement(n):
    """n correspond à la taille du tableau : nxn. Pour un tableau 3x3 n=3"""
    liste_deplacement = (1, -1, n, -n)

    def swap(l, i, j):
        l[i], l[j] = l[j], l[i]

    def depl(plateau_courant):
        expansion = []
        k = next(iter(plateau_courant))
        plateau2 = list(k)
        cost = plateau_courant.get(k)
        pos_case_vide = plateau2.index(-1)
        for d in liste_deplacement:
            plateau = plateau2[:]
            if d == -n:
                if not (0 <= pos_case_vide < n):
                    if plateau[pos_case_vide-n] != -2:
                        cost += 1
                    swap(plateau, pos_case_vide, pos_case_vide - n)
                    expansion.append((plateau, cost))

            elif d == n:
                if not (n * n - n <= pos_case_vide < n * n):
                    if plateau[pos_case_vide+n] != -2:
                        cost += 1
                    swap(plateau, pos_case_vide, pos_case_vide + n)
                    expansion.append((plateau, cost))
            elif d == -1:
                if not (pos_case_vide in [x for x in range(0, n * n, n)]):
                    # [x for x in range(0, n*n, n)] -> permet de créer une liste par palier de n si n =3 on aura: [0,3,6]
                    if plateau[pos_case_vide-1] != -2:
                        cost += 1
                    swap(plateau, pos_case_vide, pos_case_vide - 1)
                    expansion.append((plateau, cost))
            elif d == 1:
                if not (pos_case_vide in [x for x in range(n - 1, n * n, n)]):
                    # [x for x in range(n-1, n*n, n)] -> permet de créer une liste par palier de n en commençant par n-1 : si n =3 on aura: [2,5,8]
                    if plateau[pos_case_vide + 1] != -2:
                        cost += 1
                    swap(plateau, pos_case_vide, pos_case_vide + 1)
                    expansion.append((plateau, cost))
        return expansion

    return depl


def create_SQL_table():
    try:
        databases = sqlite3.connect("pa_db.db")
    except Error as e:
        print(e)
    databases.isolation_level = None
    cur = databases.cursor()
    cur.execute("DROP TABLE IF EXISTS paterne;")
    cur.execute(
        "CREATE TABLE paterne(table_id TEXT PRIMARY KEY , cout INTEGER);")
    cur.execute("BEGIN TRANSACTION;")
    cur.execute("COMMIT;")
    databases.close()


writing_in_disk_semaphore = threading.Semaphore(1)

PATERN = [[0, 1, 2, 4, 5], [3, 6, 7, 10, 11], [8, 9, 12, 13, 14]]


def write_disk(data: dict):
    writing_in_disk_semaphore.acquire()
    databases = None
    try:
        databases = sqlite3.connect("pa_db.db")
    except Error as e:
        print(e)
    databases.isolation_level = None
    cur = databases.cursor()
    cur.execute("BEGIN TRANSACTION;")
    print("writting")
    for k, v in data.items():
        cur.execute("INSERT INTO paterne VALUES (?, ?);",
                    (str(k), v))
    cur.execute("COMMIT;")
    print("finish")
    databases.close()
    writing_in_disk_semaphore.release()


def generer_grille_resolue():
    n = DIM_GRILLE
    grille = [i % (n*n) for i in range(0, n*n-1)]
    grille.append(-1)
    return grille


def pattern_study(grille_resolue: list[int], pattern: list[int]):
    tab_pattern = grille_resolue[:]
    for i in range(0, NOMBRE_CASES):
        if tab_pattern[i] not in pattern and tab_pattern[i] != -1:
            tab_pattern[i] = -2
    return tuple(tab_pattern)


if __name__ == '__main__':
    set_dim_grille(4)
    create_SQL_table()
    grille_resolue = generer_grille_resolue()
    print(len(PATERN))
    calculating_threads = [threading.Thread()] * len(PATERN)
    generator = []
    for i in range(len(PATERN)):
        generator.append(Generation_paterne_db(deplacement(DIM_GRILLE)))
        calculating_threads[i] = threading.Thread(
            target=lambda: write_disk(generator[i].bfs(pattern_study(grille_resolue, PATERN[i]), PATERN[i])))
        calculating_threads[i].start()
    for i in range(len(PATERN)):
        calculating_threads[i].join()
