# Source: bow_model.py
import logging
import os
import nltk
import gensim
from gensim import corpora
from pprint import pprint  # pretty-printer
import sys
import math
import operator
import json
import itertools
import numpy
from collections import defaultdict
from urlparse import urlparse
from itertools import groupby
from subprocess import check_output
from numpy import exp, log, dot, zeros, outer, random, dtype, float32 as REAL,\
uint32, seterr, shape, array, uint8, vstack, fromstring, sqrt, newaxis,\
ndarray, empty, sum as np_sum, prod, ones, ascontiguousarray

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                    level=logging.INFO)

fnames = []
appdir = sys.argv[1]
amount_docs_already_index = 0
corpus_already_index = None
stoplist = set(nltk.corpus.stopwords.words("english"))
KEYWORDS_DIR = appdir+"/keywords"
PERSONS_DIR = appdir+"/persons"
TEXTS_DIR = appdir+"/converted_withentities"
KW_DIR = appdir+"/entities"
APPTYPE_DIR = appdir+"/oslog"


def iter_docs(topdir, stoplist, amount_docs_already_index):
    idx = 0;
    directory = []
    for fn in os.listdir(topdir):
        directory.append(fn)
    directory.sort()
    for fn in directory:
        if(fn!=".DS_Store"):
            if (idx >= amount_docs_already_index):
                fin = open(os.path.join(topdir, fn), 'rb')
                text = fin.read().decode('utf-8').strip().lower()
                app_str = ""
		texts = [x for x in 
                        gensim.utils.tokenize(text, lowercase=True, deacc=True,
                                             errors="ignore")
                       if x not in stoplist and len(x)>2]
		if os.path.exists(APPTYPE_DIR+'/'+fn):
		    data = json.loads(open(APPTYPE_DIR+'/'+fn).read().decode('utf-8'))
		    app_str = data["appname"].replace(' ','_').lower()
		    text = text.replace(data["appname"], app_str)
                    if ("safari" in app_str) or ("chrome" in app_str) or ("firefox" in app_str) or ("opera" in app_str):
                    	app_str = urlparse(data["url"]).netloc.replace(".","_")
		if app_str!="":
		    texts.append(app_str)
                person_string = ""
                keyword_string = ""
                if os.path.exists(PERSONS_DIR+"/"+fn):
		   persons = json.loads(open(PERSONS_DIR+"/"+fn).read().decode('utf-8'))
		   for person in persons:
			texts.append(person)
		if os.path.exists(KEYWORDS_DIR+"/"+fn):
                   keywords = json.loads(open(KEYWORDS_DIR+"/"+fn).read().decode('utf-8'))
		   for keyword in keywords:
			texts.append(keyword)
#                print("----APPS---")
#		print(app_str)
#		print("----PERSONS---")
#                print(person_string)
#                print("----KEYWORDS---")
#                print(keyword_string)
                fin.close()
		#pprint(texts)
                yield (x for x in texts)
            idx+=1

class MyCorpus(object):
    
    def __init__(self, topdir, stoplist, amount_docs_already_index):
        self.topdir = topdir
        self.stoplist = stoplist
        self.amount_docs_already_index = amount_docs_already_index
        self.texts = iter_docs(topdir, stoplist, amount_docs_already_index)
        texts_for_frequency = iter_docs(topdir, stoplist, amount_docs_already_index)
        #pprint(texts)
        frequency = defaultdict(int)
        for text in texts_for_frequency:
            for token in text:
                frequency[token] += 1
        self.texts = [[token for token in text if frequency[token] > 1]
                      for text in self.texts]
        self.dictionary = gensim.corpora.Dictionary(self.texts)
        self.size = len(os.listdir(topdir))
    
    def __iter__(self):
        for text in self.texts:
            yield self.dictionary.doc2bow(text)

# copy all files in logs folder to array 'fnames'
for fname in os.listdir(TEXTS_DIR):
    if(fname!=".DS_Store"):
        fnames.append(fname)
fnames.sort()

#check if model was saved and load lsi model
if (os.path.isfile(appdir+'/corpus/corpus.mm')):
    corpus_already_index = corpora.MmCorpus(appdir+'/corpus/corpus.mm')
    corpus_already_index.dictionary = gensim.corpora.Dictionary.load(appdir+'/corpus/dictionary.dict', mmap=None)
    amount_docs_already_index = len(corpus_already_index)
corpus = None
dict2_to_dict1 = None
merged_corpus = None
model = None

# if saved model exist
if corpus_already_index != None:
    if (len(fnames)>amount_docs_already_index):
        corpus = MyCorpus(TEXTS_DIR, stoplist, amount_docs_already_index)
        dict2_to_dict1 = corpus_already_index.dictionary.merge_with(corpus.dictionary)
        merged_corpus = itertools.chain(corpus_already_index,dict2_to_dict1[corpus])
        corpora.MmCorpus.serialize(appdir+"/corpus/merged_corpus.mm",merged_corpus)
        corpus=corpora.MmCorpus(appdir+'/corpus/merged_corpus.mm')
        corpus.dictionary = corpus_already_index.dictionary
        corpora.MmCorpus.serialize(appdir+'/corpus/corpus.mm', corpus)
        corpus.dictionary.save(appdir+'/corpus/dictionary.dict')
    else:
        corpus = corpus_already_index
else:
    corpus = MyCorpus(TEXTS_DIR, stoplist, amount_docs_already_index)
    #print(corpus.dictionary.get(0))
    corpora.MmCorpus.serialize(appdir+'/corpus/corpus.mm', corpus)
    corpus.dictionary.save(appdir+'/corpus/dictionary.dict')
