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
import urllib
#from urlparse import urlparse
from itertools import groupby
from subprocess import check_output
from numpy import exp, log, dot, zeros, outer, random, dtype, float32 as REAL,\
uint32, seterr, shape, array, uint8, vstack, fromstring, sqrt, newaxis,\
ndarray, empty, sum as np_sum, prod, ones, ascontiguousarray
from pprint import pprint

#logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
#                    level=logging.INFO)

fnames = []
mainappdir = sys.argv[1].replace('/lab','')
appdir = sys.argv[1]
amount_docs_already_index = 0
corpus_already_index = None
KEYWORDS_DIR = appdir+"/keywords"
PERSONS_DIR = appdir+"/persons"
TEXTS_DIR = appdir+"/converted_withentities"
KW_DIR = appdir+"/entities"
APPTYPE_DIR = appdir+"/oslog"

def writeToFile(filename, data):
    file = open(filename,"w")
    file.write(json.dumps(data).decode("utf-8"))
    file.close()

def countOccurence(snapshot, entity):
    result = 0
    entity_terms = list(gensim.utils.tokenize(entity, lowercase=True, deacc=True,
                                         errors="ignore"))
    if len(entity_terms) == 0:
        return 0
    if len(entity_terms) == 1:
        if len(entity_terms[0])<3:
            return 0
        else:
            return 1
    for term in entity_terms:
        if term in stoplist and len(term)>2:
            continue
        result= result + list(gensim.utils.tokenize(snapshot, lowercase=True, deacc=True,
                                                    errors="ignore")).count(term)
    #AVERAGE
    return int(math.ceil(result/len(entity_terms)))


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
                    data = json.loads(open(APPTYPE_DIR+'/'+fn).read())
                    app_str = data["appname"].replace(' ','_').lower()
                    text = text.replace(data["appname"], app_str)
                    if ("safari" in app_str) or ("chrome" in app_str) or ("firefox" in app_str) or ("opera" in app_str):
                        app_str = urllib.parse.urlparse(data["url"]).netloc.replace(".","_")
                if app_str!="":
                    texts.append(app_str)
                person_string = ""
                keyword_string = ""
                if os.path.exists(PERSONS_DIR+"/"+fn):
                    persons = json.loads(open(PERSONS_DIR+"/"+fn).read())
                    for person in persons:
                        texts.append(person)
                if os.path.exists(KEYWORDS_DIR+"/"+fn):
                    keywords = json.loads(open(KEYWORDS_DIR+"/"+fn).read())
                    for keyword in keywords:
                        texts.append(keyword)
                #pprint(text)
                fin.close()
                yield (x for x in texts)
            idx+=1



class MyCorpus(object):
    def __init__(self, topdir, stoplist, amount_docs_already_index):
        self.topdir = topdir
        self.stoplist = stoplist
        self.amount_docs_already_index = amount_docs_already_index
        self.dictionary = gensim.corpora.Dictionary(iter_docs(topdir, stoplist, amount_docs_already_index))
        self.size = len(os.listdir(topdir))
    
    def __iter__(self):
        for tokens in iter_docs(self.topdir, self.stoplist, self.amount_docs_already_index):
            yield self.dictionary.doc2bow(tokens)

# update word2vec model & dictionary
def update(model, data, sentences, mincount=1):
    added_count = 0
    logging.info("Extracting vocabulary from new data...")
    newmodel = gensim.models.Word2Vec(min_count=mincount, sample=0, hs=0)
    newmodel.build_vocab(data)
    logging.info("Merging vocabulary from new data...")
    sampleint = model.vocab[model.index2word[0]].sample_int
    words = 0
    newvectors = []
    newwords = []
    for word in newmodel.vocab:
        words += 1
        if word not in model.vocab:
            v = gensim.models.word2vec.Vocab()
            v.index = len(model.vocab)
            model.vocab[word] = v
            model.vocab[word].count = newmodel.vocab[word].count
            model.vocab[word].sample_int = sampleint
            model.index2word.append(word)
            
            random_vector = model.seeded_vector(model.index2word[v.index] + str(model.seed))
            newvectors.append(random_vector)
            
            added_count += 1
            newwords.append(word)
        else:
            model.vocab[word].count += newmodel.vocab[word].count
        if words % 1000 == 0:
            logging.info("Words processed: %s" % words)
    logging.info("added %d words into model from new data" % (added_count))
    logging.info("Adding new vectors...")
    alist = [row for row in model.syn0]
    for el in newvectors:
        alist.append(el)
    model.syn0 = array(alist)
    logging.info("Generating negative sampling matrix...")
    model.syn1neg = zeros((len(model.vocab), model.layer1_size), dtype=REAL)
    model.make_cum_table()
    
    model.neg_labels = zeros(model.negative + 1)
    model.neg_labels[0] = 1.
    
    model.syn0_lockf = ones(len(model.vocab), dtype=REAL)
    
    logging.info("Training with new data...")
    model.train(data, total_examples=sentences)
    
    return model


def main():
    #print(sys.argv[0])
    # copy all files in logs folder to array 'fnames'
    VIEWS_IND_FILE = appdir+"/views_ind"
    VIEWS_IND_FILE_FEATURE = appdir+"/views_ind_feature"
    for fname in os.listdir(TEXTS_DIR):
        if(".txt" in fname):
            #print(fname)
            fnames.append(fname)
    fnames.sort()
    stoplist = set(nltk.corpus.stopwords.words("english"))

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

    # FOR PEDRAM
    f_index = 0
    views_ind = []

    ####
    dictionary_view = {}
    all_app_view = {}

    #print 'corpus DONE!!!'
    #print ''

    current_dict = gensim.corpora.Dictionary.load(appdir+'/original_corpus/dictionary.dict', mmap=None)

    new_doc_list = []
    order_key = 0;
    for vector in corpus:
        if order_key>=len(fnames):
            break
        NEW_ACTIVITY_IND_FILE = appdir+"/user activity/"+fnames[order_key]+".npy"
        vector_value_list = []
        for key,value in vector:
            count_v = 0
            while count_v < value:
                vector_value_list.append(corpus.dictionary.get(key))
                count_v=count_v+1
        #print(vector_value_list)
        #print(current_dict.doc2bow(vector_value_list))
        numpy.save(NEW_ACTIVITY_IND_FILE,current_dict.doc2bow(vector_value_list))
        order_key=order_key+1
        #print "----------"
    #print 'feature view DONE!!!'
    #print '----END---'
    #writeToFile('peopleurl.json',allpeople)
    #print feature_names

    #print "---------------------------"

    #print all_app_view
    #print len(view_keyword)
    #print (view_person)
    #print (view_app)

    #print "---------------------------"
    #print len(dictionary_view)
    #print len(corpus.dictionary.keys())
    #print dictionary_view
    #print(corpus.dictionary.token2id)
    #print views_ind

    #numpy.save(VIEWS_IND_FILE,views_ind)
    #numpy.save(VIEWS_IND_FILE_FEATURE,feature_names)
if __name__ == '__main__':
    main()
