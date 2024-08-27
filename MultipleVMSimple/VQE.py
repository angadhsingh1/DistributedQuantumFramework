"""
Code taken from Qiskit Tutorial on Varaitional Quantum Eigensolver. 
The tutorial is not archived and not availbale IBM Quantum platform. 

"""


# General imports
import numpy as np

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

def main():

    hamiltonian = SparsePauliOp.from_list(
        [("YZ", 0.3980), ("ZI", -0.3980), ("ZZ", -0.0113), ("XX", 0.1810)])
    
    # hamiltonian_qaoa = SparsePauliOp.from_list(
    #     [("IIIZZ", 1), ("IIZIZ", 1), ("IZIIZ", 1), ("ZIIIZ", 1)])

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
        estimator.options.default_shots = 10000

        res = minimize(
            cost_func,
            x0,
            args=(ansatz_isa, hamiltonian_isa, estimator),
            method="cobyla",
        )

        
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
    
    
    
    """_summary_
    Final parameters  message: Optimization terminated successfully.
 success: True
  status: 1
     fun: -0.677611865234375
       x: [ 5.537e+00  7.017e+00 ... -9.589e-02  3.615e+00]
    nfev: 181
   maxcv: 0.0
    """