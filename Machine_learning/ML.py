# Algorithmes de comparaison
import pandas
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn import model_selection
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC

# On enregistre les données
names = ['station1', 'station2', 'station3', 'station4', 'station5','station6']
dataframe = pandas.read_csv('data_Cite2Chatelet.csv', names=names)

# On affiche les neuf graphiques entre les résultats de la station "" et ceux de la station ""
sns.pairplot(dataframe, vars=names, size=2);

array = dataframe.values
X = array[:,0:5]
Y = array[:,5]

# On prépare l'ensemble des modèles
models = []
models.append(('LR', LogisticRegression()))
models.append(('LDA', LinearDiscriminantAnalysis()))
models.append(('KNN', KNeighborsClassifier()))
models.append(('CART', DecisionTreeClassifier()))
models.append(('NB', GaussianNB()))
models.append(('SVM', SVC()))

# On commence par entrainer et tester nos données en deux sets
# C'est la méthode la plus classique
for name, model in models:
    # On découpe l'échantillon en une plage de test et une autre d'entrainement
    X_train, X_test, Y_train, Y_test = model_selection.train_test_split(X, Y, test_size=0.2)
    # On entraine l'algorithme choisi
    model.fit(X_train, Y_train)
    # On prévoit le résultat sur un échantillon afin de déterminer la précision du modèle
    Y_predict = model.predict(X_test)
    plt.scatter(Y_test, Y_predict)
    print ("Train/Test split " + name + ":", model.score(X_test, Y_test))

# La deuxième méthode consiste à faire de la "Cross Validation"
# Le principe est très similaire au Train/Test split
# On divise maintenant la base en k sets et on l'entraine sur k-1
# Le dernier permet de tester
# La moyenne des précisions donne la précision finale

# results est la liste des résultats des différents algorithmes
results = []
# name correspond aux noms des algorithmes de recherche
names = []
scoring = 'accuracy'

# On évalue chaque modèle un par un
for name, model in models:
    # kfold permet de découper l'échantillon en plage de test afin de l'entrainer de façon arbitraire
	kfold = model_selection.KFold(n_splits=10, random_state='None')
    # On stocke les résultats dans cv_results
	cv_results = model_selection.cross_val_score(model, X, Y, cv=kfold, scoring=scoring)
    # On stocke les noms et les résultats dans les variables results et names pour le graphique final
	results.append(cv_results)
	names.append(name)
    # On affiche les résultats sous forme: nom du modèle, précision et la déviation standard
	msg = "%s: %f (%f)" % (name, cv_results.mean(), cv_results.std())
	print("Cross Validation " + msg)
    
# On affiche un graphe comprant l'ensemble des algorithmes implémentés
fig = plt.figure()
fig.suptitle('Algorithm Comparaison')
ax = fig.add_subplot(111)
plt.boxplot(results)
ax.set_xticklabels(names)
plt.show()