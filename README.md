# Distributed Quantum Computing Sandbox


## Running Differernt Experiments:

Make sure to run Virtual Environment before running the experiments. Run the following command in root directory
`source .venv/bin/activate`

### EXP1. Running Multiple Virtual Machines on Different Simulator

On terminal from root project directory 
`cd MultipleVMSimple/`
`python3 VQE.py`

### EXP2. Multithreading using Dask Library
An alternate to sending a VQE experiment to mutiple Virtual machines is allocation of different processes within same computer. 

On terminal from root project directory 
`cd MultithreadingUsingDask/`
`python3 VQEMultithreadingUsingDask.py`

### EXP3. Running VQE using Separate Parameters

#### Option 1: Split the terminal into two : Make sure enable virtual environment in both terminals. 

For both terminals run:
`cd VQESeparateParameter-VSP/`

Terminal 1: `python3 VSPOrchestrator.py`

Run the commands on Terminal 2 one after another
Terminal 2: `python3 VSPWorker.py 1`
Terminal 2: `python3 VSPWorker.py 2`
Terminal 2: `python3 VSPWorker.py 3`
Terminal 2: `python3 VSPWorker.py 4`

The results are saved in final_results.txt in same directory. 

#### Option 2: Run the same experiment with using `for loops`
On terminal run: `python3 VSPUsingForLoops.py`
Results are saved in `vqe_on_single_machine.json`


### Summary

Distributed quantum computing (DQC) is a rapidly evolving field with its own unique challenges. Distributing a quantum algorithm involves several key steps and considerations. The steps involve decomposition at various levels of abstraction, given the underlying quantum stack and quantum network capabilities. In our DQC design explorations, we focus on the distribution at the algorithm and circuit levels. 


Algorithmic distribution involves distributing tasks before compilation, allowing different quantum processing units (QPUs) to receive distinct parts of an algorithm. 


Circuit distribution involves executing a quantum algorithm in a distributed manner at the circuit execution level using circuit and adaptive quantum technologies. If entanglement across QPUs is supported, then quantum states can be shared between qubits on remote quantum processors. This requires a specialized architecture with data and communication qubits with non-local gates such as telegates and teledata gates.

This library presents our progress towards a framework for exploring quantum distribution at the algorithm and circuit levels. Our implementation and case studies demonstrate the feasibility of our approach and show effective pathways for distributed quantum algorithm experiments.

### Framework Idea

Our framework caters to different adaptive capabilities of quantum computing (QC) platforms (e.g., quantum runtime, mid-circuit measurement, dynamic circuits, or network entanglement) and different quantum job types (e.g., simulating, parallelizing, bench-marking, or scaling algorithms).

At the circuit level, a quantum algorithm written in a specific language (e.g., Qiskit~\cite{qiskit}) can be executed on different quantum simulators or quantum hardware processing units (QPUs). Our framework aims to support performance experiments (e.g., comparing programs written in Qiskit, Q#, PennyLane, or Cirq). The framework will highlight the advantages of one language over others by running the algorithm on a series of simulators or QPUs.

At the algorithm level, variational quantum algorithm (VQA) experiments can be conducted by leveraging hybrid quantum-classical architectures (e.g., quantum run-times or mid-circuit measurement). To improve the scalability of quantum circuit execution, big circuits can be decomposed to run on different QPUs by sharing quantum states through network entanglement. 

Our software framework provides infrastructure, virtual machines, and taskmasters to cater to job types and adaptive capabilities. One of the core requirements for DQC is entanglement across a network of QPUs. This capability is pivotal for enhancing the scalability and performance of distributed quantum algorithms. By managing entanglement efficiently, our framework can leverage the full potential of distributed quantum computing, enabling larger and more complex computations. Numerous experiments can be conducted with adaptive technologies, such as dynamic quantum circuits and mid-circuit measurement. We can experiment with algorithm and circuit scalability by leveraging entanglement swapping through simulation.

The framework provides scripts to automate the deployment of distributed quantum algorithms using virtual machines (VMs), simulators, hybrid quantum-classical architectures, and quantum networks. One featured VM acts as an orchestrator of the worker nodes. An example scenario is depicted in Fig.~\ref{fig:software_archtecture}. The orchestrator distributes the components that need to be parallelized to worker nodes via Redis container technology. Once a worker node completes processing, the results are sent back to the orchestrator, which in turn amalgamates the results, calculates algorithm-specific summary information, and visualizes the outcomes.


### References
1. S.~DiAdamo, M. Ghibaudi, and J. Cruise, “Distributed quantum computing and network control for Accelerated VQE,” IEEE Transactions on Quantum Engineering, vol. 2, pp. 1–21, Jan. 2021. %doi:10.1109/tqe.2021.3057908 


2. N.M.~Neumann, R.~van Houte, and T.~Attema, “Imperfect distributed quantum phase estimation,” LNTCS~12142, pp. 605–615, 2020. %doi:10.1007/978-3-030-50433-5\_46

3. K.~Fujii et al., “Deep variational Quantum Eigensolver: A divide-and-conquer method for solving a larger problem with smaller size quantum computers,” PRX Quantum, vol. 3, no. 1, Mar. 2022.% doi:10.1103/prxquantum.3.010346 

4. H.~Situ et al., "Distributed Quantum Architecture Search", Mar. 2024. [Online]. Available: https://arxiv.org/pdf/2403.06214

5. Microsoft Learn, Overview of hybrid quantum computing--Azure Quantum, learn.microsoft.com/en-us/azure/quantum/hybrid-computing-overview (accessed Jul.~19, 2024).

6. IBM Quantum, "{Qiskit} 1.0.2," {www.ibm.com/quantum/qiskit}, 2024

7. D.~Ferrari et al., “Compiler design for distributed quantum computing,” IEEE Transactions on Quantum Engineering, vol. 2, pp. 1–20, Dec. 2020. %doi:10.1109/tqe.2021.3053921  

8. M.~Caleffi et al., “Distributed quantum computing – distributed control of Quantum Gates,” From Distributed Quantum Computing to Quantum Internet Computing, pp. 113–135, Dec. 2022. doi:10.1002/9781394185542.ch4 

9. A.~Yimsiriwattana and S.J.~Lomonaco, “Generalized GHZ states and distributed quantum computing,” arXiv:quant-ph/0402148