#This script is the starting point for the backend of the proactive search system
#The code works for synthetic and real data
# main.py controls the following process:
#    1. Load the experiment logs
#    2. Create (or load) the low dimensional representation of data
#    3. Interaction loop:
#        3.1. Receive new snapshots (real-time documents)
#        3.2. Update the user model
#        3.3. Recommend items from different views
#        3.4. gather feedback for items

from DataLoader import DataLoader
from DataProjector import DataProjector
from UserModelCoupled import UserModelCoupled
import numpy as np
import re
import os
import json

# TODO LIST:
#           - have several Thompson sampling iteration to increase exploration
#           - note that each Thompson sample retrieves items that probably similar
#           - Data cleaning. Remove documents with no term in them (divide by zeros)
#           - remove garbage words
#           - new snapshot should have the terms that are already in the dictionary
#           - to validate the system, remove Thompson and don't show recommended_items again :)
#           - Parameters of the coupled model + number of latent dimensions should be tuned in practice
#           - Correlation between terms can be inferred from the retrieved documents
#           - Do we need GFA? (discuss with Sami)
#           - validate the retrieved snapshots. Are they sensible?

#---------------Initialization of parameters and methods
params = {

    # Number of recommended entities from each view
    "suggestion_count": 10,
    # Number of online snapshots to consider (the latest snapshots)
    "imp_doc_to_consider": 4,
    # True: normalize TF-IDF weights to sum to 1, False: no normalization. TODO: DOES THIS MAKE SENSE?
    "normalize_terms": True,
    # True: use exploration algorithm (Thompson Sampling) for recommendation, False: use the mean of the estimate.
    "Thompson_exploration": False,
    # True: allow the algorithm to show previously recommended items, False: each item can be recommended only once
    "repeated_recommendation": True,
    # A heuristic method to shrink the variance of the posterior (reduce the exploration). it should be in (0,1];
    "exploration_rate": 1,  # NOT IMPLEMENTED YET
    # Number of iterations of the simulated study
    "num_iterations": 50,
    # Number of latent dimensions for data representation
    "num_latent_dims": 100,
    # Number of runs (only for the simulated study, set to 1 for real data setting)
    "num_runs": 1,  # NOT IMPLEMENTED YET
    # True: prepare the data for FOCUS UI but have the interaction in the terminal
    "FOCUS_UI_simulator": True,
    # The directory of the corpus (It should have /corpus.mm, /dictionary.dict, and views_ind_1.npy files)
    #"corpus_directory": 'corpus1_2/corpus7_sim',
    "corpus_directory": 'corpus1_2/P01',
    # The directory of the new snapshots that will be checked at the beginning of each iteration
    "snapshots_directory": 'user activity',
    # True: Use the simulated user data to simulate the user feedback
    "Simulated_user": False,
}

# Set the desirable method to True for the experiment
Methods = {
    "LSA-coupled-Thompson": True,
    "LSA-coupled-UCB": False,
    "Random": False
}
Method_list = []
num_methods = 0
for key in Methods:
    if Methods[key] == True:
        Method_list.append(key)
        num_methods = num_methods + 1


for runs in range(params["num_runs"]):

    #---------------------- Phase 1: Load the experiment logs ----------------------------------------#

    #load the data from the log files
    data_dir = params["corpus_directory"]
    data = DataLoader(data_dir)
    data.print_info()
    #data.process_item_info()   # Use this to list entities for off line feedback gathering
    #---------------------- Phase 2: Create (or load) the low dimensional representation of data ------#
    projector = DataProjector(data, params)
    projector.generate_latent_space()
    projector.create_feature_matrices()

    #---------------------- Phase 3: Interaction loop  ------------------------------------------------#
    for method_ind in range(num_methods):
        method = Method_list[method_ind]

        selected_terms = []        # ID of terms that the user has given feedback to
        feedback_terms = []        # feedback value on the selected terms
        recommended_terms = []     # list of ID of terms that have been recommended to the user
        selected_docs = []         # ID of snapshots that the user has given feedback to (may not be available in practice)
        feedback_docs = []         # feedback value on the selected snapshots (may not be available in practice)

        for iteration in range(params["num_iterations"]):

            print 'Iteration = %d' %iteration

            # 3.1 check the snapshot folder and consider positive feedback for the real-time generated snapshots
            # the snapshot format is doc = [(term_idx,freq),..]
            print 'Loading real-time generated snapshots...'
            all_online_docs = []   # all snapshots generated from realtime user activity
            fv_online_docs = []    # considered snapshots generated from realtime user activity
            fb_online_docs = []    # dummy feedback for the newly generated snapshots
            for document in os.listdir(params["snapshots_directory"]):
                if document != ".DS_Store" and document != "readme.txt":
                    # load the numpy file
                    snapshot_fv = np.load(params["snapshots_directory"]+"/"+document)
                    all_online_docs.append(snapshot_fv)
            # only consider the most recent snapshots
            all_online_docs.reverse()
            for snapshot_fv in all_online_docs:
                if len(fv_online_docs) < params["imp_doc_to_consider"]:
                    fv_online_docs.append(snapshot_fv)
                    fb_online_docs.append(1)  #dummy feedback on the newly generated documents

            # 3.2 and 3.3: Update the user model and recommend new items based on the chosen method
            if method == "LSA-coupled-Thompson":
                # initialize the user model in the projected space
                user_model = UserModelCoupled(params)
                # create the design matrices for docs and terms
                user_model.create_design_matrices(projector, selected_terms, feedback_terms,selected_docs, feedback_docs, fv_online_docs, fb_online_docs)
                #user_model.create_design_matrices(projector, selected_terms, feedback_terms, [1], [2], [[(1,2),(4,3)], [(2,2),(14,1)] ], [0.5, 0.1])
                # posterior inference
                user_model.learn()
                # Thompson sampling for coupled EVE
                #TODO: test having K thompson sampling for the K recommendations
                if params["Thompson_exploration"]:
                    theta = user_model.thompson_sampling()
                else:
                    theta = user_model.Mu # in case of no exploration, use the mean of the posterior
                scored_docs = np.dot(projector.doc_f_mat, theta)
                scored_terms = np.dot(projector.term_f_mat, theta)
                #print theta

            if method == "LSA-coupled-UCB":
                # initialize the user model in the projected space
                user_model = UserModelCoupled(params)
                # create the design matrices for docs and terms
                user_model.create_design_matrices(projector, selected_terms, feedback_terms,selected_docs, feedback_docs, fv_online_docs, fb_online_docs)
                # posterior inference
                user_model.learn()
                # Upper confidence bound method
                scored_docs = user_model.UCB(projector.doc_f_mat)
                scored_terms = user_model.UCB(projector.term_f_mat)

            if method == "Random":
                scored_docs = np.random.uniform(0,1,projector.num_docs)
                scored_terms = np.random.uniform(0,1,projector.num_terms)


            #---------------------- 3.4: gather user feedback ---------------------------#
            #sort items based on their index
            #todo: if time consuming then have k maxs instead of sort
            sorted_docs = sorted(range(len(scored_docs)), key=lambda k:scored_docs[k], reverse=True)
            # make sure the selected items are not recommended to user again
            sorted_docs_valid = [doc_idx for doc_idx in sorted_docs if doc_idx not in set(selected_docs)]

            # make sure the selected terms are not recommended to user again
            sorted_terms = sorted(range(len(scored_terms)), key=lambda k:scored_terms[k], reverse=True)

            sorted_views_list = []  # sorted ranked list of each view
            for view in range(1, data.num_views):
                # sort items of each view. Exclude (or not exclude) the previously recommended_terms.
                if params["repeated_recommendation"]:
                    sorted_view = [term_idx for term_idx in sorted_terms
                                   if term_idx not in set(selected_terms) and data.views_ind[term_idx] == view]
                else:
                    sorted_view = [term_idx for term_idx in sorted_terms
                                   if term_idx not in set(recommended_terms) and data.views_ind[term_idx] == view]

                sorted_views_list.append(sorted_view)

            # FOCUS IN TERMINAL USER INTERFACE
            if params["FOCUS_UI_simulator"]:

                for view in range(1, data.num_views):
                    print 'view %d:' %view
                    for i in range(min(params["suggestion_count"],data.num_items_per_view[view])):
                        print '    %d,' %sorted_views_list[view-1][i] + ' ' + data.feature_names[sorted_views_list[view-1][i]]
                print 'Relevant document IDs (for debugging):'
                for i in range(params["suggestion_count"]):
                    print '    %d' %sorted_docs_valid[i]

                # save the new recommendations in this iteration and all the recommendations till now
                new_recommendations = []
                for view in range(1, data.num_views):
                    for i in range(min(params["suggestion_count"],data.num_items_per_view[view])):
                        new_recommendations.append(sorted_views_list[view-1][i])
                        if sorted_views_list[view-1][i] not in set(recommended_terms):
                            recommended_terms.append(sorted_views_list[view-1][i])

                #organize the recommentations in the right format
                data_output = {}
                data_output["keywords"] = [(sorted_views_list[0][i],data.feature_names[sorted_views_list[0][i]],
                                            scored_terms[sorted_views_list[0][i]]) for i in range(min(params["suggestion_count"],data.num_items_per_view[1]))]
                data_output["applications"] = [(sorted_views_list[1][i],data.feature_names[sorted_views_list[1][i]],
                                                scored_terms[sorted_views_list[1][i]]) for i in range(min(params["suggestion_count"],data.num_items_per_view[2]))]
                data_output["people"] = [(sorted_views_list[2][i],data.feature_names[sorted_views_list[2][i]],
                                          scored_terms[sorted_views_list[2][i]]) for i in range(min(params["suggestion_count"],data.num_items_per_view[3]))]
                # TODO: how many document? I can also send the estimated relevance.
                data_output["document_ID"] = [(sorted_docs_valid[i]) for i in range(params["suggestion_count"])]

                # TODO: for now the pair similarity part is commented to reduce the load of communications
                ##Compute the similarity matrix which is needed for FOCUS UI:
                ## I can do this by prepare a similarity matrix (e.g. cos similarity) between all the recommended terms
                ## The similarities are calculated in the latent space (based on the feature vectors).
                ## I will do this for all the "new_recommendations" and send it to frontend every iteration

                ## list of items that we want to calculate their pair similarity
                #item_list = new_recommendations
                ## an array to hold the feature vectors
                #recommended_fv = np.empty([len(item_list), projector.num_features])
                #for i in range(len(item_list)):
                #    recommended_fv[i, :] = projector.item_fv(item_list[i]) #get the feature vector
                ##Compute the dot products
                #sim_matrix = np.dot(recommended_fv, recommended_fv.T)
                ##normalize the dot products
                #sim_diags = np.diagonal(sim_matrix)
                #sim_diags = np.sqrt(sim_diags)
                #for i in range(len(item_list)):
                #    sim_matrix[i,:] = sim_matrix[i,:]/sim_diags
                #for i in range(len(item_list)):
                #    sim_matrix[:,i] = sim_matrix[:,i]/sim_diags

                ##save pairwise similarities in a list of tuples
                #all_sims = [(item_list[i],item_list[j],sim_matrix[i,j])
                #            for i in range(len(item_list)-1) for j in range(i+1,len(item_list))]
                #data_output["pair_similarity"] = all_sims

                #for now write everything in a file
                with open('data.txt', 'w') as outfile:
                    json.dump(data_output, outfile)

                #Terminal feedback gathering
                input = 1
                print 'Give your feedback as "id fb_value" for terms then press Enter. Press Enter to go to the next iteration.'
                while input != 0:
                    input_string = raw_input()
                    array_input = re.findall(r'\d*\.?\d+', input_string)
                    if len(array_input) == 0:
                        input = 0
                    else:
                        # save user feedbacks to update the model in the next iteration
                        #fb_Val coding: 1: pinning, 0:unpinning, -1:removing]
                        # TODO: it seems that in Focus now we have positive feedback (1), and canceling the positive feedback (0)
                        item_id = int(array_input[0])
                        fb_Val = float(array_input[1])

                        # Based on FOCUS requirements we will remove the previous feedbacks on the same item
                        repeated_indx = [index for index, id in enumerate(selected_terms) if id == item_id]
                        if len(repeated_indx) > 0:
                            del selected_terms[repeated_indx[0]]
                            del feedback_terms[repeated_indx[0]]
                        #todo: You may want to just replace the feedback or just remove it (decide this later)
                        selected_terms.append(item_id)
                        feedback_terms.append(fb_Val)
                        # TODO: recored the interactions

            #Simluated data experiment
            if params["Simulated_user"]:
                # save the new recommendations in this iteration and all the recommendations till now
                new_recommendations = []
                for view in range(1, data.num_views):
                    for i in range(range(min(params["suggestion_count"],data.num_items_per_view[view]))):
                        item_id = sorted_views_list[view-1][i]
                        new_recommendations.append(item_id)
                        if item_id not in set(recommended_terms):
                            recommended_terms.append(item_id)

                        #todo: here ask for the feedback for each item_id and save it in the feedback_terms and selected_terms



#TODO: Save the necessary arrays for the evaluation