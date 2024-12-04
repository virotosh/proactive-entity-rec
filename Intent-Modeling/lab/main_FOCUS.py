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
from os import listdir
from os.path import isfile, join
from collections import defaultdict
from urlparse import urlparse
import numpy as np
import re
import os
import json
import redis
import time
import sys
import urllib
# import scholarly

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
    "num_iterations": 500,
    # Number of latent dimensions for data representation
    "num_latent_dims": 100,
    # True: prepare the data for FOCUS UI
    "FOCUS_UI": True,
    # The directory of the corpus (It should have /corpus.mm, /dictionary.dict, and views_ind_1.npy files)
    "corpus_directory": 'original_corpus',
    # The directory of the new snapshots that will be checked at the beginning of each iteration
    "snapshots_directory": 'user activity',
    "userlogs_directory": 'userlogs',
    "persons_directory": 'persons',
    "keywords_directory": 'keywords',
    "apps_directory": 'oslog'
}

# Set the desirable method to True for the experiment
#in the real experiment we consider one method at a time
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


#---------------------- Phase 1: Load the experiment logs ----------------------------------------#

#load the data from the log files
data_dir = params["corpus_directory"]
data = DataLoader(data_dir)
data.print_info()

#---------------------- Phase 2: Create (or load) the low dimensional representation of data ------#

projector = DataProjector(data, params)
projector.generate_latent_space()
projector.create_feature_matrices()

# if params["use_lstm"]:
#     lstm = Lstm()
#     lstm.train(projector.svd_v)
#     ...
#     t2 = lstm.predict(t1)
# else:
#     ...

#---------------------- Phase 3: Interaction loop  ------------------------------------------------#
#Some initializations
method = Method_list[0]    #in the real experiment we consider one method at a time

selected_terms = []        # ID of terms that the user has given feedback to
feedback_terms = []        # feedback value on the selected terms
recommended_terms = []     # list of ID of terms that have been recommended to the user
selected_docs = []         # ID of snapshots that the user has given feedback to (may not be available in practice)
feedback_docs = []         # feedback value on the selected snapshots (may not be available in practice)
currently_shown = []       # currently shown items in the frontend (not used at the moment, but let's keep it!)
pinned_item = []           # the items that are pinned in the frontend (needed for calculating pair similarity)

#load extra os log directory
oslog_directory = os.getcwd().replace('lab','oslog')
converted_withentities_directory = os.getcwd().replace('lab','converted_withentities')
snapshot_directory = os.getcwd().replace('lab','original').replace('/Users/kin/','/Users/kin/')
#snapshot_directory = os.getcwd().replace('lab','original')
#load all snapshots extra logs
file_names = []
allpeople = {}
with open('peopleurl.json') as log_data:
    allpeople = json.load(log_data)

for file_name in os.listdir(converted_withentities_directory):
    if(file_name!=".DS_Store"):
        file_names.append(file_name)
file_names.sort()

def loadLOG(doc_id):
    if os.path.exists(os.path.join(oslog_directory, file_names[doc_id])):
        with open(os.path.join(oslog_directory, file_names[doc_id])) as log_data:
            return json.load(log_data)
    else:
        return {"title": " ", "appname": "unknown", "url":""}

def writeToFile(filename, data):
    file = open(filename,"w")
    file.write(json.dumps(data).decode("utf-8"))
    file.close()

def loadPeoplePic(person):
    if len(person.split('_'))==1:
        return ''
    if person.replace('_',' ').encode("utf8") in allpeople:
        return allpeople[str(person.replace('_',' ')).encode("utf8")]
    return ''

### -setup the connection to the frontend - ###
# define Redis connection for input/output
redis_IO = redis.Redis()
# define subscribed channels as an array (only one element: userFeedback)
subscribed_channels = redis_IO.pubsub()
subscribed_channels.subscribe(['userFeedback'])

new_explicit_fb_flag = False # a flag to monitor new explicit feedbacks
iteration = 0
wait_to_start = 1
wait_for_user_activity = 1
while iteration < params["num_iterations"]:

    update_interval = 10
    new_explicit_fb_flag = False
    
    while new_explicit_fb_flag == False and update_interval > 0:
        #see if new explicit feedback has arrived from the frontend
        message = subscribed_channels.get_message()
        if message:
            if message['type'] == 'subscribe':
                # get next message
                message = subscribed_channels.get_message()
        #WAITING USER TO START
        while wait_to_start:
            print 'Waiting to start !!!!!!!!!!!'
            if message:
                if message['type'] == 'subscribe':
                    # get next message
                    message = subscribed_channels.get_message()
            if message:
                print(message)
                input_data = json.loads(message['data'])
                if input_data == {"Channel":"START"}:
                    wait_to_start = 0
                    # write user feedbacks to logs
                    feedback_file = open(os.path.join(params["userlogs_directory"],str(time.time())+'_userStart.txt'),"w")
                    feedback_file.write(json.dumps(input_data))
                    feedback_file.close()
                    # command = './refresh.sh'
                    # os.popen("sudo -S %s"%(command), 'w').write('thanhtung#%!@')
            message = subscribed_channels.get_message()
            time.sleep(1)
        #WAITING FOR USER TO GIVE SOME ACTIVITIES
        while wait_for_user_activity:
            print "Waiting for user activity !!!!!!!!!!!^S"
            if(any(isfile(join(params["snapshots_directory"], i)) for i in listdir(params["snapshots_directory"]))):
                wait_for_user_activity = 0
            time.sleep(1)
        #AFTER USER PRESS START
        if message:
            # do something with the message
            print(message)
            input_data = json.loads(message['data'])
            if input_data == {"Channel":"KILL"}:
                subscribed_channels.unsubscribe()
                print 'KILL was observed. Terminate the session...'
                # write user feedbacks to logs
                feedback_file = open(os.path.join(params["userlogs_directory"],str(time.time())+'_userStop.txt'),"w")
                feedback_file.write(json.dumps(input_data))
                feedback_file.close()
                command = 'python generateExcel.py'
                os.popen("sudo -S %s"%(command), 'w').write('thanhtung#%!@')
                redis_IO.publish('EndTask', os.path.dirname(os.path.realpath(__file__))+'/listAll.xlsx')
                #sys.exit()
                os.execl(sys.executable, sys.executable, *sys.argv)
            elif "user_openlink" in input_data:
                # write user feedbacks to logs
                feedback_file = open(os.path.join(params["userlogs_directory"],str(time.time())+'_userOpenLink.txt'),"w")
                feedback_file.write(json.dumps(input_data))
                feedback_file.close()
                redis_IO.publish('clickBehavior',json.dumps(input_data).replace("\\\\","/").strip())
            else:
                #process the message from the frontend
                iteration = iteration +1
                print 'Iteration = %d' %iteration
                new_explicit_fb_flag = True
                # write user feedbacks to logs
                feedback_file = open(os.path.join(params["userlogs_directory"],str(time.time())+'_userfeedbacks.txt'),"w")
                feedback_file.write(json.dumps(input_data))
                feedback_file.close()
                # save user feedbacks to update the model in the next iteration
                exp_feedbacks = input_data.get('user_feedback')
                for i in range(len(exp_feedbacks)):
                    id = int(exp_feedbacks[i][0]) #id of the selected item
                    #fb_Val coding: 1: pinning, 0:unpinning, -1:removing
                    fb_val = float(exp_feedbacks[i][1]) #feedback of the selected item

                    #TODO: this is a HACK. we assume that document ID is ID + 600000.
                    # This way the frontend can use the same logic for documents and terms.
                    if id >= 600000: # then it is a document feedback
                        #the input is like {"user_feedback":[[doc_id+600000,feedback_val],...]}
                        id = id - 600000
                        # Based on FOCUS requirements we will remove the previous feedback on the same item
                        repeated_indx = [index for index, j in enumerate(selected_docs) if j == id]
                        if len(repeated_indx) > 0:
                            del selected_docs[repeated_indx[0]]
                            del feedback_docs[repeated_indx[0]]
                        #First remove the same index feedback and then if it was 1 add it to the feedback list (O.W. just remove)
                        if fb_val == 1: # if a doc is selected
                            feedback_docs.append(fb_val)
                            selected_docs.append(id)
                    else: #it is a term feedback
                        #the input is like {"user_feedback":[[term_id,feedback_val],...]}
                        # Based on FOCUS requirements we will remove the previous feedback on the same item
                        repeated_indx = [index for index, j in enumerate(selected_terms) if j == id]
                        if len(repeated_indx) > 0:
                            del selected_terms[repeated_indx[0]]
                            del feedback_terms[repeated_indx[0]]
                        #First remove the same index feedback and then if it was 1 add it to the feedback list (O.W. just remove)
                        if fb_val == 1: # if an item is pinned
                            pinned_item.append(id)
                            feedback_terms.append(fb_val)
                            selected_terms.append(id)
                        if fb_val == 0: # if an item is unpinned
                            pinned_item.remove(id)

                # Get explicit feedback on documents
                #the input is like {"user_feedback_doc":[[doc_id,feedback_val],...]}
                #exp_doc_feedbacks = input_data.get('user_feedback_doc')
                #for i in range(len(exp_doc_feedbacks)):
                #    id = int(exp_doc_feedbacks[i][0]) #id of the selected doc
                #    #fb_Val coding: 1: pinning, 0:unpinning, -1:removing
                #    fb_val = float(exp_doc_feedbacks[i][1]) #feedback of the selected item
                #    # Based on FOCUS requirements we will remove the previous feedbacks on the same item
                #    repeated_indx = [index for index, j in enumerate(selected_docs) if j == id]
                #    if len(repeated_indx) > 0:
                #        del selected_docs[repeated_indx[0]]
                #        del feedback_docs[repeated_indx[0]]
                #    #First remove the same index feedback and then if it was 1 add it to the feedback list (O.W. just remove)
                #    if fb_val == 1: # if a doc is selected
                #        feedback_docs.append(fb_val)
                #        selected_docs.append(id)

                currently_shown = input_data.get('currently_shown')
        else:
            # No new msg has arrived (no new explicit feedback)
            new_explicit_fb_flag = False
        time.sleep(1)
        update_interval = update_interval - 1

    #in case there was no explicit feedback then wait a bit and then update the suggestions
    #if new_explicit_fb_flag == False:
    #    time.sleep(6)  # be nice to the system :)


    # 3.1 check the snapshot folder and consider positive feedback for the real-time generated snapshots
    # the snapshot format is doc = [(term_idx,freq),..]
    print 'Loading real-time generated snapshots...'
    all_online_docs = []   # all snapshots generated from realtime user activity
    fv_online_docs = []    # considered snapshots generated from realtime user activity
    fb_online_docs = []    # dummy feedback for the newly generated snapshots
    for document in os.listdir(params["snapshots_directory"]):
        if ".npy" in document:
            #print params["snapshots_directory"]+"/"+document
        #if document != ".DS_Store" and document != "readme.txt":
            # load the numpy file
            snapshot_fv = np.load(params["snapshots_directory"]+"/"+document)
            if len(snapshot_fv)>0:
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
        # posterior inference
        user_model.learn()
        # Thompson sampling for coupled EVE
        #TODO: test having K thompson sampling for the K recommendations
        if params["Thompson_exploration"]:
            theta = user_model.thompson_sampling()
        else:
            theta = user_model.Mu
        scored_docs = np.dot(projector.doc_f_mat, theta)
        scored_terms = np.dot(projector.term_f_mat, theta)

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


    if params["FOCUS_UI"]:
        #VUONG: retrieve X set (5 new recent snapshots)
        fnames = []
        for fname in os.listdir(params["snapshots_directory"]):
            if(".npy" in fname):
                fnames.append(fname)
        fnames.sort()
        fnames = list(reversed(fnames))
        # X_keywords = []
        # X_apps = []
        # X_persons = []
        # X_documents = []
        print('5 new snapshots : ')
        # position_keyword = 0
        # position_person = 0
        for i in range(min(len(fnames), 5)):
            print(fnames[i])
        #     for keyword in json.load(open(params["keywords_directory"]+"/"+fnames[i].replace('.npy',''))):
        #         X_keywords.append((position_keyword,keyword))
        #         position_keyword+=1
        #     for person in json.load(open(params["persons_directory"]+"/"+fnames[i].replace('.npy',''))):
        #         X_persons.append((position_person,person))
        #         position_person+=1
        #     X_apps_data = json.load(open(params["apps_directory"]+'/'+fnames[i].replace('.npy','')))
        #     X_documents.append([i,X_apps_data['title'],X_apps_data['url'],os.path.join(snapshot_directory.replace("original","lab/original"), X_apps_data['filename']+".jpeg"),X_apps_data['appname']])
        #     if 'chrome' in X_apps_data["appname"].lower() or 'safari' in X_apps_data["appname"].lower() or 'firefox' in X_apps_data["appname"].lower():
        #         parsed_uri = urlparse(X_apps_data["url"])
        #         X_apps.append((i,'{uri.netloc}'.format(uri=parsed_uri)))
        #     else:
        #         X_apps.append((i,X_apps_data["appname"]))
        # X_amount_keywords = len(X_keywords)
        # X_amount_persons = len(X_persons)
        # X_amount_apps = len(X_apps)
        # X_amount_documents = len(X_documents)
        # #NOTE: This is an extra code to keep all entities about X which is separated from the sample
        # X_data = {}
        # X_data['keywords'] = X_keywords
        # X_data['people'] = X_persons
        # X_data['applications'] = X_apps
        # X_data['document_ID'] = X_documents
        # X_file = open(os.path.join(params["userlogs_directory"],str(time.time())+'_AllX.txt'),"w")
        # X_file.write(json.dumps(X_data))
        # X_file.close()

        #VUONG: Randomize the X set if the length is > 10
        # if X_amount_keywords > 10:
        #     shuffle_list = np.random.choice(len(X_keywords), 10, replace=False)
        #     X_keywords = [(X_keywords[shuffle_list[i]]) for i in range(len(shuffle_list))]
        # if X_amount_persons > 10:
        #     shuffle_list = np.random.choice(len(X_persons), 10, replace=False)
        #     X_persons = [(X_persons[shuffle_list[i]]) for i in range(len(shuffle_list))]
        # #NOTE: Amount of snapshots is less than or equal to 5, so no sampling for apps and docs
        # X_data = {}
        # X_data['keywords'] = X_keywords
        # X_data['people'] = X_persons
        # X_data['applications'] = X_apps
        # X_data['document_ID'] = X_documents
        # #VUONG: write X_data to logs
        # X_file = open(os.path.join(params["userlogs_directory"],str(time.time())+'_X.txt'),"w")
        # X_file.write(json.dumps(X_data))
        # X_file.close()

        #TODO: REMOEV THIS PART after connectiong to the front end
        for view in range(1, data.num_views):
            print 'view %d:' %view
            for i in range(min(params["suggestion_count"],data.num_items_per_view[view])):
                print '    %d,' %sorted_views_list[view-1][i] + ' ' + data.feature_names[sorted_views_list[view-1][i]]
        print 'Relevant document IDs (for debugging):'
        for i in range(params["suggestion_count"]):
            print '    %d' %sorted_docs_valid[i]
        #TODO: REMOEV THIS PART (END)

        # save the new recommendations in this iteration and all the recommendations till now
        new_recommendations = []
        for view in range(1, data.num_views):
            for i in range(min(params["suggestion_count"],data.num_items_per_view[view])):
                new_recommendations.append(sorted_views_list[view-1][i])
                if sorted_views_list[view-1][i] not in set(recommended_terms):
                    recommended_terms.append(sorted_views_list[view-1][i])

        #VUONG: Retrieve Y set from the model, Y set has equivalent amount of entities per type to X set, but at least 10
        # Y_keywords = [(i, data.feature_names[sorted_views_list[0][i]]) for i in range(min( max(X_amount_keywords,10) ,data.num_items_per_view[1]))]
        # Y_apps = [(i, data.feature_names[sorted_views_list[1][i]]) for i in range(min( max( X_amount_apps ,10) ,data.num_items_per_view[2]))]
        # Y_persons = [(i, data.feature_names[sorted_views_list[2][i]]) for i in range(min( max( X_amount_persons ,10) ,data.num_items_per_view[3]))]
        # Y_documents = [(i,loadLOG(sorted_docs_valid[i])['title'],loadLOG(sorted_docs_valid[i])['url'],os.path.join(snapshot_directory, file_names[sorted_docs_valid[i]].replace("txt","jpeg")), loadLOG(sorted_docs_valid[i])['appname']) for i in range(min(50,data.num_items_per_view[0]))]
        
        # #NOTE: This is an extra code to keep all entities about Y which is separated from the sample
        # Y_data = {}
        # Y_data['keywords'] = Y_keywords
        # Y_data['people'] = Y_persons
        # Y_data['applications'] = Y_apps
        # Y_data['document_ID'] = Y_documents
        # Y_file = open(os.path.join(params["userlogs_directory"],str(time.time())+'_AllY.txt'),"w")
        # Y_file.write(json.dumps(Y_data))
        # Y_file.close()

        # #VUONG: Randomize the Y set if the length is > 10
        # if len(Y_keywords) > 10:
        #     shuffle_list = np.random.choice(len(Y_keywords), 10, replace=False)
        #     Y_keywords = [(Y_keywords[shuffle_list[i]]) for i in range(len(shuffle_list))]
        # if len(Y_persons) > 10:
        #     shuffle_list = np.random.choice(len(Y_persons), 10, replace=False)
        #     Y_persons = [(Y_persons[shuffle_list[i]]) for i in range(len(shuffle_list))]
        # #NOTE: no sampling for apps and docs
        # Y_data = {}
        # Y_data['keywords'] = Y_keywords
        # Y_data['people'] = Y_persons
        # Y_data['applications'] = Y_apps
        # Y_data['document_ID'] = Y_documents
        # #VUONG: write Y_data to logs
        # Y_file = open(os.path.join(params["userlogs_directory"],str(time.time())+'_Y.txt'),"w")
        # Y_file.write(json.dumps(Y_data))
        # Y_file.close()

        #organize the recommentations in the right format
        data_output = {}
        data_output["keywords"] = [(sorted_views_list[0][i],data.feature_names[sorted_views_list[0][i]],
                                    scored_terms[sorted_views_list[0][i]]) for i in range(min(params["suggestion_count"],data.num_items_per_view[1]))]
        data_output["applications"] = [(sorted_views_list[1][i],data.feature_names[sorted_views_list[1][i]],
                                        scored_terms[sorted_views_list[1][i]]) for i in range(min(params["suggestion_count"],data.num_items_per_view[2]))]
        data_output["people"] = [(sorted_views_list[2][i],data.feature_names[sorted_views_list[2][i]],
                                    scored_terms[sorted_views_list[2][i]], loadPeoplePic(data.feature_names[sorted_views_list[2][i]])) for i in range(min(params["suggestion_count"],data.num_items_per_view[3]))]
        # TODO: how many document? I can also send the estimated relevance.
        #data_output["document_ID"] = [(sorted_docs_valid[i],loadLOG(sorted_docs_valid[i])['title'],loadLOG(sorted_docs_valid[i])['url']) for i in range(params["suggestion_count"])]
        #TODO: THis is the hack to distinguish doc and term IDS. Add 600000 to doc IDs for frontend
        #data_output["document_ID"] = [(sorted_docs_valid[i],loadLOG(sorted_docs_valid[i])['title'],loadLOG(sorted_docs_valid[i])['url'],os.path.join(snapshot_directory, "1513349785.60169.jpeg"), loadLOG(sorted_docs_valid[i])['appname']) for i in range(100)]
        data_output["document_ID"] = [(sorted_docs_valid[i]+600000,loadLOG(sorted_docs_valid[i])['title'],loadLOG(sorted_docs_valid[i])['url'],'file://'+urllib.quote(os.path.join(snapshot_directory, file_names[sorted_docs_valid[i]].replace("txt","jpeg"))), loadLOG(sorted_docs_valid[i])['appname']) for i in range(min(50,data.num_items_per_view[0]))]

        print data_output["keywords"]
        #Compute the similarity matrix which is needed for FOCUS UI:
        # I can do this by prepare a similarity matrix (e.g. cos similarity) between all the recommended terms
        # The similarities are calculated in the latent space (based on the feature vectors).
        # I will do this for all the "new_recommendations" and "pinned_item" and send it to frontend every iteration
        # list of items that we want to calculate their pair similarity
        #item_list = list(set(new_recommendations + currently_shown)) #commented out (old version)
        item_list = list(set(new_recommendations + pinned_item))
        # an array to hold the feature vectors
        recommended_fv = np.empty([len(item_list), projector.num_features])
        for i in range(len(item_list)):
            recommended_fv[i, :] = projector.item_fv(item_list[i]) #get the feature vector
        #Compute the dot products
        sim_matrix = np.dot(recommended_fv, recommended_fv.T)
        #normalize the dot products
        sim_diags = np.diagonal(sim_matrix)
        sim_diags = np.sqrt(sim_diags)
        for i in range(len(item_list)):
            sim_matrix[i,:] = sim_matrix[i,:]/sim_diags
        for i in range(len(item_list)):
            sim_matrix[:,i] = sim_matrix[:,i]/sim_diags
        #save pairwise similarities in a list of tuples
        all_sims = [(item_list[i],item_list[j],sim_matrix[i,j])
                    for i in range(len(item_list)-1) for j in range(i+1,len(item_list))]
        data_output["pair_similarity"] = all_sims
        #print data_output

        #send the output to the frontend
        redis_IO.publish('entityData', json.dumps(data_output))
        # writeToFile('peopleurl.json',allpeople)
        
        #VUONG: Retrive top-10 UI set
        # UI_keywords = [data_output["keywords"][i] for i in range(10)]
        # UI_persons = [data_output["people"][i] for i in range(10)]
        # UI_apps = [data_output["applications"][i] for i in range(10)]
        # UI_documents = [data_output["document_ID"][i] for i in range(min(50, len(data_output["document_ID"])))]

        # UI_data = {}
        # UI_data['keywords'] = UI_keywords
        # UI_data['people'] = UI_persons
        # UI_data['applications'] = UI_apps
        # UI_data['document_ID'] = UI_documents

        # UI_file = open(os.path.join(params["userlogs_directory"],str(time.time())+'_UI.txt'),"w")
        # UI_file.write(json.dumps(UI_data))
        # UI_file.close()


        ## write the backend output in a file
        #with open('data.txt', 'w') as outfile:
        #    json.dump(data_output, outfile)


#TODO: Save the necessary arrays for the evaluation
