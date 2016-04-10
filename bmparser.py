#!/usr/bin/env python
import sys
import re
import hashlib
from pymongo import MongoClient
import bson

client = MongoClient()
db = client.blackmailedDB
mainCollection = db.mainCollection

file_name = sys.argv[1]
emails_raw = open(file_name, "r")
email_temp = ''
received_count = 1


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

x = 0

for line in emails_raw:
    temp_line = line.replace('\r\n', '\n')  # convert to standard Unix return values
    email_temp += temp_line

    if re.match(r'\.\n', temp_line):  # find end of email

        messageSHA1 = hashlib.sha1(email_temp).hexdigest()

        boolValue = hash_check(messageSHA1)

        if boolValue is True:
            #print('--------------------------------ALREADY HERE---------------------------------------')
            email_temp = ''  # Cleared to prepare for next email

        else:
            #print('-----------------------------NEW EMAIL INSERTED------------------------------------')
            email_split = email_temp.split('\n\n', 1)
            header_temp = email_split[0]
            body_temp = email_split[1]
            email_temp = ''  # Cleared to prepare for next email
            header_list = header_temp.split('\n')
            email_dict = {}
            email_dict['email_hash'] = messageSHA1
            email_dict['email_body'] = {}
            email_dict['email_header'] = {}
            header_temp = []  # reuse the header_temp

            # Processing the headers into a dictionary
            for x in range(len(header_list)):
                if re.match(r'(.*):', header_list[x]) and not re.match(r'\t|\s(.*)', header_list[x]):  # find email header categories
                    header_temp.append(header_list[x])
                elif re.match(r'\t|\s(.*)', header_list[x]):  # find email headers with \t or ' ' beginning
                    header_temp[len(header_temp) - 1] += header_list[x]
                else:
                    header_temp.append(header_list[x] + ': NONE')

            for y in range(len(header_temp)):
                header_list = header_temp[y].split(':', 1)
                header_list[0] = unicode_detect(header_list[0])
                header_list[0] = re.sub('\.', '_-_', header_list[0])
                if header_list[0] == 'Received':
                    header_list[0] = 'Received_' + str(received_count)
                    received_count += 1
                email_dict['email_header'][header_list[0]] = unicode_detect(header_list[1].lstrip())
            body_temp = unicode_detect(body_temp)
            email_dict['email_body']['body'] = body_temp
            mainCollection.insert(email_dict)
            received_count = 1

emails_raw.close()

