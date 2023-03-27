# **************************************
# pattern databases generation
# **************************************

from collections import namedtuple
import threading
from enum import Enum
import sqlite3
from sqlite3 import Error


Etat = namedtuple('Etat', ['patterne_table', 'cout'])
Etat.__annotations__ = {
    'patterne_table': list[int], 'cout': int}

DIM_GRILLE: int
NOMBRE_TUILES: int
NOMBRE_CASES: int
# Patern pour un 4x4
PATERN = [[0, 1, 2, 4, 5], [3, 6, 7, 10, 11], [8, 9, 12, 13, 14]]
writing_in_disk_semaphore = threading.Semaphore(1)


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

# on créer la bd pour ensuite pouvoir la réutiliser plus tard.


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

# On calcul tous les états qu'on peut générer à partir de l'état choisie. Pour cela on devra faire tous les déplacement possible pour chaque tuile du paterne. De plus pour que l'état soit considéré il faut respecter la condition que le cout augmente de 1 comme on est sur une expension en largeur d'abord.


def expanse(etat_choisi: dict()) -> dict:
    result = dict()
    # variable qui permet de vérifier qu'un plateau n'est pas déjà généré.

    for d in [Card.NORD, Card.SUD, Card.OUEST, Card.EST]:
        depl = deplacement(d, etat_choisi)
        if depl is not None:
            result.update(depl)
    return result


def swap(l, i, j):
    l[i], l[j] = l[j], l[i]

# On va déplacer notre tuile cible et non la case vide. La tuile à déplacer dépend de notre paterne.


def deplacement(dir, state: dict):
    n = DIM_GRILLE
    k = next(iter(state))
    plateau = list(k)
    result = dict()
    cost = state.get(k)
    pos_case_vide = plateau.index(-1)
    if dir == Card.NORD:
        if 0 <= pos_case_vide < n:
            return None
        else:
            if plateau[pos_case_vide-n] != -2:
                cost = state.get(k)+1
            swap(plateau, pos_case_vide, pos_case_vide - n)
            result.update(
                {tuple(plateau): cost})
    elif dir == Card.SUD:
        if n * n - n <= pos_case_vide < n * n:
            return None
        else:
            if plateau[pos_case_vide+n] != -2:
                cost = state.get(k)+1
            swap(plateau, pos_case_vide, pos_case_vide + n)
            result.update(
                {tuple(plateau): cost})
    elif dir == Card.OUEST:
        if pos_case_vide in [x for x in range(0, n * n, n)]:
            return None
            # [x for x in range(0, n*n, n)] -> permet de créer une liste par palier de n si n =3 on aura: [0,3,6]
        else:
            if plateau[pos_case_vide-1] != -2:
                cost = state.get(k)+1
            swap(plateau, pos_case_vide, pos_case_vide - 1)
            result.update(
                {tuple(plateau): cost})
    elif dir == Card.EST:
        if pos_case_vide in [x for x in range(n - 1, n * n, n)]:
            return None
            # [x for x in range(n-1, n*n, n)] -> permet de créer une liste par palier de n en commençant par n-1 : si n =3 on aura: [2,5,8]
        else:
            if plateau[pos_case_vide+1] != -2:
                cost = state.get(k)+1
            swap(plateau, pos_case_vide, pos_case_vide + 1)
            result.update(
                {tuple(plateau): cost})
    return result

# générer le plateau en fct du parterne utilisé. On place toutes les tuiles comme des tuiles vides pour celles qui ne sont pas dans le patterne


def pattern_study(grille_resolue: list[int], pattern: list[int]) -> list[int]:
    tab_pattern = grille_resolue[:]
    for i in range(0, NOMBRE_CASES):
        if tab_pattern[i] not in pattern and tab_pattern[i] != -1:
            tab_pattern[i] = -2
    return tab_pattern
# Pour générer tous les coûts possible pour tous les paternes on utilisera une stratégie de largeur d'abord.


def suppression_de_la_case_vide(grille: list[int], pattern: list[int]) -> list[int]:
    tab_pattern = grille[:]
    for i in range(0, NOMBRE_CASES):
        if tab_pattern[i] not in pattern:
            tab_pattern[i] = -1
    return tab_pattern


def bfs(root: list[int], pattern: list[int]) -> dict:
    queue = dict()
    alrdy_found = dict()
    explored = dict()
    s = dict()
    queue.update({tuple(root): 0})
    alrdy_found.update({tuple(root): 0})
    # Un dictionnaire vide est évalué à faux.
    while bool(queue):
        # k permet de récuprer la position 0 du dictionnaire donc de la file. En vérité il donne la première clef
        position0 = next(iter(queue))
        selected = {position0: queue.pop(position0)}
        # s est le résultat de l'expension
        s = expanse(selected)
        for k, v in s.items():
            if k not in alrdy_found and k not in queue:
                queue.update({k: v})
                alrdy_found.update({k: v})
        explored.update(
            {tuple(suppression_de_la_case_vide(list(position0), pattern)): selected.pop(position0)})
    return explored


def generer_grille_resolue() -> list[int]:
    grille = []
    for i in range(0, DIM_GRILLE * DIM_GRILLE - 1):
        grille.append(i)
    grille.append(-1)
    return grille


if __name__ == '__main__':
    set_dim_grille(4)
    create_SQL_table()
    grille_resolue = generer_grille_resolue()
    calculating_threads = [threading.Thread()] * 3
    for i in range(3):
        calculating_threads[i] = threading.Thread(
            target=lambda: bfs(pattern_study(grille_resolue, PATERN[i]), PATERN[i]))
        calculating_threads[i].start()
    for i in range(3):
        calculating_threads[i].join()
    # bfs(pattern_study(grille_resolue, PATERN[0]), PATERN[0])
