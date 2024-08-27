# DQC

### Abstract

Distributed quantum computing (DQC) is a rapidly evolving field with its own unique challenges. Distributing a quantum algorithm involves several key steps and considerations. The steps involve decomposition at various levels of abstraction, given the underlying quantum stack and quantum network capabilities. In our DQC design explorations, we focus on the distribution at the algorithm and circuit levels. 
Algorithmic distribution involves distributing tasks before compilation, allowing different quantum processing units (QPUs) to receive distinct parts of an algorithm. 
Circuit distribution involves executing a quantum algorithm in a distributed manner at the circuit execution level using circuit and adaptive quantum technologies. If entanglement across QPUs is supported, then quantum states can be shared between qubits on remote quantum processors. This requires a specialized architecture with data and communication qubits with non-local gates such as telegates and teledata gates.

This library presents our progress towards a framework for exploring quantum distribution at the algorithm and circuit levels. Our implementation and case studies demonstrate the feasibility of our approach and show effective pathways for distributed quantum algorithm experiments.

### Framework Idea

Our framework caters to different adaptive capabilities of quantum computing (QC) platforms (e.g., quantum runtime, mid-circuit measurement, dynamic circuits, or network entanglement) and different quantum job types (e.g., simulating, parallelizing, bench-marking, or scaling algorithms).
At the circuit level, a quantum algorithm written in a specific language (e.g., Qiskit~\cite{qiskit}) can be executed on different quantum simulators or quantum hardware processing units (QPUs). Our framework aims to support performance experiments (e.g., comparing programs written in Qiskit, Q#, PennyLane, or Cirq). The framework will highlight the advantages of one language over others by running the algorithm on a series of simulators or QPUs.

At the algorithm level, variational quantum algorithm (VQA)~\cite{deep_vqe, accelerated_vqe} experiments can be conducted by leveraging hybrid quantum-classical architectures (e.g., quantum run-times or mid-circuit measurement). To improve the scalability of quantum circuit execution, big circuits can be decomposed to run on different QPUs by sharing quantum states through network entanglement. 

Our software framework provides infrastructure, virtual machines, and taskmasters to cater to job types and adaptive capabilities. One of the core requirements for DQC is entanglement across a network of QPUs. This capability is pivotal for enhancing the scalability and performance of distributed quantum algorithms. By managing entanglement efficiently, our framework can leverage the full potential of distributed quantum computing, enabling larger and more complex computations. Numerous experiments can be conducted with adaptive technologies, such as dynamic quantum circuits and mid-circuit measurement. We can experiment with algorithm and circuit scalability by leveraging entanglement swapping through simulation.

The framework provides scripts to automate the deployment of distributed quantum algorithms using virtual machines (VMs), simulators, hybrid quantum-classical architectures, and quantum networks. One featured VM acts as an orchestrator of the worker nodes. An example scenario is depicted in Fig.~\ref{fig:software_archtecture}. The orchestrator distributes the components that need to be parallelized to worker nodes via Redis container technology. Once a worker node completes processing, the results are sent back to the orchestrator, which in turn amalgamates the results, calculates algorithm-specific summary information, and visualizes the outcomes.


### References
To be added. 