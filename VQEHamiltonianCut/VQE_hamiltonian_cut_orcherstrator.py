# General imports
import numpy as np
from dask.distributed import Client, as_completed
import numpy as np
import redis
import json
import time

# Pre-defined ansatz circuit and operator class for Hamiltonian
from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import SparsePauliOp


# runtime imports
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import Session, EstimatorV2 as Estimator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

def complex_to_dict(z):
    return {"real": z.real, "imag": z.imag}

def sparse_pauli_op_to_dict(sparse_pauli_op):
    """Convert a SparsePauliOp to a dictionary."""
    return {
        'paulis': sparse_pauli_op.paulis.to_labels(),
        'coeffs': [complex_to_dict(c) for c in sparse_pauli_op.coeffs.tolist()]
    }
    
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super(NumpyEncoder, self).default(obj)
    
def deserialize_optimize_result(json_string):
    """
    Deserialize a JSON string back to an OptimizeResult-like dictionary.
    
    :param json_string: JSON string of serialized OptimizeResult
    :return: Dictionary with OptimizeResult-like structure
    """
    result_dict = json.loads(json_string)
    
    # Convert lists back to numpy arrays where appropriate
    array_attrs = ['x', 'jac']
    for attr in array_attrs:
        if attr in result_dict and isinstance(result_dict[attr], list):
            result_dict[attr] = np.array(result_dict[attr])
    
    return result_dict
    
def distribute_tasks(r, hamiltonian, number_of_workers):
    for i, hamiltonian_term in enumerate(hamiltonian):
        print(f"Hamiltonian term {hamiltonian_term}")
        task = {
            "id": i,
            "data": sparse_pauli_op_to_dict(hamiltonian_term)
        }
        print(f"Pushing task: {json.dumps(task, indent=2)}")
        worker_id = (i % 5) + 1  # Round-robin distribution
        r.rpush(f'worker:{worker_id}:tasks_queue', json.dumps(task))
        print(f"Pushed task {i} to queue \n")
        
    # Signal all workers to start
    for i in range(1, number_of_workers+1):
        r.rpush(f'worker:{i}:control', 'start')

    print(f"All tasks pushed. Waiting for results...")
   
def collect_results(r, hamiltonian, number_of_workers):
    results = {i: [] for i in range(1, number_of_workers + 1)}
    completed_workers = set()
    total_tasks = len(hamiltonian)
    received_results = 0
    
    start_time = time.time()
    while len(completed_workers) < 5 and received_results < total_tasks:
        for i in range(1, number_of_workers + 1):
            if i in completed_workers:
                continue
            json_result = r.blpop(f'worker:{i}:results', timeout=1)
        
            if json_result:
                # Process result...
                result_data = json.loads(json_result[1])
                results[i].append(result_data)
                received_results += 1
                print(f"Received result from worker {i}: {json.dumps(result_data, indent=2)}")
                
                # Check if this worker has completed all its tasks
                if r.llen(f'worker:{i}:tasks_queue') == 0 and r.llen(f'worker:{i}:results') == 0:
                    completed_workers.add(i)
                    print(f"Worker {i} has completed all tasks")
            else:
                print(f"Waiting for results from worker {i}...")
        
        # Add a timeout condition
        if time.time() - start_time > 300:  # 5 minutes timeout
            print("Timeout reached. Exiting.")
            break
    
    if received_results < total_tasks:
        print(f"Warning: Only received {received_results} out of {total_tasks} expected results")
    
    return results


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
    
def main():
    number_of_workers = 4
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    print("Orchestrator started")
    
    hamiltonian = SparsePauliOp.from_list([("YZ", 0.3980), ("ZI", -0.3980), ("ZZ", -0.0113), ("XX", 0.1810)])
    print("Hamiltonian type", hamiltonian)
    print("Hamiltonian Pauli operator data", hamiltonian.paulis)
    print("Hamiltonian Pauli operator coefficients", hamiltonian.coeffs)
    
    ansatz = EfficientSU2(hamiltonian.num_qubits)
    ansatz.decompose().draw("mpl", style="iqp")
    num_params = ansatz.num_parameters
    print(f"Number of parameters: {num_params}")
    
    backend_passed = AerSimulator()
    pm = generate_preset_pass_manager(backend=backend_passed, optimization_level=3)
    ansatz_isa = pm.run(ansatz)
    hamiltonian_isa = hamiltonian.apply_layout(layout=ansatz_isa.layout)
    print("hamiltonian_isa type", hamiltonian_isa)
    
    # Distribute tasks
    distribute_tasks(r, hamiltonian, number_of_workers)

    # Wait for results
    results = collect_results(r, hamiltonian, number_of_workers)
    print("All results received")
    
    # Print results
    for worker_id, worker_results in results.items():
        print(f"Worker {worker_id}: {worker_results}")
        
    # Process and save final results
    calculate_total_energy(results)

    
if __name__ == "__main__":
    main()
