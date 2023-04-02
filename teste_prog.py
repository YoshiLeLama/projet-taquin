import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression

# ajoute les données dans la bd à utiliser cette fct après avoir initialisé la bd
# Attention la Ram est exprimé en MiB et le GPU en %
# pour ma
file = './bd_graphe_test_prg/data.csv'
# pour linear conflict
file2 = './bd_graphe_test_prg/dataLC.csv'
# pour pa db
file3 = './bd_graphe_test_prg/dataPaDB.csv'


def panda_data(file, nb_etats_generer, nb_de_coup, utilisation_CPU, utilisation_RAM, nb_etat_frontiere, nb_etats_explorer, poids):
    data = {'nb_etats_generer': [nb_etats_generer],
            'nb_de_coup': [nb_de_coup],
            'utilisation_CPU': [utilisation_CPU],
            'utilisation_RAM': [utilisation_RAM],
            'nb_etat_frontiere': [nb_etat_frontiere],
            'nb_etats_explorer': [nb_etats_explorer],
            'categorie_de_poids': [poids]}

    # L'utilisation cpu est en pourcentage
    df = pd.DataFrame(data)

    df.to_csv(file, mode='a',  header=False)

    r = pd.read_csv(file)
    r.drop('Unnamed: 0', axis=1, inplace=True)
    # r.drop(df.filter(regex="Unnamed"), axis=1, inplace=True)
    r.to_csv(file)
    print(r)

# permet de faire un graphe en 3 dimention
# on pourrait mettre x,y,z et paramètre et faire r[x] avec x,y,z des strings.

# n représente le nombre de catégorie de poids considéré


def graphe_3d(file, n: list[int]):
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
    my_cmap = plt.get_cmap('Dark2', len(n))
    ax.set_xlabel('nombre de coup à faire', fontweight='bold')
    ax.set_ylabel('nb etat generer', fontweight='bold')
    ax.set_zlabel('nb etat frontiere', fontweight='bold')
    ctt = ax.scatter3D(x, y, z,
                       alpha=0.8,
                       c=r.categorie_de_poids,
                       cmap=my_cmap,
                       marker='.')
    fig.colorbar(ctt, ax=ax, ticks=range(len(n)), label='categorie de poids')
    plt.title("Taquin 3x3 graphe 3D")
    plt.show()


def graphe_3d_sans_color_bar(file):
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
    my_cmap = plt.get_cmap('Dark2')
    ax.set_xlabel('nombre de coup à faire', fontweight='bold')
    ax.set_ylabel('nb etat generer', fontweight='bold')
    ax.set_zlabel('nb etat frontiere', fontweight='bold')
    ctt = ax.scatter3D(x, y, z,
                       alpha=0.8,
                       c=r.nb_de_coup,
                       cmap=my_cmap,
                       marker='.')
    plt.title("Taquin 3x3 graphe 3D")
    plt.show()


# n=le nombre de graphe considéré (en fct du poids)
# X valeurs utilisées en absisse
# Y valeurs utilisées en ordonnée
# k représente kind soit le type du graphe
# subtitile représente le soustitre


def multi_graphe(file, n: list[int], X, Y, k, subtitle):
    r = pd.read_csv(file)
    matplotlib.style.use('Solarize_Light2')
    r.drop('Unnamed: 0', axis=1, inplace=True)
    df = []
    ax = []
    for i in n:
        df.append(r[r.categorie_de_poids == i])
    fig = plt.figure()
    fig.suptitle(
        subtitle, fontsize=16, y=0.1)
    for i in range(0, len(n)):
        ax.append(fig.add_subplot(3, 1, i+1))
        df[i].plot(x=X, y=Y, alpha=1,
                   kind=k, title="categorie de poids "+str(n[i]) if n[i] != 0 else "poids max", ax=ax[i])
    plt.show()


def graphe(file,  X, Y, k, subtitle):
    r = pd.read_csv(file)
    matplotlib.style.use('Solarize_Light2')
    r.drop('Unnamed: 0', axis=1, inplace=True)
    fig = plt.figure()
    r.plot(x=X, y=Y, alpha=1,
           kind=k, title=subtitle)
    plt.show()


# régression linéaire, un peut fouilli mais fct. La fct predict dans une boucle n'a pas l'aire de fonctionner...
def linear_reg(file, categorie_de_poids: list[int]):
    lin = LinearRegression()
    r = pd.read_csv(file)
    r.drop('Unnamed: 0', axis=1, inplace=True)
    plt.style.use('Solarize_Light2')
    df = []
    ax = []
    for i in categorie_de_poids:
        df.append(r[r.categorie_de_poids == i])
    fig = plt.figure()
    fig.suptitle(
        " Taquin 3x3 regression lineaire du nombre d'état explorer en fonction du nombre de coups pour 500 taquins", fontsize=16, y=0.1)
    matplotlib.style.use('Solarize_Light2')
    for i in range(1, len(categorie_de_poids)+1):
        ax.append(fig.add_subplot(3, 1, i))
    i = 0
    for dfi in df:
        lin.fit(dfi[["nb_de_coup"]], dfi["nb_etats_explorer"])
        aX = dfi.plot(x="nb_de_coup", y="nb_etats_explorer", alpha=1,
                      kind='scatter', title="categorie de poids"+str(categorie_de_poids[i]), ax=ax[i])
        aX.plot(dfi["nb_de_coup"], lin.predict(dfi[["nb_de_coup"]]), c='r')
        lin.score(dfi[["nb_de_coup"]], dfi["nb_etats_explorer"])
        i += 1

    plt.show()

# initilise la bd


def init_bd_data(file):
    df = pd.DataFrame({'nb_etats_generer': [],
                       'nb_de_coup': [],
                       'utilisation_CPU': [],
                       'utilisation_RAM': [],
                       'nb_etat_frontiere': [],
                       'nb_etats_explorer': [],
                       'categorie_de_poids': []})
    df.to_csv(file)


if __name__ == '__main__':
    file = './bd_graphe_test_prg/data.csv'
