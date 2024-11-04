import numpy as np
import redis
import json
import time
from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator

def main():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)

    print("Orchestrator started")
    
    hamiltonian = SparsePauliOp.from_list(
        [("YZ", 0.3980), ("ZI", -0.3980), ("ZZ", -0.0113), ("XX", 0.1810)]
    )
    
    number_of_workers = 4       # Can have any number of workers
    ansatz = EfficientSU2(hamiltonian.num_qubits)
    num_params = ansatz.num_parameters
    print(f"Number of parameters: {num_params}")
    
    backend_passed = AerSimulator()
    pm = generate_preset_pass_manager(backend=backend_passed, optimization_level=3)
    ansatz_isa = pm.run(ansatz)
    hamiltonian_isa = hamiltonian.apply_layout(layout=ansatz_isa.layout)
    
    x0 = 2 * np.pi * np.random.random(num_params)
    initial_population = [x0 + 0.1 * np.random.randn(len(x0)) for _ in range(number_of_workers)]
    
    # Push tasks to queue
    for i, initial_param in enumerate(initial_population):
        task = {"id": i, "data": initial_param.tolist()}
        r.lpush('task_queue', json.dumps(task))
        print(f"Pushed task {i} to queue")
    
    print(f"All tasks pushed. Waiting for results...")
    
    # Wait for results
    results = []
    start_time = time.time()
    while len(results) < len(initial_population):
        result = r.brpop('result_queue', timeout=1)
        if result:
            results.append(json.loads(result[1]))
            print(f"Received result for task {results[-1]['id']}")
        else:
            print("Waiting for results...")
        
        # Add a timeout condition
        if time.time() - start_time > 300:  # 5 minutes timeout
            print("Timeout reached. Exiting.")
            break
    
    # Process and save final results
    with open('final_results.txt', 'w') as f:
        for result in results:
            f.write(f"Task {result['id']}: Final energy = {result['energy']}, "
                    f"Parameters = {result['params']}\n")
    
    print(f"All tasks completed. Results saved in 'final_results.txt'")

if __name__ == "__main__":
    main()