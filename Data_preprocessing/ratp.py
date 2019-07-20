# -*- coding: utf-8 -*-
import http.client
import xmltodict
import zlib

def getStations(lineId):
    # This function is intended to use RATP API to get a dict
    # which contains two dicts : 'name2id', 'id2name'
    # for every station of 'lineId'
    #   'name2id' maps its name to its geoPointA_id-geoPointR_id
    #   'id2name' maps its geoPointA_id-geoPointR_id to its name
    # This function returns a dict {'name2id':name2id, 'id2name':id2name}
    #####
    
    # parameters for SOAP requests
    conn = http.client.HTTPConnection('129.104.201.23')
    headers = {
        'content-type': 'text/xml',
        'soapaction': '\'\'',
        'accept-encoding': "gzip,deflate",
        'cache-control': 'no-cache'
        }
    
    # send requests
    payload = '<soapenv:Envelope xmlns:soapenv=\'http://schemas.xmlsoap.org/soap/envelope/\' \
                                 xmlns:xsd=\'http://wsiv.ratp.fr/xsd\' \
                                 xmlns:wsiv=\'http://wsiv.ratp.fr\'>\n \
                   <soapenv:Header/>\n \
                   <soapenv:Body>\n \
                       <wsiv:getStations>\n \
                           <wsiv:station>\n \
                               <xsd:line>\n \
                                   <xsd:id>%s</xsd:id>\n \
                               </xsd:line>\n \
                           </wsiv:station>\n \
                       </wsiv:getStations>\n \
                    </soapenv:Body>\n \
                </soapenv:Envelope>' % (lineId)
    conn.request('POST', '/wsiv/services/Wsiv', payload, headers)
    # res = xmltodict.parse(conn.getresponse().read().decode('utf-8'))
    res = xmltodict.parse(zlib.decompress(conn.getresponse().read(), 16+zlib.MAX_WBITS))
    res = res['soapenv:Envelope']['soapenv:Body']['ns2:getStationsResponse']['ns2:return']['stations']
    
    # processing data
    name2id = {}
    id2name = {}
    for station in res:
        name = station['name']
        idA = station['geoPointA']['id']
        idR = station['geoPointR']['id']
        name2id[name] = idA+'-'+idR
        id2name[idA] = name
        id2name[idR] = name
    return {'name2id':name2id, 'id2name':id2name}

def getMissionsNext(lineId, stationName, direction, limit):
    # This function is intended to use RATP API to get the infos of the next mission
    # for the line 'lineId' in direction 'direction' at station 'stationName'
    # limit is the number of missions that we request
    #####
    
    # the definitions of A and R is different for theoretical/real timetable
    # here direction A for RER B is defined as Saint-Remy-les-Chevreuse -> CDG
    if lineId.isdigit():
        direction = 'A' if direction == 'R' else 'R'
    
    # parameters for SOAP requests
    conn = http.client.HTTPConnection('129.104.201.23')
    headers = {
        'content-type': 'text/xml',
        'soapaction': '\'\'',
        'accept-encoding': "gzip,deflate",
        'cache-control': 'no-cache'
        }
    
    # send requests
    payload = '<soapenv:Envelope xmlns:soapenv=\'http://schemas.xmlsoap.org/soap/envelope/\' \
                                 xmlns:xsd=\'http://wsiv.ratp.fr/xsd\' \
                                 xmlns:wsiv=\'http://wsiv.ratp.fr\'>\n \
                   <soapenv:Header/>\n \
                   <soapenv:Body>\n \
                       <wsiv:getMissionsNext>\n \
                           <wsiv:station>\n \
                               <xsd:line>\n \
                                   <xsd:id>%s</xsd:id>\n \
                               </xsd:line>\n \
                               <xsd:name>%s</xsd:name>\n \
                           </wsiv:station>\n \
                           <wsiv:direction>\n \
                               <xsd:sens>%s</xsd:sens>\n \
                           </wsiv:direction>\n \
                           <wsiv:limit>%d</wsiv:limit>\n \
                       </wsiv:getMissionsNext>\n \
                    </soapenv:Body>\n \
                </soapenv:Envelope>' % (lineId, stationName, direction, limit)
    conn.request('POST', '/wsiv/services/Wsiv', payload, headers)
    # res = xmltodict.parse(conn.getresponse().read().decode('utf-8'))
    res = xmltodict.parse(zlib.decompress(conn.getresponse().read(), 16+zlib.MAX_WBITS))
    res = res['soapenv:Envelope']['soapenv:Body']['ns2:getMissionsNextResponse']['ns2:return']
    
    # processing data
    data = {}
    if lineId.isalpha():
    # lineId is alphabetic, so we are aksing for the real timetable
        # possible perturbations
        if 'perturbations' in res:
            data['perturbations'] = res['perturbations']
        # missions
        missions = []
        if 'missions' in res:
            resMissions = res['missions']
            if isinstance(resMissions, dict):
                # only one mission
                resMissions = [resMissions]
            for i in range(len(resMissions)) :
                mid = resMissions[i]['id']
                msg = resMissions[i]['stationsMessages']
                mission = {'id':mid, 'msg':msg}
                if 'stations' in resMissions[i]:
                    if isinstance(resMissions[i]['stations'],list):
                        mission['dest'] = resMissions[i]['stations'][1]['name']
                if 'stationsDates' in resMissions[i]:
                    mission['time'] = resMissions[i]['stationsDates']
                if 'stationsStops' in resMissions[i]:
                    mission['stop'] = resMissions[i]['stationsStops']
                missions.append(mission)
            data['missions'] = missions
    else:
    # lineId isn't alphabetic, so we are aksing for the theoretical timetable
        # missions
        missions = []
        if('missions' in res):
            resMissions = res['missions']
            if isinstance(resMissions, dict):
                # only one mission
                resMissions = [resMissions]
            for i in range(len(resMissions)) :
                mid = resMissions[i]['id']
                dest = resMissions[i]['stations'][1]['name']
                mission = {'id':mid, 'dest':dest}
                mission['arrivalTime'] = resMissions[i]['stationsDates'][0]
                mission['terminalTime'] = resMissions[i]['stationsDates'][1]
                missions.append(mission)
            data['missions'] = missions
    return data

def getMission(lineId, missionId):
    # parameters for SOAP requests
    conn = http.client.HTTPConnection('129.104.201.23')
    headers = {
        'content-type': 'text/xml',
        'soapaction': '\'\'',
        'accept-encoding': "gzip,deflate",
        'cache-control': 'no-cache'
        }
    payload = '<soapenv:Envelope xmlns:soapenv=\'http://schemas.xmlsoap.org/soap/envelope/\' \
                                 xmlns:xsd=\'http://wsiv.ratp.fr/xsd\' \
                                 xmlns:wsiv=\'http://wsiv.ratp.fr\'>\n \
                   <soapenv:Header/>\n \
                   <soapenv:Body>\n \
                       <wsiv:getMission>\n \
                           <wsiv:mission>\n \
                               <xsd:id>%s</xsd:id>\n \
                               <xsd:line>\n \
                                   <xsd:id>%s</xsd:id>\n \
                               </xsd:line>\n \
                           </wsiv:mission>\n \
                       </wsiv:getMission>\n \
                   </soapenv:Body>\n \
               </soapenv:Envelope>' % (missionId, lineId)
    conn.request('POST', '/wsiv/services/Wsiv', payload, headers)
    # processing data
    # res = xmltodict.parse(conn.getresponse().read().decode('utf-8'))
    res = xmltodict.parse(zlib.decompress(conn.getresponse().read(), 16+zlib.MAX_WBITS))
    res = res['soapenv:Envelope']['soapenv:Body']['ns2:getMissionResponse']['ns2:return']
    stationNames = []
    stationGeoPoints = []
    for station in res['mission']['stations']:
        stationNames.append(station['name'])
        stationGeoPoints.append(station['geoPointA']['id']+'-'+station['geoPointR']['id'])
    return {'stationNames':stationNames, 'stationGeoPoints':stationGeoPoints}

def missionIds(lineId):
    # This function is intended to use the files from RATP_GTFS_LINES
    # to get the dict  who matches the numerical id to the alphabetical id
    # for missions of line 'lineId'
    # The file should be in folder ./'lineId'/
    #####
    
    # processing data
    with open('./'+lineId+'/trips.txt') as f_trips:
        lines = f_trips.read().splitlines()
        # labels = ['route_id', 'service_id', 'trip_id', 'trip_headsign', 
        #           'trip_short_name', 'direction_id', 'shape_id']
        trips = {}
        for line in lines[1:]:
            items = line.split(',')
            trip_id = items[2][-7:] # for RER B the useful id is only the last seven numbers
            if trip_id[0] == '0':   # remove possible 0 at beginning
                trip_id = trip_id[1:]
            trip_headsign = items[3]
            if trip_id not in trips:
                trips[trip_id] = trip_headsign
            else:
                # make sure that the short id is not duplicated
                assert trips[trip_id] == trip_headsign
    return trips

def stationSequences(lineId):
    # This function is intended to get the station sequence for all the mission id
    # with the help of API and the files from RATP_GTFS_LINES
    # Because the result of getMission depends on the time and it's unstable
    #####
    
    # get the map between station's name and its id
    mapNameId = getStations(lineId)
    # get the map from numercial mission id to the alphabetical one
    mapId = missionIds(lineId)
    
    seq = {}
    midDone = []    # list of mission ids whose station sequence is known
    with open('./'+lineId+'/stop_times.txt') as f_stop_times:
        lines = f_stop_times.read().splitlines()
        # labels = ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 
        #           'stop_sequence', 'stop_headsign', 'shape_dist_traveled']
        for line in lines[1:]:
            items = line.split(',')
            trip_id = items[0][-7:] # for RER B the useful id is only the last seven numbers
            if trip_id[0] == '0':   # remove possible 0 at beginning
                trip_id = trip_id[1:]
            mid = mapId[trip_id]
            stop_name = mapNameId['id2name'][items[3]]
            stop_sequence = items[4]
    
            if mid not in seq:
            # first see this mission, then it must begins with 1
                assert stop_sequence == '1'
                seq[mid] = [stop_name]
            elif mid not in midDone:
            # have seen this mission
                if stop_sequence == '1':
                # it's a new sequence
                # we supppose that for the same mission id, the sequence is same
                # so we mark it as done
                    midDone.append(mid)
                else:
                # it's a unfinished sequence
                    seq[mid].append(stop_name)
    return seq