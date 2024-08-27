# General imports
import numpy as np
import dask
from dask.distributed import Client, as_completed

# Pre-defined ansatz circuit and operator class for Hamiltonian
from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import SparsePauliOp

# SciPy minimizer routine
from scipy.optimize import minimize

# Plotting functions
import matplotlib.pyplot as plt

# runtime imports
from qiskit_ibm_runtime import QiskitRuntimeService, Session
from qiskit_ibm_runtime import EstimatorV2 as Estimator

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from qiskit_aer import AerSimulator

cost_history_dict = {
    "prev_vector": None,
    "iters": 0,
    "cost_history": [],
}

def cost_func(params, ansatz, hamiltonian, estimator):
    """Return estimate of energy from estimator

    Parameters:
        params (ndarray): Array of ansatz parameters
        ansatz (QuantumCircuit): Parameterized ansatz circuit
        hamiltonian (SparsePauliOp): Operator representation of Hamiltonian
        estimator (EstimatorV2): Estimator primitive instance
        cost_history_dict: Dictionary for storing intermediate results

    Returns:
        float: Energy estimate
    """
    pub = (ansatz, [hamiltonian], [params])
    result = estimator.run(pubs=[pub]).result()
    energy = result[0].data.evs[0]

    cost_history_dict["iters"] += 1
    cost_history_dict["prev_vector"] = params
    cost_history_dict["cost_history"].append(energy)
    # print(f"Iters. done: {cost_history_dict['iters']} [Current cost: {energy}]")

    return energy

def parallel_minimize(x0, ansatz, hamiltonian, estimator):
    client = Client()
    
    # Define objective function to be minimized
    def objective_function(params):
        return cost_func(params, ansatz, hamiltonian, estimator)

    # Generate initial population of parameter sets
    num_workers = sum(client.ncores().values())
    initial_population = [x0 + 0.1 * np.random.randn(len(x0)) for _ in range(num_workers)]

    futures = [client.submit(minimize, objective_function, x0=initial_params, method='cobyla') for initial_params in initial_population]

    results = []
    for future in as_completed(futures):
        result = future.result()
        results.append(result)
        print("Interim result:", result)

    best_result = min(results, key=lambda res: res.fun)
    client.close()

    return best_result

def main():
    hamiltonian = SparsePauliOp.from_list(
        [("YZ", 0.3980), ("ZI", -0.3980), ("ZZ", -0.0113), ("XX", 0.1810)]
    )

    ansatz = EfficientSU2(hamiltonian.num_qubits)
    ansatz.decompose().draw("mpl", style="iqp")

    num_params = ansatz.num_parameters
    print("Number of parameters", num_params)

    aer_sim = AerSimulator()
    pm = generate_preset_pass_manager(backend=aer_sim, optimization_level=3)

    ansatz_isa = pm.run(ansatz)
    ansatz_isa.draw(output="mpl", idle_wires=False, style="iqp")

    hamiltonian_isa = hamiltonian.apply_layout(layout=ansatz_isa.layout)

    x0 = 2 * np.pi * np.random.random(num_params)
    print("Initial parameters", x0)

    with Session(backend=aer_sim) as session:
        estimator = Estimator(session=session)
        # estimator.options.default_shots = 10000

        res = parallel_minimize(x0, ansatz_isa, hamiltonian_isa, estimator)

    print("Final parameters", res)

    all(cost_history_dict["prev_vector"] == res.x)

    cost_history_dict["iters"] == res.nfev

    fig, ax = plt.subplots()
    ax.plot(range(cost_history_dict["iters"]), cost_history_dict["cost_history"])
    ax.set_xlabel("Iterations")
    ax.set_ylabel("Cost")
    plt.draw()

if __name__ == "__main__":
    main()
