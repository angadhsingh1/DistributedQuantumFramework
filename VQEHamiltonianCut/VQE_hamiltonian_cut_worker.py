# General imports
import numpy as np
import redis
import json
import sys
# Pre-defined ansatz circuit and operator class for Hamiltonian
from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import SparsePauliOp

# SciPy minimizer routine
from scipy.optimize import minimize

# Plotting functions
import matplotlib.pyplot as plt

# runtime imports
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import Session, EstimatorV2 as Estimator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="qiskit_ibm_runtime")

cost_history_dict = {
    "prev_vector": None,
    "iters": 0,
    "cost_history": [],
}

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

def process_received_data(data):
    """Process the received data and convert it to a SparsePauliOp."""
    print(f"Processing received data: {data}")
    
    if isinstance(data, dict) and 'paulis' in data and 'coeffs' in data:
        # Handle the expected dictionary format
        paulis = data['paulis']
        coeffs = [complex(c['real'], c['imag']) for c in data['coeffs']]
        return SparsePauliOp(paulis, coeffs)
    elif isinstance(data, list):
        # Handle the list format
        if all(isinstance(item, (int, float)) for item in data):
            # If it's a list of numbers, treat it as parameters
            # You might need to adjust this part based on how these parameters are meant to be used
            return data
        else:
            # If it's a list of [pauli_string, coefficient] pairs
            return SparsePauliOp.from_list(data)
    else:
        raise ValueError(f"Unexpected data format: {type(data)}")
    
def numpy_to_python(obj):
    """Convert numpy types to Python native types."""
    if isinstance(obj, (np.integer, np.floating, np.bool_)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

def serialize_optimize_result(result):
    """
    Serialize an OptimizeResult object to a JSON string.
    
    :param result: OptimizeResult object
    :return: JSON string
    """
    result_dict = {
        'x': numpy_to_python(result.x),
        'fun': numpy_to_python(result.fun),
        'success': numpy_to_python(result.success),
        'message': result.message,
        'nfev': numpy_to_python(result.nfev),
    }

    # Optionally include attributes that might not always be present
    optional_attrs = ['nit', 'status', 'jac']
    for attr in optional_attrs:
        if hasattr(result, attr):
            result_dict[attr] = numpy_to_python(getattr(result, attr))

    return json.dumps(result_dict)

def main(worker_id):
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    print(f"Worker {worker_id} started")
    
    while True:
        print(f"Worker {worker_id} waiting for task...")
        # Wait for start signal
        
        start_signal= r.blpop(f'worker:{worker_id}:control', timeout=180)
        
        if not start_signal:
            print(f"Worker {worker_id} timed out waiting for start signal")
            break
        
        print(f"Worker {worker_id} received start signal")
        task = r.blpop(f'worker:{worker_id}:tasks_queue', timeout=180)

        if task:
            print(f"Worker {worker_id} received task")
            print(f"Received task: {json.dumps(task, indent=2)}")
            
            task_data = json.loads(task[1])
            hamiltonian_term_data = task_data['data']
            print("Hamiltonian term on worker", hamiltonian_term_data)
            
            # Process the received data
            hamiltonian_processed_data = process_received_data(hamiltonian_term_data)
            print(f"Processed data: {hamiltonian_processed_data}")
            print("Processed data type", type(hamiltonian_processed_data))
            
            # THIS IS WHERE THE NUMBER OF QUBITS CAN BE FIXED ON INITIAL HAMILTONIAN TERM
            ansatz = EfficientSU2(hamiltonian_processed_data.num_qubits)
            ansatz.decompose().draw("mpl", style="iqp")
            num_params = ansatz.num_parameters
            print(f"Number of parameters for given Hamiltonian: {num_params}")
            
            backend_passed = AerSimulator()
            pm = generate_preset_pass_manager(backend=backend_passed, optimization_level=3)
            ansatz_isa = pm.run(ansatz)
            hamiltonian_isa = hamiltonian_processed_data.apply_layout(layout=ansatz_isa.layout)
            print("hamiltonian_isa type", hamiltonian_isa)
            
            x0 = 2 * np.pi * np.random.random(num_params)
            print("Initial parameters x0", x0)
            
            result = parallel_cost_function_VM(x0, ansatz_isa, hamiltonian_isa, backend_passed)
            print("Result from minimization", result)
            print("Result type", type(result))
            json_result = serialize_optimize_result(result)
            
            # r.rpush('result_queue', json_result)
            r.rpush(f'worker:{worker_id}:results', json_result)
            print(f"Received result: {json_result}")
            print(f"Worker {worker_id} pushed result to queue")

            with open(f'worker_output_{worker_id}.txt', 'a') as f:
                f.write(f"Processed task {task_data['id']}\n")
        else:
            print(f"Worker {worker_id} timed out waiting for task")
            break

    print(f"Worker {worker_id} finished")

if __name__ == "__main__":
    worker_id = sys.argv[1]
    main(worker_id)