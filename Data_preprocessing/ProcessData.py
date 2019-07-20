# -*- coding: utf-8 -*-
from datetime import datetime
from ratp import stationSequences
import unicodedata

def stripAccents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def msgUniformed(msg):
    # This function is intended to unify/classify the msg
    # so it will be easier to analyze later
    #####

    # msg can be :
    # time like 22:33 or
    # ["A l'approche Voie 2", 'Départ Voie 2B', 'Train sans arrêt',
    #  'Départ Voie B', "A l'approche Voie 2B", "Train à l'approche",
    #  "A l'approche V.2B", 'Départ Voie 1B', 'Départ Voie 3',
    #  'Train à quai', 'Train à quai V.2B', 'Train retardé',
    #  "A l'approche V.2", 'Train à quai V.2', 'Sans arrêt V.2']
    
    msg = stripAccents(msg)
    
    if msg.startswith("A l'approche") or msg in ["Train a l'approche"] or msg in ["Train  l'approche"]:
        return 'coming'
    elif msg.startswith("Train a quai") or msg in ["Train  quai"]:
        return 'arrive'
    elif msg == 'Train retarde':
        return 'late'
    elif 'Depart' or 'Dpart' in msg:
        return 'depart'
    elif msg.startswith('Sans arret') or msg in ['Train sans arret'] or msg in ['Train sans arrt']:
        return 'pass'
    elif msg == 'Supprime':
        return 'deleted'
    elif msg.startswith('Train terminus'):
        return 'terminal'
    elif msg.startswith('Sans voyageurs'):
        return 'notraveler'
    elif msg.startswith('Stationne'):
        return 'park'
    elif msg in ['Voie 2', 'Voie Z', 'Voie 2B']:
        # 20170520060815,Laplace,ILAS,201705200608,true,Voie 2,ERAN,201705200609,201705200657
        # 20170520060522,Laplace,ERAN,201705200605,true,Voie Z,ERAN,201705200609,201705200657
        return 'arrive'
    elif msg[2] == ':':
        return msg
    else:
        print('msg unknown: '+msg)
        return msg

def msgSet(data):
    # This function is intended to get all types of msgs in data
    # If msgUniformed() prints too many unknown msgs,
    # we can use this function to find the unknown types of msgs
    #####

    msgList = []
    for mid in data.keys():
        for stationName in data[mid].keys():
            for log in data[mid][stationName]:
                msg = log['msg']
                if msg[2] != ':':
                    msgList.append(msg)
    return list(set(msgList))

def file2data(filename):
    # Recover data from log file
    with open(filename, 'r', errors='ignore') as f_log:
        lines = f_log.read().splitlines()
        data = {}
        # perturbations = []
        for line in lines:
            items = line.split(',')
            if(items[0] != 'perturbation'):
                if(len(items) >= 6):
                    # items = [logTime, stationName, midE, arrivalTimeE, stop, msg]
                    # or    = [logTime, stationName, midE, arrivalTimeE, stop, msg, midT, arrivalTimeT, terminalTime]
                    [logTime, stationName, midE, arrivalTimeE, stop, msg] = items[:6]
                    # unify msg
                    msg = msgUniformed(msg)
                    # correct msg
                    # if msg = 05:29 Voie 2 and logTime = 20170520052925
                    # set the msg to 'arrive' manually
                    # also because of the bug of substraction of datetime
                    if msg[2] == ':' and msg[:2] == logTime[-6:-4] and msg[3:5] == logTime[-4:-2]:
                        msg = 'sametime'

                    if midE not in data:
                        data[midE] = {}
                    if stationName not in data[midE]:
                        data[midE][stationName] = []
                    d = {'msg':msg, 'arrivalTimeE':arrivalTimeE, 'logTime':logTime, 'stop':stop}
                    if len(items) == 9:
                        [midT, arrivalTimeT, terminalTime] = items[-3:]
                        d.update({'midT':midT, 'arrivalTimeT':arrivalTimeT, 'terminalTime':terminalTime})
                    data[midE][stationName].append(d)
            #else:
                # process perturbations
    return data

def data2table(data):
    # dig out the real arrival time
    arrivalTimetable = {}
    for mid in data.keys():
        arrivalTimetable[mid] = {}
        for stationName in data[mid].keys():
            arrivalTimetable[mid][stationName] = []

            msg = ''
            new = True          # a flag to mark a new mission
            coming = False      # a flag to mark that mission is coming
            # depart = False      # depart
            for log in data[mid][stationName]:
                if log['stop'] == 'true':
                    msgPrev = msg
                    msg = log['msg']
                    if msg in ['depart','terminal']:
                        # ignore the depart messages for the moment
                        pass
                    else:
                        if new:
                            # we are processing a new mission
                            # once we start to process, it's no longer a new mission
                            new = False
                            if msg in ['park','arrive','deleted','sametime']:
                                # for a new mission, the mission is aleady arrived ?
                                # so this msg comes from the last mission
                                # because we have to observe 'coming' msg before observing 'arrive' msg
                                # or the msg is deleted, so the mission doesn't exist anymore
                                # so we restart
                                new = True
                            elif msg[2] == ':' or msg in ['late','coming']:
                                # we note the first estimated arrival time to as the estimated arrival time since it may change
                                arrivalTimeE = log['arrivalTimeE']
                                arrivalTimeT = ''   # default
                                if 'midT' in log:
                                    if mid == log['midT']:
                                        arrivalTimeT = log['arrivalTimeT']
                                if msg == 'coming':
                                    # the mission is coming
                                    coming = True
                        else:
                            # we continue to process the msgs of a mission
                            if msg == 'deleted':
                                # mission annulled so reset the flags
                                new = True
                                coming = False
                            elif msg == 'coming':
                                # the mission is coming
                                coming = True
                            elif msg in ['arrive','park','sametime']:
                                # we treat 'park', 'sametime' as 'arrive'
                                if coming or msgPrev[2] == ':' or msg == 'late':
                                    # if we observed 'coming' msg before observing 'arrive' msg
                                    # or if we didn't observe 'coming' msg but the previous msg is like '18:28'
                                    arrivalTimeR = log['logTime']
                                    if arrivalTimeT == '':
                                        arrivalTimetable[mid][stationName].append({'E':arrivalTimeE,'R':arrivalTimeR})
                                    else:
                                        arrivalTimetable[mid][stationName].append({'E':arrivalTimeE,'R':arrivalTimeR,'T':arrivalTimeT})
                                    # we have finished processing the msgs of a mission
                                    new = True
                                    coming = False
                                else:
                                    pass
                                    # print('%s, %s arrive at %s without coming and msg = %s, msgPrev = %s' % (log['logTime'], mid, stationName, msg, msgPrev))
                            else:
                                assert msg[2] == ':' or msg == 'late'
    return arrivalTimetable

def main(stationList):
    lineId = 'RB'
    DEBUG = False

    # until May 27 2017, the information of stations after Chatelet isn't disponible
    # missedstations = ['Gare du Nord', 'La Plaine-Stade de France', 'Aubervilliers', 'Le Bourget', 'Drancy', 'Blanc-Mesnil', 'Aulnay Sous Bois', 'Sevran Beaudottes', 'Villepinte', 'Parc des Expositions', 'Aeroport Ch.De Gaulle 1', 'Aeroport Ch.De Gaulle 2', 'Sevran-Livry', 'Vert-Galant', 'Villeparisis Mitry', 'Mitry-Claye']
    # station names
    # stationList = ['Saint Remy les Chevreuse', 'Courcelle Sur Yvette', 'Gif Sur Yvette', 'La Hacquiniere', 'Bures Sur Yvette', 'Orsay Ville', 'Le Guichet', 'Lozere', 'Palaiseau Villebon', 'Palaiseau', 'Massy Palaiseau', 'Massy Verrieres', 'Les Baconnets', 'Fontaine Michalon', 'Antony', 'La Croix de Berny', 'Parc de Sceaux', 'Bourg la Reine', 'Bagneux', 'Arcueil Cachan', 'Laplace', 'Gentilly', 'Cite Universitaire', 'Denfert Rochereau', 'Port Royal', 'Luxembourg', 'Saint Michel', 'Chatelet', 'Gare du Nord', 'La Plaine-Stade de France', 'Aubervilliers', 'Le Bourget', 'Drancy', 'Blanc-Mesnil', 'Aulnay Sous Bois', 'Sevran Beaudottes', 'Villepinte', 'Parc des Expositions', 'Aeroport Ch.De Gaulle 1', 'Aeroport Ch.De Gaulle 2', 'Sevran-Livry', 'Vert-Galant', 'Villeparisis Mitry', 'Mitry-Claye', 'Robinson', 'Fontenay aux Roses', 'Sceaux']
    # delete some stations
    # stationList = [station for station in stationList if station not in missedstations]

    # station sequences
    seq = stationSequences(lineId)
    # delete some stations
    for mid in seq.keys():
        seq[mid] = [station for station in seq[mid] if station in stationList]

    # the log file that we are going to analyze
    filelist = ['log_20170516050030_RB-A','log_20170518050054_RB-A',\
                'log_20170519050317_RB-A','log_20170520044135_RB-A',\
                # files below are obtained from server
                 'log_20170521140359_RB-A','log_20170522063243_RB-A',\
                 'log_20170523040002_RB-A','log_20170524040001_RB-A',\
                 'log_20170525040002_RB-A','log_20170526040001_RB-A',\
                 'log_20170527040002_RB-A','log_20170528040001_RB-A',\
                 'log_20170529040001_RB-A','log_20170530040002_RB-A',\
                 'log_20170531040002_RB-A','log_20190512110952_RB-A',\
                 'log_20190512111451_RB-A','log_20190512111715_RB-A',\
                 'log_20190512111923_RB-A','log_20190512112200_RB-A',\
                 'log_20190512112608_RB-A','log_20190512113735_RB-A',\
                 'log_20190512131213_RB-A','log_20190512135710_RB-A',\
                 'log_20190512181850_RB-A','log_20190512221306_RB-A',\
                 'log_20190512222723_RB-A','log_20190513000837_RB-A',\
                 'log_20190513053112_RB-A','log_20190513113422_RB-A',\
                 'log_20190514153311_RB-A','log_20190514192003_RB-A',\
                 'log_20190519171923_RB-A','log_20190519185321_RB-A']

    # timetable list
    timetableList = []
    for filename in filelist:
        print('Processing %s' % filename)
        filename = './log/'+filename+'.txt'
        # retrieve data from log file
        data = file2data(filename)

        # delete those unknown missionId
        keys = list(data.keys())
        for mid in keys:
            if mid not in seq.keys():
                if DEBUG and mid[0] != 'W' and mid[2] != 'W':
                # missions like W*W* don't take any travellers
                    print('Unknown missionId: %s' % mid)
                data.pop(mid, None)

        # delete the station where train shouldn't stop
        # delete some empty lists too
        for mid in data.keys():
            stationNames = list(data[mid].keys())
            for stationName in stationNames:
                if stationName not in seq[mid]:
                    data[mid].pop(stationName, None)

        # observe the type of msgs
        # log_20170520044135_RB-A :
        # ['pass', 'coming', 'arrive', 'deleted', 'latedepart', 'depart', 'late', 'park']
        if DEBUG:
            print(msgSet(data))

        arrivalTimetable = data2table(data)
        timetableList.append(arrivalTimetable)
    
    # delete strange mission who pass less than 2 stations
    for timetable in timetableList:
        midList = list(timetable.keys())
        for mid in midList:
            if len(timetable[mid].keys()) < 2:
                timetable.pop(mid, None)
            
    # find the timeline for each mission
    for itable in range(len(timetableList)):
        timetable = timetableList[itable]
        for mid in timetable.keys():
            seqLocal = [station for station in stationList if station in timetable[mid].keys()]
            assert set(seqLocal) == set(timetable[mid].keys())
            for i in range(len(seqLocal)-1):
                station0 = seqLocal[i]
                station1 = seqLocal[i+1]
                # print('table %d %s %s %d | %s %d' % (itable, mid, station0,len(timetable[mid][station0]),station1,len(timetable[mid][station1])))
                arrivalTimeListR0 = [datetime.strptime(mission['R'],'%Y%m%d%H%M%S') for mission in timetable[mid][station0]]
                arrivalTimeListR1 = [datetime.strptime(mission['R'],'%Y%m%d%H%M%S') for mission in timetable[mid][station1]]
                j0 = 0
                j1 = 0
                topop0 = []
                topop1 = []
                while j0 < len(arrivalTimeListR0) and j1 < len(arrivalTimeListR1):
                    time0 = arrivalTimeListR0[j0]
                    time1 = arrivalTimeListR1[j1]
                    if time0 <= time1:
                        if (time1.minute - time0.minute) % 60 > 10: # time here need to be adjusted because sometimes the stations are far enough
                            topop0.insert(0, j0)
                            j0 += 1
                        else:
                            #print('%02d:%02d | %02d:%02d'% (time0.hour,time0.minute,time1.hour,time1.minute))
                            j0 += 1
                            j1 += 1
                    else:
                        topop1.insert(0, j1)
                        j1 += 1
                # delete useless informations
                while j0 < len(arrivalTimeListR0):
                    topop0.insert(0, j0)
                    j0 += 1
                while j1 < len(arrivalTimeListR1):
                    topop1.insert(0, j1)
                    j1 += 1
                for j0 in topop0:
                    timetable[mid][station0].pop(j0)
                for j1 in topop1:
                    timetable[mid][station1].pop(j1)
            for i in range(len(seqLocal)-1,0,-1):
                station0 = seqLocal[i-1]
                station1 = seqLocal[i]
                # print('table %d %s %s %d | %s %d' % (itable, mid, station0,len(timetable[mid][station0]),station1,len(timetable[mid][station1])))
                arrivalTimeListR0 = [datetime.strptime(mission['R'],'%Y%m%d%H%M%S') for mission in timetable[mid][station0]]
                arrivalTimeListR1 = [datetime.strptime(mission['R'],'%Y%m%d%H%M%S') for mission in timetable[mid][station1]]
                j0 = 0
                j1 = 0
                topop0 = []
                topop1 = []
                while j0 < len(arrivalTimeListR0) and j1 < len(arrivalTimeListR1):
                    time0 = arrivalTimeListR0[j0]
                    time1 = arrivalTimeListR1[j1]
                    if time0 <= time1:
                        if (time1.minute - time0.minute) % 60 > 10: # time here need to be adjusted because sometimes the stations are far enough
                            topop0.insert(0, j0)
                            j0 += 1
                        else:
                            #print('%02d:%02d | %02d:%02d'% (time0.hour,time0.minute,time1.hour,time1.minute))
                            j0 += 1
                            j1 += 1
                    else:
                        topop1.insert(0, j1)
                        j1 += 1
                # delete useless informations
                while j0 < len(arrivalTimeListR0):
                    topop0.insert(0, j0)
                    j0 += 1
                while j1 < len(arrivalTimeListR1):
                    topop1.insert(0, j1)
                    j1 += 1
                for j0 in topop0:
                    timetable[mid][station0].pop(j0)
                for j1 in topop1:
                    timetable[mid][station1].pop(j1)
            # assert that we have some observations for each station
            # except the start
            if len(seqLocal) > 1:
                num = len(timetable[mid][seqLocal[1]])
                for station in seqLocal[1:]:
                    if num != len(timetable[mid][station]):
                        print(num,station)
                        print(timetable[mid][station])
                        assert False
            else:
                print(itable, mid, seqLocal)
        # delete those mission that we didn't observe a continue mission
        midList = list(timetable.keys())
        for mid in midList:
            if len(timetable[mid][list(timetable[mid].keys())[1]]) == 0:
                timetable.pop(mid, None)

    # get the list of mission ids and check that stationList contains all the stations
    missionIdList = []
    mid2seq = {}    # the relation between mission id -> sequence of station
    for timetable in timetableList:
        # check all the station is included in stationList
        for mid in timetable.keys():
            if mid not in missionIdList:
                missionIdList.append(mid)
                seqLocal = [station for station in stationList if station in timetable[mid].keys()]
                mid2seq[mid] = seqLocal
            if not set(timetable[mid].keys()) <= set(stationList):
                print('missing stations in stationList : '+list(set(timetable[mid].keys()) - set(stationList)))
    seq2mid = {}    # the relation between sequence of station -> mission id
    for mid in mid2seq.keys():
        seq = ','.join(mid2seq[mid])
        if seq not in seq2mid.keys():
            seq2mid[seq] = []
        seq2mid[seq].append(mid)
    # equivalence between mission ids
    midEq = {}
    for seq in seq2mid.keys():
        for mid in seq2mid[seq]:
            midEq[mid] = seq2mid[seq][0]
    
    Dict = {mid:[] for mid in list(set(midEq.values()))}
    for timetable in timetableList:
        for mid in timetable.keys():
            seqLocal = [station for station in stationList if station in timetable[mid].keys()]
            for i in range(len(timetable[mid][seqLocal[0]])):
                latenessList = []
                for station in stationList:
                    if station in seqLocal:
                        mission = timetable[mid][station][i]
                        timeE = datetime.strptime(mission['E'],'%Y%m%d%H%M')
                        timeR = datetime.strptime(mission['R'][:-2],'%Y%m%d%H%M')
                        lateness = ((timeR-timeE).seconds if timeE < timeR else -(timeE-timeR).seconds) // 60
                        latenessList.append(lateness)
                    else:
                        latenessList.append(None)
                Dict[midEq[mid]].append(latenessList)
#    numTotal = 0
#    for mid in Dict.keys():
#        numTotal += len(Dict[mid])
#    print('%d records' % numTotal)
    
    filename = 'analyseLog_%s.txt' % (datetime.now().strftime('%Y%m%d%H%M%S'))
    with open(filename, 'w+') as f:
        for mid in list(set(midEq.values())):
            f.write('%s %d\n' % (mid, len(Dict[mid])))
            f.write('%s\n' % ','.join(mid2seq[mid]))
    return Dict

if __name__ == '__main__':
    # study only bewtween Cite Universitaire -> Chatelet
    stationList = ['Cite Universitaire', 'Denfert Rochereau', 'Port Royal', 'Luxembourg', 'Saint Michel', 'Chatelet']
    Dict = main(stationList)
    data = Dict['EPOL']
    data = [item for item in data if None not in item]
    print('Data Set has %d examples' % len(data))
    
    filename = 'data_Cite2Chateletbis.txt'
    with open(filename, 'w+') as f:
        for item in data:
            f.write(','.join(map(str,item))+'\n')