# -*- coding: utf-8 -*-
from datetime import datetime
import time
from multiprocessing import Process
import methods
from ratp import getStations, getMissionsNext, missionIds
import os

def monitor(lineId, stationName, direction, q, startTime, T, sleepMax, counter, trips):
    # This function is intended to create a process which
    # monitors the station 'stationName' of the line 'lineId' at direction 'direction'
    # until time = startTime + T
    # It sends requests regularly o get the next mission (real/theoretical),
    # then it sends the msgs to the queue 'q' so that the printer process can write it into log file
    # It uses also a 'counter' (queue) to count the number of requests too
    # Moreover, we need to use the dict of numerical id - alphabetical id to unify the msg to print
    #####
    
    # derive the alphabetical id ('lineIdR', real) and the numerical id ('lineIdT', theoretical)
    lineIdR = lineId[0]
    lineIdT = lineId[1]
    assert lineIdR.isalpha() and lineIdT.isdigit()
    
    count = 0   # number of requests
    # start to monitor
    while((datetime.now()-startTime).seconds <= T):
        count += 2
        # request for the next mission
        timestamp = datetime.now()
        dataMissionsNextR = getMissionsNext(lineIdR, stationName, direction, 1)
        dataMissionsNextT = getMissionsNext(lineIdT, stationName, direction, 1)
        sleeptime = 25      # default sleeptime
        # text to print
        text2qR = ''
        text2qT = ''
        # if the next mission (real) exist
        if 'missions' in dataMissionsNextR:
            nextMissionR = dataMissionsNextR['missions'][0]
            msg = nextMissionR['msg']
            if 'time' in nextMissionR:
                if 'stop' in nextMissionR:
                    text2qR = timestamp.strftime('%Y%m%d%H%M%S')+','+stationName+','+nextMissionR['id']+','+nextMissionR['time']+','+nextMissionR['stop']+','+msg
                if msg[2] == ':':
                    arrivalTimeE = datetime.strptime(nextMissionR['time'],'%Y%m%d%H%M')
                    if arrivalTimeE > timestamp:
                        # sometimes arrivalTimeE is smaller than time now
                        # 201705202313 < 20170520231315
                        # and time2wait can be very big like 86340
                        time2wait = (arrivalTimeE - timestamp).seconds
                        if time2wait > 60:
                            # wait more time if the next train will not arrive in one minute
                            # but wait at most sleepMax seconds
                            sleeptime = min(time2wait - 60, sleepMax)
        # if the next mission (theoretical) exist
        if 'missions' in dataMissionsNextT:
            nextMissionT = dataMissionsNextT['missions'][0]
            if nextMissionT['id'] in trips:
                text2qT = trips[nextMissionT['id']] + ',' + nextMissionT['arrivalTime'] + ',' + nextMissionT['terminalTime']
        # log only if the next mission (real) exist
        if text2qR != '':
            if text2qT != '':
                q.put(text2qR+','+text2qT+'\n')
            else:
                q.put(text2qR+'\n')
        # possible perturbations
        if 'perturbations' in dataMissionsNextR:
            perturbations = dataMissionsNextR['perturbations']
            if isinstance(perturbations, dict):
                    perturbations = [perturbations]
            for perturbation in perturbations:
                level = perturbation['level']
                msg = perturbation['message']['text']
                if level != 'info' \
                    and not msg.startswith('Les informations horaires ne sont pas disponibles pour le moment') \
                    and not msg.startswith("Les informations horaires de l'ensemble de la ligne ne sont pas disponibles"):
                    # if there is no more train, the msg is
                    # "Les informations horaires ne sont pas disponibles pour le moment. Veuillez nous excuser pour la gêne occasionnée."
                    # or "Les informations horaires de l'ensemble de la ligne ne sont pas disponibles pour le moment. Veuillez nous excuser pour la gène occasionnée."
                    q.put('perturbation,'+stationName+','+level+','+msg+'\n')
        # take a rest
        time.sleep(sleeptime)
    counter.put(count)

def printer(q, filename):
    # This function is intended to create a process which
    # print the messages in the queue 'q' to the file 'filename'
    #####
    # flag to know if we need to stop the printer
    flag = True
    while flag:
        # count the lines that it wrote and save the file regularly
        num = 0
        with open(filename, 'a') as f:
            while flag and num < 50:
                if q.qsize() > 0:
                    item = q.get()
                    if item == None:
                        # job finished
                        flag = False
                    else:
                        f.write(item)
                        num += 1

def main():
    # Main function
    #####
    
    # parameters for request
    # line Id : RA, M1, B139
    # direction A for RER B is Saint-Remy-les-Chevreuse -> CDG
    lineId = ['RB','78']
    direction = 'A'
    T = 21000      # runtime in seconds
    sleepMax = 60;
    # the log file
    filename = './log/log_%s_%s-%s.txt' % (datetime.now().strftime('%Y%m%d%H%M%S'), lineId[0], direction)
    # create the folder is it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # get the dict of numerical id - alphabetical id
    trips = missionIds(lineId[0])
    # get stations
    stationsNames = list(getStations(lineId[0])['name2id'].keys())
    # queue to receive logs
    q = methods.Queue()
    # counter of request
    counter = methods.Queue()
    # monitors for stations
    monitors = [Process(target=monitor, args=(lineId, stationName, direction, q, datetime.now(), T, sleepMax, counter, trips)) for stationName in stationsNames]
    # printer to write logs in file
    print2f = Process(target=printer, args=(q,filename))
 
    # start to monitor stations
    for m in monitors:
        m.daemon = True
        m.start()
    # start to print logs
    print2f.daemon = True   # When a process exits, it attempts to terminate all of its daemonic child processes.
    print2f.start()

    # wait until all the monitors finish their job
    for m in monitors:
        m.join()
    # tell the printer to stop
    q.put(None)
    # wait it to stop
    print2f.join()

    # count number of request
    count = 0
    while counter.qsize() > 0:
        count += counter.get()
    print('Finished with %d requests' % count)

if __name__ == '__main__':  # necessary for protecting main(), https://docs.python.org/2/library/multiprocessing.html#the-process-class
    main()
