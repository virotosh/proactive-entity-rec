
# Code logic

The starting point of the code is lab/main.py file. However, please note that the user data is not available in this repository.
Please refer to lab/DataLoader.py, lab/DataProjector.py, and lab/UserModelCoupled.py as the main recommendation system components.

 main.py controls the following process:
 
      1. Load the experiment logs 
      2. Create (or load) the low dimensional representation of data
      3. Interaction loop:
          3.1. Receive new snapshots (real-time documents)
          3.2. Update the user model
          3.3. Recommend items from different views
          3.4. gather feedback for items
          

## Reference

If you are using this source code in your research please consider citing us:

 * Giulio Jacucci, Pedram Daee, Tung Vuong, Salvatore Andolina, Khalil Klouche, Mats SjÖberg, Tuukka Ruotsalo, and Samuel Kaski. 2021. **Entity Recommendation for Everyday Digital Tasks**. ACM Trans. Comput.-Hum. Interact. 28, 5, Article 29 (October 2021), 41 pages. DOI:https://doi.org/10.1145/3458919

