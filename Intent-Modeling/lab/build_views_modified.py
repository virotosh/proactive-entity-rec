# Source: bow_model.py
import logging
import os
import nltk
import gensim
from gensim import corpora
import sys
import math
import operator
import json
import itertools
import numpy
from urlparse import urlparse
from itertools import groupby
from subprocess import check_output
from numpy import exp, log, dot, zeros, outer, random, dtype, float32 as REAL,\
uint32, seterr, shape, array, uint8, vstack, fromstring, sqrt, newaxis,\
ndarray, empty, sum as np_sum, prod, ones, ascontiguousarray
import scholarly

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                    level=logging.INFO)

fnames = []
appdir = sys.argv[1]

KEYWORDS_DIR = appdir+"/keywords"
PERSONS_DIR = appdir+"/persons"
TEXTS_DIR = appdir+"/converted_withentities"
KW_DIR = appdir+"/entities"
APPTYPE_DIR = appdir+"/oslog"
# copy all files in logs folder to array 'fnames'
#TEXTS_DIR = appdir+"/translated"
#KW_DIR = appdir+"/entities"
#APPTYPE_DIR = appdir+"/oslog"
#VIEWS_IND_FILE = appdir+"/lab/views_ind"
VIEWS_IND_FILE_FEATURE = appdir+"/lab/original_corpus/views_ind_1"


# GET ALL APPS
all_app_view = []
all_person_view = []
all_keyword_view = []


stoplist = set(nltk.corpus.stopwords.words("english"))

# load corpus
corpus = corpora.MmCorpus(appdir+'/lab/original_corpus/corpus.mm')
corpus.dictionary = gensim.corpora.Dictionary.load(appdir+'/lab/original_corpus/dictionary.dict')
print('CORPUS !!!!')

#print corpus.dictionary.doc2bow(["thanh_tung"])

allpeople = {}
#with open(appdir+'/lab/peopleurl.json') as log_data:
#    allpeople = json.load(log_data).decode('utf-8')
allpeople = json.loads(open(appdir+'/lab/peopleurl.json').read().decode('utf-8'))
print(allpeople)
#print 'yes', allpeople['istvan beszteri']

def writeToFile(filename, data):
    file = open(filename,"w")
    file.write(json.dumps(data).decode("utf-8"))
    file.close()

def loadPeoplePic(person):
    temp_person = person.split('_')
    print temp_person
    temp_person = list(filter(lambda x: len(x)>2, temp_person))
    if len(temp_person)==1:
        return ''
    myperson = ' '.join(temp_person)
    print person, myperson
    #print person.replace('_',' ')
    if person.replace('_',' ') in allpeople:
        return allpeople[person.replace('_',' ')]
    search_query = scholarly.search_author(myperson.replace('_',' '))
    try:
        author = next(search_query)
        print author.url_picture
        allpeople[person.replace('_',' ')] = author.url_picture
        return author.url_picture
    except:
        allpeople[person.replace('_',' ')] = ''
        return ''
    return ''


for fn in os.listdir(TEXTS_DIR):
    if(fn!=".DS_Store"):
        fnames.append(fn)
	fin = open(os.path.join(TEXTS_DIR, fn), 'rb')
        text = fin.read().decode('utf-8').strip().lower()
        app_str = ""
        if os.path.exists(APPTYPE_DIR+'/'+fn):
            #print APPTYPE_DIR+'/'+fn
       	    data = json.loads(open(APPTYPE_DIR+'/'+fn).read().decode('utf-8'))
            app_str = data["appname"].replace(' ','_').lower()
            text = text.replace(data["appname"], app_str)
            if ("safari" in app_str) or ("chrome" in app_str) or ("firefox" in app_str) or ("opera" in app_str):
           	app_str = urlparse(data["url"]).netloc.replace(".","_")
	if app_str!="" and app_str not in all_app_view:
	    all_app_view.append(app_str)

        if os.path.exists(PERSONS_DIR+"/"+fn):
            persons = json.loads(open(PERSONS_DIR+"/"+fn).read().decode('utf-8'))
	    for person in persons:
		if person not in all_person_view:
            	    all_person_view.append(person)
                    print loadPeoplePic(person)
        if os.path.exists(KEYWORDS_DIR+"/"+fn):
            keywords = json.loads(open(KEYWORDS_DIR+"/"+fn).read().decode('utf-8'))
            for keyword in keywords:
                if keyword not in all_keyword_view:
                    all_keyword_view.append(keyword)

fnames.sort()



#print corpus.dictionary.doc2bow(all_app_view)
print 'app amount'
print len(all_app_view)
print 'person amount'
print len(all_person_view)
print 'keyword amount'
print len(all_keyword_view)
# FOR PEDRAM
f_index = 0
views_ind = []

####
dictionary_view = {}

for keyword_id in corpus.dictionary.doc2bow(all_keyword_view):
    dictionary_view[keyword_id[0]] = 1
for person_id in corpus.dictionary.doc2bow(all_person_view):
    dictionary_view[person_id[0]] = 3
for app_id in corpus.dictionary.doc2bow(all_app_view):
    dictionary_view[app_id[0]] = 2

print 'DICTIONARY !!!!'

# GET FEATURES
feature_names = []
views_ind_feature_names = []
view_keyword = []
view_app = []
view_person = []
for i in range(corpus.num_terms):
    #for i in range(300):
    if i in dictionary_view:
        feature_names.append(dictionary_view[i])
        if dictionary_view[i] == 3:
            view_person.append(corpus.dictionary.get(i))
        if dictionary_view[i] == 2:
            view_app.append(corpus.dictionary.get(i))
        if dictionary_view[i] == 1:
            view_keyword.append(corpus.dictionary.get(i))
    else:
        feature_names.append(0)

print 'FEATURES !!!!'
#print feature_names

#print "---------------------------"

print all_app_view
#print (view_keyword)
#print len(view_person)
#print (view_app)

#print "---------------------------"
#print len(dictionary_view)
#print len(corpus.dictionary.keys())
#print dictionary_view
#print(corpus.dictionary.token2id)
#print views_ind

#numpy.save(VIEWS_IND_FILE,views_ind)
numpy.save(VIEWS_IND_FILE_FEATURE,feature_names)
writeToFile(appdir+'/lab/peopleurl.json',allpeople)



