#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import requests
from pymongo import MongoClient
import json

client = MongoClient()
db = client.blackmailedDB
mainCollection = db.mainCollection
geoipCollection = db.geoipCollection


def hash_check(hash_sha1):

    if db.geoipCollection.find().count() > 0:
        if not db.geoipCollection.find({'email_hash': hash_sha1}).count() == 0:
            hashResult = True
        else:
            hashResult = False
    else:
        hashResult = False
    return(hashResult)

print((mainCollection.count()))

for post in mainCollection.find():
    messageSHA1 = post['email_hash']
    print(messageSHA1)
    boolValue = hash_check(messageSHA1)
    if boolValue is False:
        geoip_dict = {}
        for x in list(post['email_header'].keys()):
            temp = str(x)

            if re.search(r'Received', temp):
                if re.search(r'\[', post['email_header'][x]):
                    try:
                        IPAddress = post['email_header'][x].split('[')[1].split(']')[0].encode('UTF-8', 'strict')
                        r = requests.get('http://localhost:8080/json/' + IPAddress)
                        geoipDict = json.loads(r.text)
                        geoip_dict['email_hash'] = post['email_hash']
                        geoip_dict[temp] = geoipDict
                        print(geoip_dict)
                        print(temp)

                    except:
                        geoip_dict['email_hash'] = post['email_hash']
                        geoip_dict[temp] = 'Domain not resolved'
                        print(geoip_dict)
                        print(temp)

                else:
                    rxTemp = re.match(r'from(.*)by(.*)with(.*)for(.*);(.*)', post['email_header'][x].encode('UTF-8', 'strict'))
                    if rxTemp:
                        if re.search(r'(\S+)\.(\S+)', rxTemp.group(1)):
                            Domain = rxTemp.group(1).strip().encode('UTF-8', 'strict')
                            print(('Line 73: ' + Domain))
                            if re.search(r'%RND', Domain):
                                geoipDict = Domain + ': Contains invalid escape for a Domain.'
                            else:
                                try:
                                    r = requests.get('http://localhost:8080/json/' + Domain)
                                    print(r)
                                    reqResult = str(r.text)
                                    print((reqResult[:3]))
                                    if reqResult[:3] == '404':
                                        geoipDict = Domain + ': Could not be resolved'
                                    else:
                                        geoipDict = json.loads(reqResult)

                                except Exception:
                                    geoipDict = Domain + ': Lookup timed out.'

                            geoip_dict['email_hash'] = post['email_hash']
                            geoip_dict[temp] = geoipDict
                            print(geoip_dict)
                            print(temp)

                        elif re.search(r'envelope-from <(\S+)>', rxTemp.group(3)):
                            Domain = rxTemp.group(2).strip().encode('UTF-8', 'strict')

                            try:
                                r = requests.get('http://localhost:8080/json/' + Domain)
                                geoipDict = json.loads(r.text)
                                geoip_dict['email_hash'] = post['email_hash']
                                geoip_dict[temp] = geoipDict
                                print(geoip_dict)
                                print(temp)

                            except:
                                geoip_dict['email_hash'] = post['email_hash']
                                geoip_dict[temp] = Domain + ': Could not be resolved'
                                print(geoip_dict)
                                print(temp)

                        else:
                            print('No match!')
        geoipCollection.insert(geoip_dict)
