import redis
import json
import sys
import numpy as np
from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import SparsePauliOp
from scipy.optimize import minimize
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import Session
from qiskit_ibm_runtime import EstimatorV2 as Estimator
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="qiskit_ibm_runtime")

def cost_func(params, ansatz, hamiltonian, estimator):
    pub = (ansatz, [hamiltonian], [params])
    result = estimator.run(pubs=[pub]).result()
    energy = result[0].data.evs[0]
    return energy

def parallel_minimize_VM(ansatz, hamiltonian, backend_passed, initial_param):
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

def main(worker_id):
    r = redis.Redis(host='localhost', port=6379)
    print(f"Worker {worker_id} started")
    
    hamiltonian = SparsePauliOp.from_list(
        [("YZ", 0.3980), ("ZI", -0.3980), ("ZZ", -0.0113), ("XX", 0.1810)]
    )
    ansatz = EfficientSU2(hamiltonian.num_qubits)
    backend_passed = AerSimulator()
    pm = generate_preset_pass_manager(backend=backend_passed, optimization_level=3)
    ansatz_isa = pm.run(ansatz)
    hamiltonian_isa = hamiltonian.apply_layout(layout=ansatz_isa.layout)
    
    print(f"Worker {worker_id} waiting for a single task...")
    task = r.brpop('task_queue', timeout=10)
    if task:
        print(f"Worker {worker_id} received task")
        task_data = json.loads(task[1])
        initial_param = np.array(task_data['data'])
        result = parallel_minimize_VM(ansatz_isa, hamiltonian_isa, backend_passed, initial_param)
        result['id'] = task_data['id']
        
        # Ensure all numpy types are converted to native Python types
        result = {k: v.item() if isinstance(v, np.generic) else v for k, v in result.items()}
        
        r.lpush('result_queue', json.dumps(result))
        print(f"Worker {worker_id} pushed result to queue")
        
        with open(f'worker_output_{worker_id}.txt', 'a') as f:
            f.write(f"Processed task {task_data['id'], result}\\n")
    else:
        print(f"Worker {worker_id} timed out waiting for task")

    print(f"Worker {worker_id} finished")

if __name__ == "__main__":
    worker_id = sys.argv[1]
    main(worker_id)