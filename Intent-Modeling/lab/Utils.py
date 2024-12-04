# Pedram Daee <<pedram.daee@hiit.fi>>.

import numpy as np
def inv_woodbury(A_inv, C_inv, U, V):
    "Woodbury formula for computating the inverse of (A+UCV)"
    #(A+UCV)^-1 = A_inv - A_inv * U * (C_inv + V*A_inv*U)^-1 * V * A_inv
    temp1 = np.dot(V,A_inv)
    temp2 = C_inv + np.dot( temp1, U )
    temp2_inv = np.linalg.inv(temp2)
    temp3 = np.dot(A_inv,U)
    temp4 = np.dot(temp3,temp2_inv)
    temp5 = np.dot(temp4,temp1)
    return A_inv - temp5