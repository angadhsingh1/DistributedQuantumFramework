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
    ansatz = EfficientSU2(hamiltonian.num_qubits)
    num_params = ansatz.num_parameters
    
    x0 = 2 * np.pi * np.random.random(num_params)

    initial_population = [x0 + 0.1 * np.random.randn(len(x0)) for _ in range(4)]
        
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