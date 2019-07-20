# -*- coding: utf-8 -*-
"""
Created on Fri May 10 20:12:59 2019
’
@author: thibautbadoual
"""

import requests
import xml.etree.ElementTree as ET
import datetime

url="http://129.104.201.23/wsiv/services/Wsiv?wsdl="

# Cette fonction renvoie la liste des stations d'une ligne
# Par exemple lineId = "M6", "RB", etc
def getListStations(lineId):

    headers = {'content-type': 'text/xml', 'SOAPAction': 'urn:getStations'}
    body  = '<soapenv:Envelope xmlns:soapenv=\'http://schemas.xmlsoap.org/soap/envelope/\' \
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
                </soapenv:Envelope>'% (lineId)
    response = requests.post(url,data=body,headers=headers)
    data = response.content
    xml = ET.fromstring(data)
    stationsElements = xml.findall(".//{http://wsiv.ratp.fr/xsd}stations/{http://wsiv.ratp.fr/xsd}name")
    stations = [e.text for e in stationsElements]
    return stations

# Cette fonction convertit l'heure du format 20190519193600 au format 2019-05-19T19:36:00
# Objectif = gagner en lisibilité
def conversion_heure(s):
    t = datetime.datetime(int(s[:4]), int(s[4:6]), int(s[6:8]), int(s[8:10]), int(s[10:12])) 
    return t.isoformat()

# Cette fonction renvoie l'heure d'arrivée des prochains trains dans une gare donnée
# Par exemple lineId = "M6", direction = "A", station = "Nation"
def getStationsDates(lineId, direction, station):
    sol=[]
    
    headers = {'content-type': 'text/xml', 'SOAPAction': 'urn:getMissionsNext'}
    body  = '<soapenv:Envelope xmlns:soapenv=\'http://schemas.xmlsoap.org/soap/envelope/\' \
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
                       </wsiv:getMissionsNext>\n \
                    </soapenv:Body>\n \
                </soapenv:Envelope>'% (lineId, station, direction)
    response = requests.post(url,data=body,headers=headers)
    data = response.content
    xml = ET.fromstring(data)
    x = xml.findall(".//{http://wsiv.ratp.fr/xsd}stationsDates")
    nextTrains = [e.text for e in x] 
    # On convertit les horaires dans le bon format
    for h in nextTrains:
        sol+=[conversion_heure(h)]
    return sol
    