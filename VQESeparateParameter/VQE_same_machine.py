import numpy as np
import redis
import json
import time
from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
import sys
from scipy.optimize import minimize
from qiskit_ibm_runtime import Session
from qiskit_ibm_runtime import EstimatorV2 as Estimator
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="qiskit_ibm_runtime")

def define_hamiltonian_and_ansatz():
    """
    Define the Hamiltonian and Ansatz for the VQE algorithm.

    Returns:
    - hamiltonian (SparsePauliOp): The Hamiltonian operator.
    - ansatz (EfficientSU2): The ansatz circuit.
    """
    hamiltonian = SparsePauliOp.from_list(
        [("YZ", 0.3980), ("ZI", -0.3980), ("ZZ", -0.0113), ("XX", 0.1810)]
    )
    ansatz = EfficientSU2(hamiltonian.num_qubits)
    return hamiltonian, ansatz

def choose_backend_and_optimize_ansatz(ansatz, hamiltonian):
    """
    Choose the backend simulator and optimize the ansatz.

    Parameters:
    - ansatz (EfficientSU2): The ansatz circuit.
    - hamiltonian (SparsePauliOp): The Hamiltonian operator.

    Returns:
    - backend_passed (AerSimulator): The backend simulator.
    - ansatz_isa (QuantumCircuit): Optimized ansatz circuit.
    - hamiltonian_isa (SparsePauliOp): Optimized Hamiltonian.
    """
    backend_passed = AerSimulator()
    pm = generate_preset_pass_manager(backend=backend_passed, optimization_level=3)
    ansatz_isa = pm.run(ansatz)
    hamiltonian_isa = hamiltonian.apply_layout(layout=ansatz_isa.layout)
    return backend_passed, ansatz_isa, hamiltonian_isa

def generate_initial_population(num_params):
    """
    Generate initial population for the parallel minimization.

    Parameters:
    - num_params (int): Number of parameters in the ansatz.

    Returns:
    - initial_population (list of numpy.ndarray): List of initial parameter sets.
    """
    x0 = 2 * np.pi * np.random.random(num_params)
    return [x0 + 0.1 * np.random.randn(len(x0)) for _ in range(4)]

def perform_minimization_for_population(ansatz_isa, hamiltonian_isa, backend_passed, initial_population):
    """
    Perform parallel minimization for each initial parameter set.

    Parameters:
    - ansatz_isa (QuantumCircuit): Optimized ansatz circuit.
    - hamiltonian_isa (SparsePauliOp): Optimized Hamiltonian.
    - backend_passed (AerSimulator): The backend simulator.
    - initial_population (list of numpy.ndarray): List of initial parameter sets.

    Returns:
    - results (dict): Dictionary of results indexed by iteration.
    """
    results = {}
    for i, initial_param in enumerate(initial_population):
        print(f"Pushed task {i+1}, with initial param {initial_param} to queue")
        result = parallel_minimize_VM(ansatz_isa, hamiltonian_isa, backend_passed, initial_param)
        print("Result:  ", result, "\n")
        results[f'iteration_{i+1}'] = result
    return results

def save_results_to_file(results, filename='vqe_on_single_machine.json'):
    """
    Save the results to a JSON file.

    Parameters:
    - results (dict): Dictionary of results to be saved.
    - filename (str): The name of the file where results will be saved.
    """
    with open(filename, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"All tasks completed. Results saved to '{filename}'")

def cost_func(params, ansatz, hamiltonian, estimator):
    """
    Calculates the energy cost function for the given parameters.

    Parameters:
    - params (numpy.ndarray): Parameters for the ansatz circuit.
    - ansatz (QuantumCircuit): The quantum circuit ansatz.
    - hamiltonian (SparsePauliOp): The Hamiltonian operator.
    - estimator (Estimator): IBM Quantum Runtime estimator.

    Returns:
    - float: Energy computed for the given parameters.
    """
    pub = (ansatz, [hamiltonian], [params])
    result = estimator.run(pubs=[pub]).result()
    energy = result[0].data.evs[0]
    return energy

def parallel_minimize_VM(ansatz, hamiltonian, backend_passed, initial_param):
    """
    Performs parallel minimization of the cost function using Cobyla method.

    Parameters:
    - ansatz (QuantumCircuit): The quantum circuit ansatz.
    - hamiltonian (SparsePauliOp): The Hamiltonian operator.
    - backend_passed (AerSimulator): Backend simulator for estimation.
    - initial_param (numpy.ndarray): Initial parameters for minimization.

    Returns:
    - dict: Dictionary containing 'energy', 'params', 'success', 'message' of the minimization result.
    """
    
    print("----------------- Starting parallel minimization -----------------")
    print("Initial parameters in minimization: ", initial_param)
    
    with Session(backend=backend_passed) as session:
        estimator = Estimator(session=session)
        
        def objective_function(params):
            return cost_func(params, ansatz, hamiltonian, estimator)
        
        result = minimize(objective_function, initial_param, method='cobyla')
    
    print("----------------- Ending parallel minimization -----------------")
    return {
        'energy': float(result.fun),  # Convert to native Python float
        'params': result.x.tolist(),  # Convert NumPy array to list
        'success': bool(result.success),  # Convert NumPy bool to Python bool
        'message': str(result.message)  # Ensure message is a string
    }

def main():
    """
    Main function to execute the VQE algorithm, including defining Hamiltonian and Ansatz,
    optimizing Ansatz, performing minimization, and saving results.
    """
    # Define Hamiltonian and Ansatz
    hamiltonian, ansatz = define_hamiltonian_and_ansatz()
    num_params = ansatz.num_parameters
    
    # Choose backend and optimize ansatz
    backend_passed, ansatz_isa, hamiltonian_isa = choose_backend_and_optimize_ansatz(ansatz, hamiltonian)
    
    # Generate initial population for parallel minimization
    initial_population = generate_initial_population(num_params)
    
    # Perform minimization for each initial parameter set
    results = perform_minimization_for_population(ansatz_isa, hamiltonian_isa, backend_passed, initial_population)
    
    # Write results to file
    save_results_to_file(results)

if __name__ == "__main__":
    main()