import numpy as np
import redis
import json
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
    print(f"Number of parameters: {num_params}")
    
    backend_passed = AerSimulator()
    pm = generate_preset_pass_manager(backend=backend_passed, optimization_level=3)
    ansatz_isa = pm.run(ansatz)
    hamiltonian_isa = hamiltonian.apply_layout(layout=ansatz_isa.layout)
    
    x0 = 2 * np.pi * np.random.random(num_params)
    initial_population = [x0 + 0.1 * np.random.randn(len(x0)) for _ in range(4)]
    
    # Push tasks to queue
    for i, initial_param in enumerate(initial_population):
        task = {"id": i, "data": initial_param.tolist()}
        r.lpush('task_queue', json.dumps(task))
        print(f"Pushed task {i} to queue")
    
    print(f"All tasks pushed. Waiting for results...")
    

if __name__ == "__main__":
    main()