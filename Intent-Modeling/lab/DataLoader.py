# Pedram Daee <<pedram.daee@hiit.fi>>.
# A DataLoader is an object that loads the log data from the first phase of the user study
# A data matrix is a matrix with n rows (num_data) and d columns (num_features)
# the features are themselves grouped in different views (num_views)

import numpy as np
from matplotlib import pyplot
from gensim import corpora, models, similarities
import json

class DataLoader:

    def __init__(self, data_dir):
        """For initialization"""
        #Parameters

        #self.W2V = models.Word2Vec.load(data_dir+'/word2vec')
        self.corpus = corpora.MmCorpus(data_dir+'/corpus.mm')
        self.dictionary = corpora.Dictionary.load(data_dir+'/dictionary.dict')
        #self.index = similarities.MatrixSimilarity.load(data_dir+'/corpus.mm.index')
        #views_ind is a num_featurs*1 int array, e.g. [1,1,2,3] for 3 views and 4 features
        self.views_ind = np.load(data_dir+'/views_ind_1.npy')
        #views_ind = np.zeros(self.num_features)

        self.num_features = self.corpus.num_terms          #total number of features
        self.num_data = self.corpus.num_docs               #total number of data (snapshots)
        self.num_views = max(self.views_ind) + 1           #total number of views views= [0=BOW, 1=KW, 2=App, 3=People]
        self.Data = None                                   #todo: (it may be impossible to create this) a num_data*num_featurs array
        #name of the features
        self.feature_names = [self.dictionary.get(i) for i in range(self.num_features) ]
        self.num_items_per_view = [sum(self.views_ind == i) for i in range(self.num_views)]

    def print_info(self):
        print 'The corpus has %d items' %self.num_data+' and %d features'%self.num_features+\
              ' and %d views' %self.num_views +' there are %d' %self.corpus.num_nnz +' non-zero elements'
        print 'People view %d' % self.num_items_per_view[3]+ ' items, Application view %d' %self.num_items_per_view[2]+\
              ' items, KW view %d' %self.num_items_per_view[1]+' items, BOW view %d' %self.num_items_per_view[0]+' items.'

    def process_item_info(self):
        #This function is used for offline feedback gathering
        print 'The corpus has %d items' %self.num_data+' and %d features'%self.num_features+\
              ' and %d views' %self.num_views +' there are %d' %self.corpus.num_nnz +' non-zero elements'
        print 'People view %d' %sum(self.views_ind == 3)+ ' items, Application view %d' %sum(self.views_ind == 2)+\
              ' items, KW view %d' %sum(self.views_ind == 1)+' items, BOW view %d' %sum(self.views_ind == 0)+' items.'

        #get the document frequency of the terms (i.e. how many document did a particular term occur in):
        term_frequency_dic = self.dictionary.dfs
        sorted_term_ferequency = sorted(term_frequency_dic.iteritems(), key=lambda (k,v): (v,k), reverse=True)
        sorted_IDs = [sorted_term_ferequency[i][0] for i in range(self.num_features)]

        count_term = [y for (x,y) in sorted_term_ferequency]
        pyplot.hist(count_term[9000:self.num_features-1], 20, facecolor='green')
        pyplot.xlabel('number of occurrences in the corpus')
        pyplot.ylabel('count')
        pyplot.show()
        num_of_1_occurance = len([y for (x,y) in sorted_term_ferequency if y==1])
        print '%d terms' %num_of_1_occurance+' have only appeared once in the corpus'
        term_names_1_occurance = [(self.feature_names[x]) for (x,y) in sorted_term_ferequency if y==1 ]
        with open('term_names_1_occurance.txt', 'w') as outfile:
            json.dump(term_names_1_occurance, outfile)
        #those terms can be removed from the dictionary.todo: HOWEVER, they should be removed when the corpus is being made
        #print self.dictionary
        #self.dictionary.filter_extremes(no_below=2)
        #print self.dictionary

        AP_names = [(self.feature_names[sorted_IDs[i]]) for i in range(self.num_features) \
                    if  self.views_ind[sorted_IDs[i]] == 2]
        AP_ids = [(sorted_IDs[i]) for i in range(self.num_features) \
                    if  self.views_ind[sorted_IDs[i]] == 2]

        KW_names = [(self.feature_names[sorted_IDs[i]]) for i in range(self.num_features) \
                    if  self.views_ind[sorted_IDs[i]] == 1]
        KW_ids = [(sorted_IDs[i]) for i in range(self.num_features) \
                    if  self.views_ind[sorted_IDs[i]] == 1]

        People_names = [(self.feature_names[sorted_IDs[i]]) for i in range(self.num_features) \
                    if  self.views_ind[sorted_IDs[i]] == 3]
        People_ids = [(sorted_IDs[i]) for i in range(self.num_features) \
                    if  self.views_ind[sorted_IDs[i]] == 3]

        num_to_show = 1000 #
        data = {}
        data["AP_names"] = AP_names[:num_to_show]
        data["KW_names"] = KW_names[:num_to_show]
        data["People_names"] = People_names[:num_to_show]
        data["AP_ids"] = AP_ids[:num_to_show]
        data["KW_ids"] = KW_ids[:num_to_show]
        data["People_ids"] = People_ids[:num_to_show]


        with open('for_vuong.txt', 'w') as outfile:
            json.dump(data, outfile)
