
import os
import sys
import json
import collections
from collections import defaultdict
from urlparse import urlparse
import xlsxwriter
import gensim
from gensim import corpora

#appdir = sys.argv[1]
appdir =  os.path.dirname(os.path.realpath(__file__))
#exit()
fnames_X = []
fnames_Y = []
fnames_UI = []

USERLOGS_DIR = appdir+"/userlogs"

for fname in os.listdir(USERLOGS_DIR):
    if(fname!=".DS_Store" and '_X' in fname):
        fnames_X.append(fname)
for fname in os.listdir(USERLOGS_DIR):
    if(fname!=".DS_Store" and '_Y' in fname):
        fnames_Y.append(fname)
for fname in os.listdir(USERLOGS_DIR):
    if(fname!=".DS_Store" and '_UI' in fname):
        fnames_UI.append(fname)

fnames_UI.sort()
fnames_X.sort()
fnames_Y.sort()

apps = defaultdict(int)
persons = defaultdict(int)
keywords = defaultdict(int)
docs = defaultdict(int)

ALL_ENTITIES = {'keywords': [], 'people': [], 'applications': []}
for fname in fnames_X:
    data = json.load(open(os.path.join(USERLOGS_DIR,fname)))
    ALL_ENTITIES['keywords'] = ALL_ENTITIES['keywords'] + data['keywords']
    ALL_ENTITIES['people'] = ALL_ENTITIES['people'] + data['people']
    ALL_ENTITIES['applications'] = ALL_ENTITIES['applications'] + data['applications']
    temp_docs = defaultdict(int)
    for doc in data['document_ID']:
        temp_docs[doc[1]] = [doc[0],doc[3].replace('https://reknowdesktopsurveillance.hiit.fi','/var/www/html')]
        if len(temp_docs)>=10:
            break
    docs.update(temp_docs)
i_UI = 0
for fname in fnames_Y:
    data = json.load(open(os.path.join(USERLOGS_DIR,fname)))
    data_UI = json.load(open(os.path.join(USERLOGS_DIR,fnames_UI[i_UI])))
    ALL_ENTITIES['keywords'] = ALL_ENTITIES['keywords'] + data['keywords']
    ALL_ENTITIES['people'] = ALL_ENTITIES['people'] + data['people']
    ALL_ENTITIES['applications'] = ALL_ENTITIES['applications'] + data['applications']
    temp_docs = defaultdict(int)
    i_doc_UI = 0
    for doc in data['document_ID']:
        doc_UI = data_UI['document_ID'][i_doc_UI]
        if doc[1] not in temp_docs:
            temp_docs[doc[1]] = [doc_UI[0],doc[3].replace('https://reknowdesktopsurveillance.hiit.fi','/var/www/html')]
        if len(temp_docs)>=10:
            break
        i_doc_UI+=1
    newdocs = defaultdict(int)
    for key,val in temp_docs.iteritems():
        newdocs[key+"["+str(val[0])] = val
    docs.update(newdocs)
    i_UI+=1
for fname in fnames_UI:
    data = json.load(open(os.path.join(USERLOGS_DIR,fname)))
    ALL_ENTITIES['keywords'] = ALL_ENTITIES['keywords'] + data['keywords']
    ALL_ENTITIES['people'] = ALL_ENTITIES['people'] + data['people']
    ALL_ENTITIES['applications'] = ALL_ENTITIES['applications'] + data['applications']
    temp_docs = defaultdict(int)
    for doc in data['document_ID']:
        if doc[1] not in temp_docs:
            temp_docs[doc[1]] = [doc[0],doc[3].replace('https://reknowdesktopsurveillance.hiit.fi','/var/www/html')]
        if len(temp_docs)>=10:
            break
    newdocs = defaultdict(int)
    for key,val in temp_docs.iteritems():
        newdocs[key+"["+str(val[0])] = val
    docs.update(newdocs)
for keyword in ALL_ENTITIES['keywords']:
    keywords[keyword[1].replace('_',' ').lower()] += 1
for app in ALL_ENTITIES['applications']:
    apps[app[1].replace('_appname','').replace("_"," ").replace("."," ").lower()] += 1
for person in ALL_ENTITIES['people']:
    persons[person[1].replace('_',' ').lower()] += 1

keywords = collections.OrderedDict(sorted(keywords.items()))
persons = collections.OrderedDict(sorted(persons.items()))
apps = collections.OrderedDict(sorted(apps.items()))
docs = collections.OrderedDict(sorted(docs.items()))

workbook = xlsxwriter.Workbook(os.path.join(appdir,'listAll.xlsx'))
worksheet = workbook.add_worksheet()

# write to excel
row = 0
col = 0
format = workbook.add_format()
format.set_bold()
format.set_bg_color('yellow')

worksheet.write(row,col+1,"----APPLICATIONS----",format)
worksheet.write(row,col,"Relevant",format)
row += 1
for key,val in apps.iteritems():
    worksheet.write(row,col+1,key)
    row += 1

worksheet.write(row,col+1,"----DOCUMENTS----",format)
worksheet.write(row,col,"Relevant",format)
row += 1
for key,val in docs.iteritems():
    worksheet.write(row,col+1,key.split('[')[0])
    worksheet.insert_image(row,col+2,val[1], {'x_scale': 0.30, 'y_scale': 0.30})
    worksheet.write(row,col+3,val[0])
    row += 30

worksheet.write(row,col+1,"----PERSONS----",format)
worksheet.write(row,col,"Relevant",format)
row += 1
for key,val in persons.iteritems():
    worksheet.write(row,col+1,key)
    row += 1

worksheet.write(row,col+1,"----KEYWORDS----",format)
worksheet.write(row,col,"Relevant",format)
row += 1
for key,val in keywords.iteritems():
    worksheet.write(row,col+1,key)
    row += 1

workbook.close()

