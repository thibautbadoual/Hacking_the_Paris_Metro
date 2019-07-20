import pandas as pd
import matplotlib.pyplot as plt

# On commence par lire toutes les données
dataTrips = pd.read_csv('RERB/trips.csv')
dataStopTimes = pd.read_csv('RERB/stop_times.csv')
dataCalendarDate = pd.read_csv('RERB/calendar_dates.csv')
dataStops = pd.read_csv('RERB/stops.csv')


def freqPassage(station,date):
    T = [0]*24
    dataDay = data.loc[data['date']==date,:]
    dataStation = dataDay.loc[dataDay['stop_name']==station,:]
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

# On fusionne toutes les tables qui nous intéressent sur les critères pertinents
data0 = pd.merge(dataTrips,dataCalendarDate,on='service_id',how="left")
data1 = pd.merge(data0,dataStopTimes,on='trip_id',how='left')
data = pd.merge(data1,dataStops,on='stop_id',how='left')


Lo = freqPassage('Lozère',20190811)
Cha = freqPassage('Châtelet-Les Halles',20190812)
Hour =  [k for k in range (24)]          
plt.plot(Hour,Lo)
plt.plot(Hour,Cha)
plt.ylabel('Number of trains')
plt.xlabel('hour of the day')
plt.xticks(range(0, 24))
plt.show()

# On calcule la probabilité qu'un train passant par Châtelet s'arrête à Lozère
X = ['No RER running']*24
for k in range (24):
    if Cha[k]!= 0 : 
        X[k]=((Lo[k]/Cha[k])*100)
    
print (X)


    