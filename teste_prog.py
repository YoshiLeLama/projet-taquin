import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression

# ajoute les données dans la bd à utiliser cette fct après avoir initialisé la bd


def panda_data(nb_etats_generer, nb_de_coup, utilisation_CPU, nb_etat_frontiere, nb_etats_explorer, poids):
    global ligne
    data = {'nb_etats_generer': [nb_etats_generer],
            'nb_de_coup': [nb_de_coup],
            'utilisation_CPU': [utilisation_CPU],
            'nb_etat_frontiere': [nb_etat_frontiere],
            'nb_etats_explorer': [nb_etats_explorer],
            'categorie_de_poids': [poids]}

    # L'utilisation cpu est en pourcentage
    df = pd.DataFrame(data)

    df.to_csv('data.csv', mode='a',  header=False)

    r = pd.read_csv('data.csv')
    r.drop('Unnamed: 0', axis=1, inplace=True)
    # r.drop(df.filter(regex="Unnamed"), axis=1, inplace=True)
    r.to_csv('data.csv')
    print(r)

# permet de faire un graphe en 3 dimention
# on pourrait mettre x,y,z et paramètre et faire r[x] avec x,y,z des strings.


def graphe_3d(file):
    r = pd.read_csv(file)
    r.drop('Unnamed: 0', axis=1, inplace=True)
    fig = plt.figure(figsize=(16, 9))
    ax = plt.axes(projection="3d")
    x = r.nb_de_coup
    y = r.nb_etat_frontiere
    z = r.nb_etats_generer
    ax.grid(b=True, color=0,
            linestyle='-.', linewidth=0.3,
            alpha=0.2)
    my_cmap = plt.get_cmap('Dark2', 6)
    ax.set_xlabel('nombre de coup à faire', fontweight='bold')
    ax.set_ylabel('nb etat generer', fontweight='bold')
    ax.set_zlabel('nb etat frontiere', fontweight='bold')
    ctt = ax.scatter3D(x, y, z,
                       alpha=0.8,
                       c=r.categorie_de_poids,
                       cmap=my_cmap,
                       marker='.')
    fig.colorbar(ctt, ax=ax, ticks=range(7), label='categorie de poids')
    plt.title("Taquin 3x3 graphe 3D")
    plt.show()

# permet d'afficher n graphes en 1 seul fichier. Le k représente kind soit le type du graphe


def multi_graphe(file, n, X, Y, k, subtitle):
    r = pd.read_csv(file)
    matplotlib.style.use('Solarize_Light2')
    r.drop('Unnamed: 0', axis=1, inplace=True)
    df = []
    ax = []
    for i in range(1, n+1):
        df.append(r[r.categorie_de_poids == i])
    fig = plt.figure()
    fig.suptitle(
        subtitle, fontsize=16, y=0.1)
    for i in range(1, n+1):
        ax.append(fig.add_subplot(3, 3, i))
        df[i-1].plot(x=X, y=Y, alpha=1,
                     kind=k, title="categorie de poids "+str(i), ax=ax[i-1])
    plt.show()


# régression linéaire, un peut fouilli mais fct. La fct predict dans une boucle n'a pas l'aire de fonctionner...
def linear_reg(file):
    lin = LinearRegression()
    r = pd.read_csv(file)
    r.drop('Unnamed: 0', axis=1, inplace=True)
    plt.style.use('Solarize_Light2')
    df1 = r[r.categorie_de_poids == 1]
    df2 = r[r.categorie_de_poids == 2]
    df3 = r[r.categorie_de_poids == 3]
    df4 = r[r.categorie_de_poids == 4]
    df5 = r[r.categorie_de_poids == 5]
    df6 = r[r.categorie_de_poids == 6]
    lin.fit(df1[["nb_de_coup"]], df1["nb_etats_explorer"])
    matplotlib.style.use('Solarize_Light2')
    fig = plt.figure()
    fig.suptitle(
        " Taquin 3x3 regression lineaire du nombre d'état explorer en fonction du nombre de coups sans coef de normalisation", fontsize=16, y=0.1)
    ax1 = fig.add_subplot(3, 3, 1)
    ax2 = fig.add_subplot(3, 3, 2)
    ax3 = fig.add_subplot(3, 3, 3)
    ax4 = fig.add_subplot(3, 3, 4)
    ax5 = fig.add_subplot(3, 3, 5)
    ax6 = fig.add_subplot(3, 3, 6)
    aX0 = df1.plot(x="nb_de_coup", y="nb_etats_explorer", alpha=1,
                   kind='scatter', title="categorie de poids 1", ax=ax1)
    aX0.plot(df1["nb_de_coup"], lin.predict(df1[["nb_de_coup"]]), c='r')
    lin.score(df1[["nb_de_coup"]], df1["nb_etats_explorer"])

    aX2 = df2.plot(x="nb_de_coup", y="nb_etats_explorer", alpha=1,
                   kind='scatter', title="categorie de poids 2", ax=ax2)
    aX2.plot(df2["nb_de_coup"], lin.predict(df2[["nb_de_coup"]]), c='r')
    lin.score(df2[["nb_de_coup"]], df2["nb_etats_explorer"])

    aX3 = df3.plot(x="nb_de_coup", y="nb_etats_explorer", alpha=1,
                   kind='scatter', title="categorie de poids 3", ax=ax3)
    aX3.plot(df3["nb_de_coup"], lin.predict(df3[["nb_de_coup"]]), c='r')
    lin.score(df3[["nb_de_coup"]], df3["nb_etats_explorer"])

    aX4 = df4.plot(x="nb_de_coup", y="nb_etats_explorer", alpha=1,
                   kind='scatter', title="categorie de poids 4", ax=ax4)
    aX4.plot(df4["nb_de_coup"], lin.predict(df4[["nb_de_coup"]]), c='r')
    lin.score(df4[["nb_de_coup"]], df4["nb_etats_explorer"])

    aX5 = df5.plot(x="nb_de_coup", y="nb_etats_explorer", alpha=1,
                   kind='scatter', title="categorie de poids 5", ax=ax5)
    aX5.plot(df5["nb_de_coup"], lin.predict(df5[["nb_de_coup"]]), c='r')
    lin.score(df5[["nb_de_coup"]], df5["nb_etats_explorer"])

    aX6 = df6.plot(x="nb_de_coup", y="nb_etats_explorer", alpha=1,
                   kind='scatter', title="categorie de poids 6", ax=ax6)
    aX6.plot(df6["nb_de_coup"], lin.predict(df6[["nb_de_coup"]]), c='r')
    lin.score(df6[["nb_de_coup"]], df6["nb_etats_explorer"])
    plt.show()

# initilise la bd


def init_bd_data(file):
    df = pd.DataFrame({'nb_etats_generer': [],
                       'nb_de_coup': [],
                       'utilisation_CPU': [],
                       'nb_etat_frontiere': [], 'nb_etats_explorer': [], 'categorie_de_poids': []})
    df.to_csv(file)


if __name__ == '__main__':
    file = './bd_graphe_test_prg/data.csv'
