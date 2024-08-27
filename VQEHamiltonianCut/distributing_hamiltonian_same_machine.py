# General imports
import numpy as np

# SciPy minimizer routine
from scipy.optimize import minimize

# Pre-defined ansatz circuit and operator class for Hamiltonian
from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import SparsePauliOp

# runtime imports
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import Session, EstimatorV2 as Estimator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="qiskit_ibm_runtime")


def cost_func(params, ansatz, hamiltonian, estimator):
    """Evaluate a single Hamiltonian term in a separate IBM Runtime session"""
    pub = (ansatz, [hamiltonian], [params])
    result = estimator.run(pubs=[pub]).result()
    energy = result[0].data.evs[0]
    return energy

def parallel_cost_function_VM(x0, ansatz_isa, hamiltonian_isa, backend_passed):
    """
    Evaluate the cost function in parallel for each Hamiltonian term
    """
    
    print("----------------- Starting parallel minimization -----------------")
    print("Initial hamiltonian in minimization: ", hamiltonian_isa)
    print("Initial parameters in minimization: ", x0)
    print("Initial ansatz in minimization: ", ansatz_isa)
        
    with Session(backend=backend_passed) as session:
        estimator = Estimator(session=session)
        estimator.options.default_shots = 10000
        
        result = minimize(
            cost_func,
            x0,
            args=(ansatz_isa, hamiltonian_isa, estimator),
            method="cobyla",
        )
    
    print("----------------- Ending parallel minimization -----------------")
    return result

def calculate_total_energy(results):
    total_energy = 0
    with open('final_results.txt', 'w') as f:
        # Flatten the results into a single list of result dictionaries
        all_results = [result for worker_results in results.values() for result in worker_results]
        
        for result in all_results:
            if isinstance(result, dict) and 'fun' in result:
                # If the result is a dictionary with a 'fun' key
                f.write(f"Partial energy = {result['fun']}\n")
                total_energy += result['fun']
            else:
                print(f"Unexpected result format: {result}")

        f.write(f"\nTotal Energy: {total_energy}\n")

    print(f"All tasks completed. Results saved in 'final_results.txt'")
    print(f"Total Energy: {total_energy}")
    
def initialize_results(number_of_workers):
    """
    Initialize results dictionary for the given number of workers.

    Parameters:
    - number_of_workers (int): Number of worker nodes.

    Returns:
    - dict: Dictionary to store results for each worker.
    """
    return {i: [] for i in range(1, number_of_workers + 1)}

def print_hamiltonian_details(hamiltonian):
    """
    Print details of the Hamiltonian.

    Parameters:
    - hamiltonian (SparsePauliOp): The Hamiltonian operator.
    """
    print("Hamiltonian type", hamiltonian)
    print("Hamiltonian Pauli operator data", hamiltonian.paulis)
    print("Hamiltonian Pauli operator coefficients", hamiltonian.coeffs)

def process_hamiltonian_term(hamiltonian_term):
    """
    Process a single Hamiltonian term by creating and optimizing the ansatz,
    and performing parallel cost function minimization.

    Parameters:
    - hamiltonian_term (SparsePauliOp): A term of the Hamiltonian.

    Returns:
    - dict: The result from the minimization process.
    """
    print(f"Hamiltonian term {hamiltonian_term}")
    
    ansatz = EfficientSU2(hamiltonian_term.num_qubits)
    ansatz.decompose().draw("mpl", style="iqp")
    num_params = ansatz.num_parameters
    print(f"Number of parameters for given Hamiltonian: {num_params}")
    
    backend_passed = AerSimulator()
    pm = generate_preset_pass_manager(backend=backend_passed, optimization_level=3)
    ansatz_isa = pm.run(ansatz)
    hamiltonian_isa = hamiltonian_term.apply_layout(layout=ansatz_isa.layout)
    print("hamiltonian_isa type", hamiltonian_isa)
    
    x0 = 2 * np.pi * np.random.random(num_params)
    
    result = parallel_cost_function_VM(x0, ansatz_isa, hamiltonian_isa, backend_passed)
    return result

def process_hamiltonian(hamiltonian, number_of_workers):
    """
    Process all terms in the Hamiltonian and collect results for each worker.

    Parameters:
    - hamiltonian (SparsePauliOp): The Hamiltonian operator.
    - number_of_workers (int): Number of worker nodes.

    Returns:
    - dict: Dictionary of results for each worker.
    """
    results = initialize_results(number_of_workers)
    
    for i, hamiltonian_term in enumerate(hamiltonian):
        result = process_hamiltonian_term(hamiltonian_term)
        results[i+1].append(result)
    
    return results

def main():
    """
    Main function to execute the VQE algorithm, including defining Hamiltonian,
    processing each term, and calculating total energy.
    """
    number_of_workers = 4
    
    hamiltonian = SparsePauliOp.from_list([("YZ", 0.3980), ("ZI", -0.3980), ("ZZ", -0.0113), ("XX", 0.1810)])
    
    print_hamiltonian_details(hamiltonian)
    
    results = process_hamiltonian(hamiltonian, number_of_workers)
    
    print("All results received", results)
    
    # Process and save final results
    calculate_total_energy(results)

if __name__ == "__main__":
    main()