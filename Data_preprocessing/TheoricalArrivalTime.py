# -*- coding: utf-8 -*-
from ratp import getMission

# parameter
lineId = 'RB'

# processing data
with open('./'+lineId+'/trips.txt') as f_trips:
    lines = f_trips.read().splitlines()
    # labels = ['route_id', 'service_id', 'trip_id', 'trip_headsign', 
    #           'trip_short_name', 'direction_id', 'shape_id']
    labels = lines[0].split(',')
    trips = {}
    for line in lines[1:]:
        items = line.split(',')
        trip_id = items[2][-7:]
        trip_headsign = items[3]
        if trip_id not in trips:
            trips[trip_id] = trip_headsign
        else:
            # make sure that the short id is not duplicated
            assert trips[trip_id] == trip_headsign

with open('./'+lineId+'/stop_times.txt') as f_stop_times:
    lines = f_stop_times.read().splitlines()
    # labels = ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 
    #           'stop_sequence', 'stop_headsign', 'shape_dist_traveled']
    labels = lines[0].split(',')
    stop_times = {}
    for line in lines[1:]:
        items = line.split(',')
        trip_id = items[0][-7:]
        stop_id = items[3]
        arrival_time = items[1]
        mid = trips[trip_id]        
        if mid in stop_times:
            if stop_id not in stop_times[mid]:
                stop_times[mid][stop_id] = []
            stop_times[mid][stop_id].append(arrival_time)
        else:
            stop_times[mid]={stop_id : [arrival_time]}

missionId = 'EPOL'
lineId = 'RB'
stationName = 'Massy Palaiseau'

# get station-id for the mission
dataMission = getMission(lineId, missionId)

stationNames = dataMission['stationNames']
stationGeoPoints = dataMission['stationGeoPoints']

if stationName in stationNames:
    stationId = stationGeoPoints[stationNames.index(stationName)]
    if stationId[:4] in stop_times[missionId]:
        stationId = stationId[:4]
    elif stationId[-4:] in stop_times[missionId]:
        stationId = stationId[-4:]
    else:
        print('stationId not found')
else:
    print('station not found')

timelist = list(set(stop_times[missionId][stationId]))
timelist.sort()
for timestamp in timelist:
    print(timestamp[:5])