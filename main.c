/**************************************************/
/*   １５パズル/WD用テーブル作成        puz15wd.c */
/*           Computer & Puzzle 2001/04 by takaken */
/**************************************************/
#include <stdio.h>
#include <stdlib.h>

#define  FALSE           0
#define  TRUE            1
#define  BOARD_WIDTH     4

#define  WDTBL_SIZE  24964 /* WalkingDistance TableSize */

typedef  unsigned __int64  u64;

int   TABLE[BOARD_WIDTH][BOARD_WIDTH];
// WDTOP correspond au nombre d'itérations dans Simuration
// WDEND correspond à la taille de la table
int   WDTOP, WDEND;
u64   WDPTN[WDTBL_SIZE];                 /* 局面パターン */ /* schéma de phase */
char  WDTBL[WDTBL_SIZE];                 /* 最短手数(WD) */ /* nombre minimum de coups (WD) */
short WDLNK[WDTBL_SIZE][2][BOARD_WIDTH]; /* 双方向リンク */ /* tableau de liens bidirectionnels */

/*********************************************/
/* 探索結果のテーブルをディスクに保存する    */
/*********************************************/
void WriteDisk(void)
{
    int  i, j, k, work[8];
    u64 table;
    char *filename = "sql.txt";
    FILE *fp;

    fp = fopen(filename, "wb");
    /*for (i=0; i<WDTBL_SIZE; i++) {
        *//* WDPTN *//*
        table = WDPTN[i];
        for (j=7; j>=0; j--,table>>=8)
            work[j] = (int)(table & 0xff);
        for (j=0; j<8; j++)
            fputc(work[j], fp);
        *//* WDTBL *//*
        fputc(WDTBL[i], fp);
        *//* WDLNK *//*
        for (j=0; j<2; j++)
        for (k=0; k<4; k++) {
            fputc(WDLNK[i][j][k]  >> 8 , fp);
            fputc(WDLNK[i][j][k] & 0xff, fp);
        }
    }*/

    char sql_command[200];

    for (i=0; i < WDTBL_SIZE; i++) {
        sprintf(sql_command, "INSERT INTO distances VALUES (%lld, %d);\n", WDPTN[i], WDTBL[i]);
        fputs(sql_command, fp);
    }

    fclose(fp);
}
/*********************************************/
/* パターンの登録と双方向リンクの形成        */
/*********************************************/
void WriteTable(char count, int vect, int group)
{
    int  i, j, k;
    u64  table;

    /* 同一パターンを探す */
    // Recherche de modèles identiques
    table =0;
    for (i=0; i<4; i++)
    for (j=0; j<4; j++)
        table = (table << 3) | TABLE[i][j];
    for (i=0; i<WDEND; i++)
        if (WDPTN[i] == table) break;

    /* 新規パターン登録 */
    // Enregistrement d'un nouveau modèle
    if (i == WDEND) {
        // On ajoute l'indentifiant du modèle
        WDPTN[WDEND] = table;
        // On ajoute la walking distance correspondante
        WDTBL[WDEND] = count;
        WDEND++;
        // On remplit le i-ème tableau de WDLNK avec WDTBL_SIZE
        for (j=0; j<2; j++)
        for (k=0; k<4; k++)
            WDLNK[i][j][k] = WDTBL_SIZE;
    }

    /* 双方向リンクを形成させる */
    // Formation d'un lien bidirectionnel
    //
    j = WDTOP - 1;
    WDLNK[j][vect    ][group] = (short)i;
    WDLNK[i][vect ^ 1][group] = (short)j;
}
/*********************************************/
/* 幅優先探索でWalkingDistanceを求める       */
/*********************************************/
void Simuration(void)
{
    int  i, j, k, space=0, piece;
    char count;
    u64  table;

    /* 初期面を作る */
    // On met la table à 0
    for (i=0; i<4; i++)
    for (j=0; j<4; j++)
        TABLE[i][j] = 0;

    // On donne à la diagonale la valeur 4 sauf pour tout en bas à droite
    TABLE[0][0] = TABLE[1][1] = TABLE[2][2] = 4;
    TABLE[3][3] = 3;
    table =0;

    // Calcul valeur magique jsp ce que ça fait
    for (i=0; i<4; i++)
    for (j=0; j<4; j++)
        table = (table << 3) | TABLE[i][j];

    /* 初期面を登録 */
    // La première valeur de WDPTN est définie comme étant table, et celle de WDTBL comme étant 0
    WDPTN[0] = table;
    WDTBL[0] = 0;

    // On remplit le premier tableau de WDLNK avec WDTBL_SIZE
    for (j=0; j<2; j++)
    for (k=0; k<4; k++) {
        WDLNK[0][j][k] = WDTBL_SIZE;
    }

    /* 幅優先探索 */
    WDTOP=0; WDEND=1;
    while (WDTOP < WDEND) {
        /* TABLE[][]呼び出し */
        // On prend la valeur de l'identifiant de la table de l'état à expanser
        table = WDPTN[WDTOP];
        // Cout de l'état à expanser
        count = WDTBL[WDTOP];
        // On incrémente l'indice de l'état à explorer après
        WDTOP++;
        // Le nombre de coups est incrémenté
        count++;

        /* TABLE[][]再現 */
        // On reproduit la table à partir de l'identifiant (opérations inverses)

        // 7 == 111b
        // ...000 | 011 = 011                   & 111 = 011 <- valeur de la case
        // table  | val = bloc de 3 dans table & 7   = val
        for (i=3; i>=0; i--) {
            piece = 0;
            for (j=3; j>=0; j--) {
                TABLE[i][j] = (int)(table & 7);
                table >>= 3;
                piece += TABLE[i][j];
            }
            // Si on ne trouve que 3 pièces dans la ligne, alors la case vide y est
            if (piece == 3) space = i;
        }

        /* 0:駒を上に移動 */
        // Déplacer la pièce vers le haut
        // piece = bloc de 4 en dessous de la case vide
        if ((piece = space + 1) < 4) {
            for (i=0; i<4; i++) {
                // Si le bloc considéré contient une pièce du groupe i,
                // on fait monter la pièce et descendre la case vide
                if (TABLE[piece][i]) {
                    TABLE[piece][i]--;
                    TABLE[space][i]++;
                    // On calcule la Walking distance de la table obtenue
                    WriteTable(count, 0, i);
                    // On remet la table comme avant
                    TABLE[piece][i]++;
                    TABLE[space][i]--;
                }
            }
        }

        /* 1:駒を下に移動 */
        // Déplacer la pièce vers le bas
        // piece = bloc de 4 au dessus de la case vide
        if ((piece = space - 1) >= 0) {
            // Si le bloc considéré contient une pièce du groupe i,
            // on fait descendre la pièce et monter la case vide
            for (i=0; i<4; i++) {
                if (TABLE[piece][i]) {
                    TABLE[piece][i]--;
                    TABLE[space][i]++;
                    // On calcule la Walking distance de la table obtenue
                    WriteTable(count, 1, i);
                    // On remet la table comme avant
                    TABLE[piece][i]++;
                    TABLE[space][i]--;
                }
            }
        }
    }
}
int main(void)
{
    printf("making......\n");
    Simuration();
    printf("saving......\n");
    WriteDisk();
    printf("finish!\n");

    return 0;
}