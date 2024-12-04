# Pedram Daee <<pedram.daee@hiit.fi>>.
# A DataProjector is an object that projects data object to a latent space
# At the moment we will use LSI types of methdos to do this
import numpy
from gensim import corpora, models, similarities,matutils
import numpy as np
import os.path
import time
import scipy.sparse

class DataProjector:

    def __init__(self, data_orig, params):
        """For initialization"""
        self.params = params
        self.num_terms = data_orig.corpus.num_terms      #total number of features (items of views, aka terms)
        self.num_docs = data_orig.corpus.num_docs        #total number of data (snapshots)
        self.num_features = params["num_latent_dims"]    #number of latent dimensions

        self.data_orig = data_orig                   # keep the original data
        self.corpus_normalized = None                # contains the corpus in the tfidf format or in the nomalized format
        self.tfidf = None                            # the tf-idf model of the input corpus
        self.corpus_lsi = None                       # contains the corpus in the LSI space
        self.lsi = None                              # the lsi transformation of corpus_normalized
        self.svd_v = None                            # the V matrix in lsi[X] = U^-1*X = V*S

    def generate_latent_space(self):
        #for now just use Gensim's LSA for latent space
        if os.path.isfile('./temp/corp1.lsi') and os.path.isfile('./temp/corp1.tfidf') and os.path.isfile('./temp/corpus_normalized.mm') \
                and os.path.isfile('./temp/corp1.svd_v.npy'):
            print 'Loading LSI model from folder /temp...'
            #The mapping between the questions (how many times does a word appear..) and ids is called a dictionary
            #self.dictionary = corpora.Dictionary.load('./temp/corp1.dict')
            self.lsi = models.LsiModel.load('./temp/corp1.lsi')
            self.tfidf = models.TfidfModel.load('./temp/corp1.tfidf')
            self.svd_v = np.load('./temp/corp1.svd_v.npy')
            self.corpus_normalized = corpora.MmCorpus('./temp/corpus_normalized.mm')

        else:
            #use libraries from gensim to build LSI model
            print 'Create latent space and save it in /temp...'
            t1 = time.time()
            #todo: maybe I don't need to do tfidf, but if I do I should also do it for the query
            self.tfidf = models.TfidfModel(self.data_orig.corpus)
            self.tfidf.save('./temp/corp1.tfidf')
            corpus_tfidf = self.tfidf[self.data_orig.corpus]
            self.corpus_normalized = corpus_tfidf # tfidf is a basic normalization

            corpora.MmCorpus.serialize('./temp/corpus_normalized.mm', self.corpus_normalized)  #save the normalized corpus
            # initialize an LSI transformation
            self.lsi = models.LsiModel(self.corpus_normalized, id2word=self.data_orig.dictionary, num_topics=self.num_features)
            self.lsi.save('./temp/corp1.lsi')
            # Given a model lsi = LsiModel(X, ...), with the truncated singular value decomposition of your corpus X being X=U*S*V^T,
            # doing lsi[X] computes U^-1*X, which equals V*S (basic linear algebra). So if you want V, divide lsi[X] by S:
            self.svd_v = matutils.corpus2dense(self.lsi[self.corpus_normalized], num_terms=len(self.lsi.projection.s)).T / self.lsi.projection.s #TODO: is \ element wise?!
            np.save('./temp/corp1.svd_v.npy', self.svd_v)
            #print(lsi.print_topics(self.num_latent_dims))
            t2 = time.time()
            t_latent = t2-t1
            print 'Latent space creation took %f second' %t_latent
        # create a double wrapper over the original corpus: bow->tfidf->fold-in-lsi
        self.corpus_lsi = self.lsi[self.corpus_normalized]


    def create_feature_matrices(self):
        #This function creates the neccessary featuer matrices introduced in [1]
        #the new idea is that the keyword space is projected to a latent space first and
        # based on the document transformation idea, the documents are also projected
        if os.path.isfile('./temp/term_f_mat.npy') and os.path.isfile('./temp/doc_f_mat.npy'):
            self.term_f_mat = np.load('./temp/term_f_mat.npy')
            self.doc_f_mat = np.load('./temp/doc_f_mat.npy')
        else:
            t1 = time.time()
            w = self.svd_v
            w = w/self.lsi.projection.s  # this is necessary based on the LSI in wiki

            # Use sparse matrix rather than dense matrices to do the calculations (save memory)
            M_T_sparse = matutils.corpus2csc(self.corpus_normalized, num_terms=self.data_orig.num_features, num_docs=self.data_orig.num_data, num_nnz=self.data_orig.corpus.num_nnz)
            self.term_f_mat = M_T_sparse.dot(w)
            np.save('./temp/term_f_mat.npy', self.term_f_mat)
            t2 = time.time()

            # Based on the assumptions in [1], I need to normalize to have P(t_i|d_j) in the original space
            # Normalize the document vectors to sum up to one
            if self.params["normalize_terms"]:
                sum_over_terms = M_T_sparse.sum(axis=0).A.ravel()  # take the sum over terms for each doc
                sum_over_terms_diag = scipy.sparse.diags(1/sum_over_terms, 0)  # create an inverted diag matrix of sums
                M_T_sparse_normalized = M_T_sparse.dot(sum_over_terms_diag)  # divide by sums by using doc product
                M_T_sparse_normalized_T = M_T_sparse_normalized.transpose()
            else:
                M_T_sparse_normalized_T = M_T_sparse.transpose()

            # Use sparse matrix rather than dence matrices to do the calculations (save memory)
            self.doc_f_mat = M_T_sparse_normalized_T.dot(self.term_f_mat)
            np.save('./temp/doc_f_mat.npy', self.doc_f_mat)
            t3 = time.time()
            t_term_mat = t2-t1
            t_doc_mat = t3-t2
            t_total = t3-t1
            print 'Creating term matrix %f second' %t_term_mat
            print 'Creating document matrix %f second' %t_doc_mat
            print 'Total %f second' %t_total


    def item_fv(self,index_item):
        return self.term_f_mat[index_item][:]


    def doc_fv(self,index_doc):
        #there would be new docs generated in every iteration. Should I update the latent space? "no" at the moment
        return self.doc_f_mat[index_doc][:]


    def doc_fv_new(self, new_doc_fv):
        #feedbacks are on new docs (not in corpus)
        #It is only enough to transform the new doc fv to the latent space which can be done as: fv * self.term_f_mat
        #input: new_doc_fv should be a bag-of-word representation of a document (sparse matrix)
        # the logger needs to check if the term names are the same to the current dictionary
        # use tfidf
        new_doc_fv_tfidf = self.tfidf[new_doc_fv]
        # make it an array
        new_doc_fv_normalized = np.zeros(self.num_terms)
        sum_over_terms = 0
        for i in range(len(new_doc_fv_tfidf)):
            new_doc_fv_normalized[int(new_doc_fv_tfidf[i][0])] = new_doc_fv_tfidf[i][1]
            sum_over_terms = sum_over_terms + new_doc_fv_tfidf[i][1]

        if self.params["normalize_terms"]:
            new_doc_fv_normalized = new_doc_fv_normalized / sum_over_terms

        new_fv = np.dot(new_doc_fv_normalized, self.term_f_mat)
        return new_fv

