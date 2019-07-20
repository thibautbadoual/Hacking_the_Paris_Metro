import pandas as pd
import matplotlib.pyplot as plt

# On commence par lire toutes les données
dataTrips = pd.read_csv('M6/trips.csv')
dataStopTimes = pd.read_csv('M6/stop_times.csv')
dataCalendarDate = pd.read_csv('M6/calendar_dates.csv')
dataStops = pd.read_csv('M6/stops.csv')

# On fusionne toutes les tables qui nous intéressent sur les critères pertinents
data0 = pd.merge(dataTrips,dataCalendarDate,on='service_id',how="left")
data1 = pd.merge(data0,dataStopTimes,on='trip_id',how='left')
data = pd.merge(data1,dataStops,on='stop_id',how='left')

# Cette fonction détermine la fréquence de passage d'un train à une station donnée, une date fixée.
# Elle retourne un tableau de 24 cases correspondant aux 24 heures de la journée, 
# avec le nombre de trains passés par la station choisie à l'heure de la case.
def freqPassage(station,date):
    T = [0]*24
    dataDay = data.loc[data['date']==date,:]
    dataStation = dataDay.loc[dataDay['stop_name']==station,:]
    # On parcourt les horaires en rajoutant le nombre de train passée à une heure précise
    # k représente les heures
    # Impossible d'aller de 0 à 24 d'un coup car pour k<10 il faut rajouter un 0 devant 
    # i représente les minutes, de même obligation d'aller de 0 à 9 puis de 10 à 60
    for k in range (10) :
        for i in range (10):
            T[k]=T[k]+len(dataStation.loc[dataStation['arrival_time']=='0'+str(k)+':0'+str(i)+':00',:])
        for i in range (10, 60):
            T[k]=T[k]+len(dataStation.loc[dataStation['arrival_time']=='0'+str(k)+':'+str(i)+':00',:])            
    for k in range (10, 24):
        for i in range (10):
            T[k]=T[k]+len(dataStation.loc[dataStation['arrival_time']==str(k)+':0'+str(i)+':00',:])
        for i in range (10,60):
            T[k]=T[k]+len(dataStation.loc[dataStation['arrival_time']==str(k)+':'+str(i)+':00',:])        
    
    return T

# On affiche le résultat final
Na = freqPassage('Nation',20190602)
Hour =  [k for k in range (24)]          
plt.plot(Hour,Na)
plt.ylabel('Number of trains')
plt.xlabel('hour of the day')
plt.xticks(range(0, 24))
plt.show()

