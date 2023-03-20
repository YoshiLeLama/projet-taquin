import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psutil
from io import StringIO
from mpl_toolkits import mplot3d
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression
from scipy import stats

if __name__ == '__main__':
    file = './bd_graphe_test-prg/data.csv'
    r = pd.read_csv(file)
    r.drop('Unnamed: 0', axis=1, inplace=True)
    print(r)
