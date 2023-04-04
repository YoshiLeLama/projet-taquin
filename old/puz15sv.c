/**************************************************/
/*   �P�T�p�Y��/�����[�� with WD,ID     puz15sv.c */
/*           Computer & Puzzle 2001/04 by takaken */
/**************************************************/
/* Nécessite puz15wd.db de puz15wd.c pour s'exécuter*/
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define FALSE 0
#define TRUE 1
#define BOARD_WIDTH 4
#define BOARD_SIZE 16

#define WDTBL_SIZE 24964 /* WalkingDistance TableSize */
#define IDTBL_SIZE 106   /* InvertDistance TableSize  */

typedef unsigned __int64 u64;

int BOARD[BOARD_SIZE] = {
    3, 11, 9, 8, // sample
    6, 12, 7, 2,
    15, 10, 1, 13,
    4, 5, 14, 0};

u64 WDPTN[WDTBL_SIZE];                   /* tableau de motifs */
short WDLNK[WDTBL_SIZE][2][BOARD_WIDTH]; /* lien */
char WDTBL[WDTBL_SIZE];                  /* Tableau de calcul WD   */
char IDTBL[IDTBL_SIZE];                  /* Tableau de calcul ID   */
char RESULT[100];                        /* tableau d'enregistrement des réponses */
int DEPTH;                               /* limite de profondeur de recherche */
int MOVAL[BOARD_SIZE][5] = {             /* table mobile */
                            1, 4, -1, 0, 0,
                            2, 5, 0, -1, 0,
                            3, 6, 1, -1, 0,
                            7, 2, -1, 0, 0,
                            0, 5, 8, -1, 0,
                            1, 6, 9, 4, -1,
                            2, 7, 10, 5, -1,
                            3, 11, 6, -1, 0,
                            4, 9, 12, -1, 0,
                            5, 10, 13, 8, -1,
                            6, 11, 14, 9, -1,
                            7, 15, 10, -1, 0,
                            8, 13, -1, 0, 0,
                            9, 14, 12, -1, 0,
                            10, 15, 13, -1, 0,
                            11, 14, -1, 0, 0};
int CONV[BOARD_SIZE] = {/* Table de conversion d'aspect */
                        0,
                        1, 5, 9, 13,
                        2, 6, 10, 14,
                        3, 7, 11, 15,
                        4, 8, 12};

/*********************************************/
/* Préparation de diverses tables de référence                      */
/*********************************************/
void Initialize(void)
{
    int i, j, k, nextd;
    u64 table;
    char *filename = "puz15wd.db";
    FILE *fp;

    /* IDTBL[] */
    for (i = 0; i < 106; i++)
        IDTBL[i] = (char)((i / 3) + (i % 3));

    /* WDPTN[], WDTBL[], WDLNK[][][] */
    fp = fopen(filename, "rb");
    for (i = 0; i < WDTBL_SIZE; i++)
    {
        /* WDPTN */
        table = 0;
        for (j = 0; j < 8; j++)
            table = (table << 8) | getc(fp);
        WDPTN[i] = table;
        /* WDTBL */
        WDTBL[i] = (char)getc(fp);
        /* WDLNK */
        for (j = 0; j < 2; j++)
            for (k = 0; k < 4; k++)
            {
                nextd = getc(fp);
                WDLNK[i][j][k] = (short)((nextd << 8) | getc(fp));
            }
    }
    fclose(fp);
}
/*********************************************/
/* Retour en arrière avec approfondissement itératif          */
/*********************************************/
int IDA(int space, int prev, int idx1o, int idx2o, int inv1o, int inv2o, int depth)
{
    int i, j, n, n2, piece, wd1, wd2, id1, id2, diff;
    int idx1, idx2, inv1, inv2, lowb1, lowb2;

    /* essayez tout ce qui suit */
    depth++;
    for (i = 0;; i++)
    {
        // litteralement le poids à donner en fct de la position de la case vide
        piece = MOVAL[space][i]; /* Coordonnées de la pièce à déplacer */
        if (piece == -1)
            break; /* garde */
        if (piece == prev)
            continue;     /* Prévention des retouches de dernière minute */
        n = BOARD[piece]; /* Nombre de pièces à déplacer */

        /* Trouvez le (WD, ID) de la phase suivante en fonction de la direction de déplacement de la pièce */
        idx1 = idx1o;
        idx2 = idx2o;
        inv1 = inv1o;
        inv2 = inv2o;
        diff = piece - space;
        if (diff > 0)
        {
            if (diff == 4)
            {
                /* déplacer la pièce vers le haut */
                for (j = space + 1; j < piece; j++)
                    if (BOARD[j] > n)
                        inv1--;
                    else
                        inv1++;
                idx1 = WDLNK[idx1o][0][(n - 1) >> 2];
            }
            else
            {
                /* déplacer la pièce vers la gauche */
                n2 = CONV[n];
                for (j = space + 4; j < 16; j += 4)
                    if (CONV[BOARD[j]] > n2)
                        inv2--;
                    else
                        inv2++;
                for (j = piece - 4; j >= 0; j -= 4)
                    if (CONV[BOARD[j]] > n2)
                        inv2--;
                    else
                        inv2++;
                idx2 = WDLNK[idx2o][0][(n2 - 1) >> 2];
            }
        }
        else
        {
            if (diff == -4)
            {
                /* déplacer la pièce vers le bas */
                for (j = piece + 1; j < space; j++)
                    if (BOARD[j] > n)
                        inv1++;
                    else
                        inv1--;
                idx1 = WDLNK[idx1o][1][(n - 1) >> 2];
            }
            else
            {
                /* déplacer la pièce à droite */
                n2 = CONV[n];
                for (j = piece + 4; j < 16; j += 4)
                    if (CONV[BOARD[j]] > n2)
                        inv2++;
                    else
                        inv2--;
                for (j = space - 4; j >= 0; j -= 4)
                    if (CONV[BOARD[j]] > n2)
                        inv2++;
                    else
                        inv2--;
                idx2 = WDLNK[idx2o][1][(n2 - 1) >> 2];
            }
        }

        /* Borne inférieure */
        wd1 = WDTBL[idx1];
        wd2 = WDTBL[idx2];
        id1 = IDTBL[inv1];
        id2 = IDTBL[inv2];
        lowb1 = (wd1 > id1) ? wd1 : id1;
        lowb2 = (wd2 > id2) ? wd2 : id2;

        /* Appel récursif après vérification avec la méthode d'élagage de la limite inférieure */
        if (depth + lowb1 + lowb2 <= DEPTH)
        {
            BOARD[piece] = 0;
            BOARD[space] = n;
            if (depth == DEPTH || IDA(piece, space, idx1, idx2, inv1, inv2, depth))
            {
                RESULT[depth - 1] = (char)n; /* Enregistrez vos étapes de réponse */
                return TRUE;
            }
            BOARD[space] = 0;
            BOARD[piece] = n;
        }
    }
    return FALSE;
}
/*********************************************/
/* Résolvez 15 énigmes                         */
/*********************************************/
int Search(void)
{
    int space, num1, num2, idx1, idx2, inv1, inv2, wd1, wd2;
    int id1, id2, lowb1, lowb2, i, j, work[BOARD_WIDTH];
    int cnvp[] = {0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15};
    u64 table;

    /*Vérification de l'existence de la solution */
    for (space = 0; BOARD[space]; space++)
        ;
    inv1 = (BOARD_WIDTH - 1) - space / BOARD_WIDTH;
    for (i = 0; i < BOARD_SIZE; i++)
    {
        if (BOARD[i] == 0)
            continue;
        for (j = i + 1; j < BOARD_SIZE; j++)
            if (BOARD[j] && BOARD[j] < BOARD[i])
                inv1++;
    }
    if (inv1 & 1)
        return FALSE;

    /* IDX1 initial pour WD */
    table = 0;
    for (i = 0; i < BOARD_WIDTH; i++)
    {
        for (j = 0; j < BOARD_WIDTH; j++)
            work[j] = 0;
        for (j = 0; j < BOARD_WIDTH; j++)
        {
            num1 = BOARD[i * BOARD_WIDTH + j];
            if (num1 == 0)
                continue;
            work[(num1 - 1) >> 2]++;
        }
        for (j = 0; j < BOARD_WIDTH; j++)
            table = (table << 3) | work[j];
    }
    for (idx1 = 0; WDPTN[idx1] != table; idx1++)
        ;

    /* IDX2 initial pour WD */
    table = 0;
    for (i = 0; i < BOARD_WIDTH; i++)
    {
        for (j = 0; j < BOARD_WIDTH; j++)
            work[j] = 0;
        for (j = 0; j < BOARD_WIDTH; j++)
        {
            num2 = CONV[BOARD[j * BOARD_WIDTH + i]];
            if (num2 == 0)
                continue;
            work[(num2 - 1) >> 2]++;
        }
        for (j = 0; j < BOARD_WIDTH; j++)
            table = (table << 3) | work[j];
    }
    for (idx2 = 0; WDPTN[idx2] != table; idx2++)
        ;

    /* INV1 initial pour ID */
    inv1 = 0;
    for (i = 0; i < BOARD_SIZE; i++)
    {
        num1 = BOARD[i];
        if (!num1)
            continue;
        for (j = i + 1; j < BOARD_SIZE; j++)
        {
            num2 = BOARD[j];
            if (num2 && num2 < num1)
                inv1++;
        }
    }

    /* INV2 initial pour ID */
    inv2 = 0;
    for (i = 0; i < BOARD_SIZE; i++)
    {
        num1 = CONV[BOARD[cnvp[i]]];
        if (!num1)
            continue;
        for (j = i + 1; j < BOARD_SIZE; j++)
        {
            num2 = CONV[BOARD[cnvp[j]]];
            if (num2 && num2 < num1)
                inv2++;
        }
    }

    /* Limite inférieure initiale */
    wd1 = WDTBL[idx1];
    wd2 = WDTBL[idx2];
    id1 = IDTBL[inv1];
    id2 = IDTBL[inv2];
    lowb1 = (wd1 > id1) ? wd1 : id1;
    lowb2 = (wd2 > id2) ? wd2 : id2;
    printf("(WD=%d/%d,ID=%d/%d) LowerBound=%d\n", wd1, wd2, id1, id2, lowb1 + lowb2);

    /* Exécution de l'IDA */
    for (DEPTH = lowb1 + lowb2;; DEPTH += 2)
    {
        printf("-%d", DEPTH);
        if (IDA(space, -1, idx1, idx2, inv1, inv2, 0))
            break;
    }

    return TRUE;
}
int main(void)
{
    time_t start_time = time(NULL);
    int i;

    /* �e�Q�ƃe�[�u������ */
    Initialize();

    /* BOARD�\��(���ʕ\��) */
    for (i = 0; i < BOARD_SIZE; i++)
    {
        if (i && !(i % BOARD_WIDTH))
            printf("\n");
        printf("%3d", BOARD[i]);
    }
    printf("\n");

    /* �T�����Č��ʂ�\�� */
    if (Search())
    {
        printf("\n[%d moves] time=%dsec", DEPTH, time(NULL) - start_time);
        for (i = 0; i < DEPTH; i++)
        {
            if (i % 10 == 0)
                printf("\n");
            printf(" %2d ", RESULT[i]);
        }
        printf("\n");
    }
    else
    {
        printf("Impossible!!\n");
    }

    return 0;
}