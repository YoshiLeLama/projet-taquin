import numpy as np
import sqlite3 as sql

BOARD_WIDTH = 4
WDTBL_SIZE = 24964

TABLE: list[list[int]] = []
for i in range(0, BOARD_WIDTH):
    TABLE.append([])
    for j in range(0, BOARD_WIDTH):
        TABLE[i].append(0)

u64 = np.ulonglong

WDTOP, WDEND = 0, 1
WDPTN = [u64(0)] * WDTBL_SIZE
WDTBL = [0] * WDTBL_SIZE
WDLNK: list[list[list[np.short]]] = []
for i in range(0, WDTBL_SIZE):
    WDLNK.append([])
    for j in range(0, 2):
        WDLNK[i].append([])
        for k in range(0, BOARD_WIDTH):
            WDLNK[i][j].append(np.short(0))


U64_SEVEN = u64(7)
U64_THREE = u64(3)
U64_EIGHT = u64(8)


def write_disk():
    i: int
    j: int
    k: int
    work: list[int] = [0] * 8
    table: u64

    con = sql.connect("walking_distance.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE distances(ptn, tbl)")

    for i in range(WDTBL_SIZE):
        cur.execute("INSERT INTO distances VALUES (" + str(WDPTN[i]) + ", " + str(WDTBL[i]) + ")")
        con.commit()

    con.close()


def write_table(count: int, vect: int, group: int):
    global WDEND, WDTOP, WDPTN, WDTBL, WDLNK, TABLE
    i: int
    j: int
    k: int
    table = u64(0)

    for i in range(0, 4):
        for j in range(0, 4):
            table = u64(np.bitwise_or(u64(np.left_shift(table, U64_THREE)), u64(TABLE[i][j])))
    i = 0
    while True:
        i += 1
        if i >= WDEND or np.equal(WDPTN[i], table):
            break

    if i == WDEND:
        WDPTN[WDEND] = table
        WDTBL[WDEND] = count
        WDEND += 1
        for j in range(0, 2):
            for k in range(0, 4):
                WDLNK[i][j][k] = WDTBL_SIZE

    j = WDTOP - 1
    WDLNK[j][vect][group] = i
    WDLNK[i][vect ^ 1][group] = j



def simulation():
    global WDEND, WDTOP, WDPTN, WDTBL, WDLNK, TABLE
    i: int
    j: int
    k: int
    space: int = 0
    piece: int
    count: int
    table: u64

    #  On met la table à 0
    for i in range(0,4):
        for j in range(0,4):
            TABLE[i][j]=0

    # On donne à la diagonale la valeur 4 sauf pour tout en bas à droite

    TABLE[0][0] = TABLE[1][1] = TABLE[2][2] = 4
    TABLE[3][3] = 3
    table = u64(0)

    for i in range(0,4):
        for j in range(0,4):
            table = u64(np.bitwise_or(u64(np.left_shift(table, U64_THREE)), u64(TABLE[i][j])))

    # la première valeur de WPDTN est def comme étant table, t celle de WDTBL comme étant 0
    WDPTN[0]= table
    WDTBL[0] = 0

    # On remplit le premier tableau de WDLNK avec WDTBL_SIZE

    for j in range(0,2):
        for k in range(0,4):
            WDLNK[0][j][k] = WDTBL_SIZE

    WDTOP = 0
    WDEND = 1

    while WDTOP < WDEND :
        # On prend la valeur de l'identifiant de la table de l'état à expanser
        table = WDPTN[WDTOP]
        # Cout de l'état à expanser
        count = WDTBL[WDTOP]
        # On incrémente l'indice de l'état à explorer après
        WDTOP += 1
        # le nb de coups est incremente
        count += 1

        # On reproduit la table à partir de l'identifiant (opérations inverses)

        #  7 == 111b
        #  ...000 | 011 = 011 & 111 = 011 < - valeur de la case
        #  table | val = bloc de 3 dans table & 7 = val
        for i in range(3,-1,-1) :
            piece=0
            for j in range(3,-1,-1):
                TABLE[i][j] = int(np.bitwise_and(table, U64_SEVEN))
                table = np.right_shift(table, U64_THREE)
                piece += TABLE[i][j]
            if piece == 3:
                space = i
        # Déplacer la pièce vers le haut 
        # piece = bloc de 4 en dessous de la case vide
        piece = space + 1
        if piece < 4:
            for i in range (0,4):
                # Si le bloc considéré contient une pièce du groupe i,
                # on fait monter la pièce et descendre la case vide
                if TABLE[piece][i] != 0:
                    TABLE[piece][i] -= 1
                    TABLE[space][i] += 1
                    #  On calcule la Walking distance de la table obtenue
                    write_table(count, 0, i)
                    # On remet la table comme avant
                    TABLE[piece][i] += 1
                    TABLE[space][i] -= 1
        # Déplacer la pièce vers le bas
        # piece = bloc de 4 au dessus de la case vide
        piece = space - 1
        if piece >= 0:
            # Si le bloc considéré contient une pièce du groupe i,
            # on fait descendre la pièce et monter la case vide
            for i in range(0,4):
                if TABLE[piece][i] != 0:
                    TABLE[piece][i] -= 1
                    TABLE[space][i] += 1
                    #  On calcule la Walking distance de la table obtenue
                    write_table(count, 1, i)
                    # On remet la table comme avant
                    TABLE[piece][i] += 1
                    TABLE[space][i] -= 1











if __name__ == "__main__":
    print("making")
    simulation()
    print("finish")
    write_disk()
    