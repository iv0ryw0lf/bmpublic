#!/usr/bin/env python
import sys
import re
import os
import hashlib
from pymongo import MongoClient
import bson

pathStr = sys.argv[1]
client = MongoClient()
db = client.blackmailedDB
mainCollection = db.mainCollection
os.chdir(pathStr)
print(pathStr)

emails_raw = ''
received_count = 1
print('\n')


def hash_check(hash_sha1):

    if db.mainCollection.find().count() > 0:
        if not db.mainCollection.find({'email_hash': hash_sha1}).count() == 0:
            hashResult = True
        else:
            hashResult = False
    else:
        hashResult = False
    return(hashResult)


def unicode_detect(test_value):

    try:
        #This code could deal with other encodings, like latin_1
        #but that's not the point here
        test_value.decode('utf-8')

    except UnicodeDecodeError:
        test_value = bson.binary.Binary(str(test_value))

    return(test_value)


def message_process(filename):

    print(filename)
    f = open(filename, 'r')
    emails_raw = f.read()
    f.close()
    emails_raw.replace('\r\n', '\n')  # convert to standard Unix return values
    if emails_raw[:5] == 'From ':
        emails_raw = emails_raw.split('\n', 1)[1]
    print(emails_raw)
    print(('SHA1 Hash: ' + hashlib.sha1(emails_raw).hexdigest()))
    messageSHA1 = hashlib.sha1(emails_raw).hexdigest()
    print(messageSHA1)

    while True:
        received_count = 1
        if hash_check(messageSHA1) is True:
            print('--------------------------------ALREADY HERE---------------------------------------')
            break

        else:
            email_split = emails_raw.split('\n\n', 1)
            header_temp = email_split[0]
            if len(email_split) == 2:
                body_temp = email_split[1]
            else:
                body_temp = ''
            emails_raw = ''  # Cleared to prepare for next email
            header_list = header_temp.split('\n')
            email_dict = {}
            email_dict['email_hash'] = messageSHA1
            email_dict['email_body'] = {}
            email_dict['email_header'] = {}
            header_temp = []  # reuse the header_temp

            # Processing the headers into a dictionary
            for x in range(len(header_list)):
                # find email header categories
                if re.match(r'(.*):', header_list[x]) and not re.match(r'\t|\s(.*)', header_list[x]):
                    header_temp.append(header_list[x])
                elif re.match(r'\t|\s(.*)', header_list[x]):  # find email headers with \t or ' ' beginning
                    header_temp[len(header_temp) - 1] += header_list[x]
                else:
                    header_temp.append(header_list[x] + ':NONE')
            print('Completed header list')
            for y in range(len(header_temp)):
                header_list = header_temp[y].split(':', 1)
                print(header_list)
                header_list[0] = unicode_detect(header_list[0])
                header_list[0] = re.sub('\.', '_-_', header_list[0])
                if header_list[0] == 'Received':
                    header_list[0] = 'Received_' + str(received_count)
                    received_count += 1
                email_dict['email_header'][header_list[0]] = unicode_detect(header_list[1].lstrip())
                # Another method to updating the dictionary
                # email_dict.update({email_header:{header_list[0]:header_list[1]}})

            body_temp = unicode_detect(body_temp)
            email_dict['email_body']['body'] = body_temp
            #email_dict.update({email_body:{'body':body_temp}})  # Another method to updating the dictionary
            print(('\n' + str(email_dict)))
            mainCollection.insert(email_dict)
            received_count = 1
            break

for files in os.listdir('.'):
    message_process(files)



