# Pedram Daee <<pedram.daee@hiit.fi>>.
# A user model for interactive intent modeling based on feedback on documents and features (here called items)
# The regression model is built in the latent space but the recommendations are in the original space
# Some parts of the implementations are from
# [1] Daee, et. al. (2016). Interactive intent modeling from multiple feedback domains.
#       In Proceedings of IUI '16. ACM, Sonoma, California, USA, 71-75.


import numpy as np
from Utils import inv_woodbury


class UserModelCoupled:
    def __init__(self, params):
        """For initialization"""
        # Parameters
        self.params = params  # user model parameters
        # variance parameters of the Bayesian model
        self.sigma2_doc_imp = 0.05  # feedback noise on documents when the feedback is implicit (new snapshots)
        self.sigma2_doc_exp = 0.01  # feedback noise on documents when the feedback is explicit (clicks on docs)
        self.sigma2_term = 0.01  # feedback noise on terms, which is always explicit
        self.tau2 = 0.1  # prior variance
        # Feedback values and feature vectors in the projected space:
        self.XT = None  # design matrix of item (terms) vectors
        self.XD_exp = None  # design matrix of document vectors (for explicit clicks)
        self.XD_imp = None  # design matrix of document vectors (for implicit snapshots)
        self.YT = None  # feedback vector for items (terms)
        self.YD_exp = None  # feedback vector for documents (for explicit clicks)
        self.YD_imp = None  # feedback vector for documents (for implicit snapshots)
        # Posterior parameters (the posterior is a Multivariate normal distribution)
        self.Mu = None  # posterior mean
        self.Cov = None  # posterior covariance


    def create_design_matrices(self, projector, idx_selected_terms, y_selected_terms,
                               idx_selected_docs, y_selected_docs, fv_docs, y_fv_docs):
        # create the necessary design matrices for documents (XD_imp, XD_exp) and terms (XT).
        # Organize the feedback (YD_exp, YD_imp and YT) assumed that user feedback on documents
        # can be on old documents, or a new one (given the feature vector)
        num_term_fb = len(y_selected_terms)
        num_features = projector.num_features

        # manage design matrix and response vector for terms
        self.XT = np.empty([num_term_fb, num_features])
        for i in range(num_term_fb):
            self.XT[i, :] = projector.item_fv(idx_selected_terms[i])
        self.YT = y_selected_terms

        # manage design matrix and response vector for explicit documents
        num_doc_fb_exp = len(y_selected_docs)
        self.XD_exp = np.empty([num_doc_fb_exp, num_features])
        self.YD_exp = np.empty(num_doc_fb_exp)
        for i in range(num_doc_fb_exp):
            self.XD_exp[i, :] = projector.doc_fv(idx_selected_docs[i])
            self.YD_exp[i] = y_selected_docs[i]

        # manage design matrix and response vector for implicit documents
        num_doc_fb_imp = len(y_fv_docs)
        self.XD_imp = np.empty([num_doc_fb_imp, num_features])
        self.YD_imp = np.empty(num_doc_fb_imp)
        for i in range(num_doc_fb_imp):
            fv_docs_new = projector.doc_fv_new(fv_docs[i])
            self.XD_imp[i, :] = fv_docs_new
            self.YD_imp[i] = y_fv_docs[i]

        # the outputs of this function are XT, YT, XD_imp, YD_imp, XD_exp, YD_exp


    def learn(self):
        # This function updates the posterior based on the feature vectors of the selected items and their feedback
        # calculates the parameters of the posterior based on Equation (3) in [1].
        num_features = self.XT.shape[1]
        num_fb_terms = self.XT.shape[0]
        num_fb_docs_exp = self.XD_exp.shape[0]
        num_fb_docs_imp = self.XD_imp.shape[0]

        # The followings are the implementation of Eq (3) in the paper
        # For Cov matrix I used these in the original implementation. But the time complexity here is O(D^3)
        # However, if we use woodbury equation (the code in the next section) then it reduces to O(n^3+d^2??)

        inv_cov = 1 / (self.tau2) * np.identity(num_features)
        if num_fb_terms > 0:  # if we have feedback for terms
            inv_cov = inv_cov + 1 / (self.sigma2_term) * np.dot(self.XT.T, self.XT)
        if num_fb_docs_exp > 0:  # if we have explicit feedback for documents
            inv_cov = inv_cov + 1 / (self.sigma2_doc_exp) * np.dot(self.XD_exp.T, self.XD_exp)
        if num_fb_docs_imp > 0:  # if we have implicit feedback for documents
            inv_cov = inv_cov + 1 / (self.sigma2_doc_imp) * np.dot(self.XD_imp.T, self.XD_imp)
        self.Cov = np.linalg.inv(inv_cov)

        temp = np.zeros(num_features)
        if num_fb_terms > 0:  # if we have feedback for terms
            temp = temp + 1 / (self.sigma2_term) * np.dot(self.XT.T, self.YT)
        if num_fb_docs_exp > 0:  # if we have explicit feedback for documents
            temp = temp + 1 / (self.sigma2_doc_exp) * np.dot(self.XD_exp.T, self.YD_exp)
        if num_fb_docs_imp > 0:  # if we have implicit feedback for documents
            temp = temp + 1 / (self.sigma2_doc_imp) * np.dot(self.XD_imp.T, self.YD_imp)
        self.Mu = np.dot(self.Cov, temp)

        # the outputs of this function are Mu and Cov, which define the posterior


    def thompson_sampling(self):
        # posterior is defined by Mu and Cov
        # draw a sample from the posterior
        theta = np.random.multivariate_normal(self.Mu, self.Cov)
        return theta


    def UCB(self, feature_matrix):
        # this calculates the marginal distribution of mean relevance of each item/document based on the posterior
        # TODO: exploration rate should be controlled
        exploration_rate = 0.1
        mean_values = np.dot(feature_matrix, self.Mu)

        num_data = feature_matrix.shape[0]
        var_values = np.empty(num_data)
        for i in range(num_data):
            data_vect = feature_matrix[i][:]
            temp = np.dot(data_vect,self.Cov)
            var_values[i]  = np.dot(temp,data_vect.transpose())
        UCBs = mean_values + exploration_rate * var_values
        return UCBs
