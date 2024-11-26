from scipy.optimize import minimize_scalar
import math

# Define the function f(x) = -2 * e^(-x) + e^(-x) * x
def f_to_maximize(x):
    return -2 * math.exp(-x) + math.exp(-x) * x

# Negate the function for finding the maximum using a minimizer
def neg_f(x):
    return -f_to_maximize(x)

# Find the maximum value by minimizing the negative of the function
result = minimize_scalar(neg_f, bounds=(0, 1), method='bounded')
absolute_max_value = -result.fun  # Negate back to get the actual maximum value
print(absolute_max_value)
 # type: ignore