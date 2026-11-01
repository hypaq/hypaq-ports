# HYPAQ Ports

**Optimization Intelligence for Smart Ports — AI-First, Quantum-Ready.**

HYPAQ Ports is an open laboratory for learning, modeling, and evaluating optimization approaches for port operations. It connects operational decisions with mathematical models, classical solvers, and quantum optimization experiments using Python and the Ket programming platform.

The project starts with small, explainable exercises and synthetic data. Its intended evolution is a reproducible collection of problem instances, formulations, validation tools, and benchmarks that researchers, students, developers, and industry practitioners can explore and extend.

> **Project status: initial development.** The three exercises described below are the initial roadmap. Their descriptions define planned scope and expected outputs; they do not indicate that executable notebooks, solver integrations, or an AI assistant are already available.

## Why port optimization?

Port operations involve interconnected decisions about vessel arrivals, berth availability, equipment allocation, and service schedules. An arrival delay or unavailable resource can affect waiting times, resource utilization, and the stability of an existing plan.

HYPAQ Ports explores how these decisions can be represented explicitly, solved, validated, and explained. The initial exercises focus on understanding the relationship between the operational problem, the mathematical formulation, and the behavior of different solution methods.

## AI-First, Quantum-Ready

| Principle | Intended implementation |
| --- | --- |
| **AI-First** | Assist users in describing a scenario, identifying missing information, proposing structured inputs, and interpreting verified results. |
| **Optimization Intelligence** | Make objectives, constraints, assumptions, solution quality, and trade-offs visible and auditable. |
| **Quantum-Ready** | Develop and validate QUBO/Ising formulations, then explore quantum algorithms on appropriately sized instances. |
| **Port-oriented** | Express problems and results in terms of vessels, berths, cranes, service demand, and operational schedules. |

The planned AI workflow will use validated input schemas and predefined modeling functions. Solvers will compute candidate solutions, independent checks will evaluate feasibility, and explanations will be grounded in those outputs. AI-generated interpretations will not constitute mathematical proofs of feasibility or optimality.

Quantum experiments will initially use **Ket with the KBW simulator**, running on classical hardware. These experiments support education and evaluation; they do not establish quantum advantage or production readiness.

## The first three exercises

| Exercise | Operational question | Initial scope | Expected output |
| --- | --- | --- | --- |
| **01 — Berth Allocation** | Where and when should each vessel be served? | A small, discrete berth allocation problem with synthetic arrivals and fixed service durations. | A berth schedule, waiting-time indicators, and a comparison of classical and quantum experiment results. |
| **02 — Quay Crane Allocation** | How should available cranes be assigned to vessels? | A simplified resource allocation problem with known productivity, demand, and availability. | A crane allocation schedule, demand coverage, and resource utilization indicators. |
| **03 — Disruption and Replanning** | How should a schedule change after a delay or resource outage? | Scenario analysis built on the berth allocation model. | A comparison of waiting time, feasibility, and changes to the original schedule. |

### Exercise 01 — Berth Allocation

**Goal:** assign vessels to compatible berths and service windows while minimizing total waiting time.

The first illustrative instance will target two vessels, two berths, and two time windows, with fixed service durations and explicitly stated compatibility assumptions. Additional instances can expand the horizon and the number of vessels.

The exercise will guide users through:

1. Defining arrival times, berth availability, compatibility, and service duration.
2. Representing assignment decisions with binary variables.
3. Enforcing one assignment per vessel and preventing berth conflicts.
4. Establishing a classical reference using exhaustive enumeration for tiny instances and CP-SAT where appropriate.
5. Building a QUBO and checking that its penalties represent the intended constraints.
6. Mapping the QUBO to an Ising cost Hamiltonian.
7. Running QAOA with Ket/KBW and evaluating decoded samples.

**Expected visualization:** a berth occupancy timeline showing vessel assignments, service windows, and waiting time.

**Scope:** an educational discrete BAP. Navigation-channel coordination, tides, draft restrictions, and detailed terminal operating rules are outside the first version.

### Exercise 02 — Quay Crane Allocation

**Goal:** allocate limited crane capacity to vessel service demand over a short planning horizon.

The first illustrative instance will target two vessels, two cranes, and two periods. The initial version will use a predefined vessel service schedule and run independently of Exercise 01.

The exercise will guide users through:

1. Specifying service demand, crane availability, and simplified productivity.
2. Enforcing that a crane cannot serve multiple vessels simultaneously.
3. Modeling capacity limits and unmet-demand penalties.
4. Comparing a classical reference with a validated QUBO formulation.
5. Exploring QAOA with Ket/KBW and the effect of penalty choices on feasibility.

**Expected visualization:** a crane-to-vessel allocation timeline, together with utilization and demand coverage indicators.

**Scope:** simplified quay crane allocation. Crane travel, interference, non-crossing constraints, and detailed task sequencing are outside the first version. This exercise does not represent a complete Quay Crane Scheduling Problem (QCSP).

### Exercise 03 — Disruption and Replanning

**Goal:** understand the trade-off between improving operational performance and preserving an existing schedule after a disruption.

This exercise will reuse the berth allocation model and introduce controlled changes, such as a delayed vessel arrival or a temporarily unavailable berth.

Users will compare three responses:

| Response | Decision rule |
| --- | --- |
| **Evaluate the original plan** | Check whether it remains feasible under the changed conditions and measure its performance when feasible. |
| **Reoptimize the schedule** | Compute a new plan for the updated scenario, subject to any explicitly fixed commitments. |
| **Limit schedule changes** | Penalize reassignment or time changes while optimizing the updated plan. |

The initial implementation will use explicit scenario rules and classical references. Quantum experiments can follow once the updated formulations have been validated. A later AI assistant may translate a request such as “Vessel A arrives two hours late” into a structured scenario update for review and execution.

**Expected visualization:** original and revised berth schedules, accompanied by changes in waiting time, assignment stability, and feasibility.

**Scope:** controlled, offline scenario analysis. Live terminal integration and autonomous operational decisions are outside the initial scope.

## A common experimental workflow

Each exercise will follow the same sequence:

1. **Describe** the operational decision, assumptions, units, and input data.
2. **Model** the objective and constraints explicitly.
3. **Solve classically** to obtain a reference and record the solver status.
4. **Validate the formulation**, including QUBO penalty behavior on small instances.
5. **Experiment quantumly**, when applicable, using Ket/KBW.
6. **Validate and compare** decoded solutions using the original operational constraints.
7. **Explain** the result, trade-offs, and limitations.

For small instances, exhaustive enumeration will help verify that the QUBO and the original constrained model agree on optimal feasible solutions when penalties are chosen appropriately. Reports will distinguish the operational objective from the penalized QUBO energy, including any constant offsets in Hamiltonian comparisons.

## Evaluation and reproducibility

Planned reports will record:

- Instance identifier, data provenance, assumptions, and units.
- Solver status, best feasible objective, and reference optimum when known.
- Constraint violations and the fraction of feasible sampled solutions.
- Empirical frequency of obtaining an optimal solution, when an optimum is known.
- Number of binary variables, qubits, algorithm layers, and circuit depth where available.
- Penalty weights, parameter initialization, random seeds, and sampling settings.
- End-to-end runtime, with classical parameter optimization and simulation costs identified.
- Dependency versions and execution environment.

An optimum will only be reported when established by exhaustive evaluation or an appropriate solver certificate/status. A feasible solution will not be labeled optimal without supporting evidence. Cross-method runtime comparisons will state the execution conditions and measurement boundaries.

## Planned repository organization

The following layout is proposed for the implementation phase. These directories may not yet exist.

| Path | Intended content |
| --- | --- |
| `notebooks/` | Guided exercises, with Google Colab entry points once executable notebooks are published. |
| `src/` | Shared modeling, solver adapter, validation, and reporting functions. |
| `data/synthetic/` | Documented synthetic instances and instance-generation settings. |
| `results/` | Reference outputs and experiment configurations. |
| `tests/` | Checks of feasibility, objective calculations, and formulation equivalence. |
| `docs/` | Problem descriptions, methodology, and contribution guidance. |

## Getting started

At this stage, start with the exercise descriptions above. Installation instructions, tested dependency versions, runnable notebook links, and reference outputs will be added with the first executable release.

The first planned milestone is **v0.1.0: a complete, reproducible Berth Allocation exercise**. Quay Crane Allocation and Disruption and Replanning will follow incrementally. QAOA is the initial quantum algorithm; FALQON is a potential later extension.

## Contributing

Contributions are welcome in problem modeling, synthetic instances, independent validation, visualization, documentation, and reproducible experiments.

Please open an issue to describe a proposed change before undertaking substantial work. For bug reports, include the relevant instance, environment, configuration, expected behavior, and observed result.

Use only material you are authorized to share. Synthetic or openly licensed data with documented provenance is preferred for public examples. Operational data supplied by partners requires explicit authorization for publication.

## About HYPAQ

HYPAQ develops Optimization Intelligence with an **AI-First, Quantum-Ready** approach. HYPAQ Ports is its public application laboratory for port-related optimization, complementing research in distributed quantum computing and network-sensitive assessment of quantum workloads.

Related public research repositories:

- [HYPAQ DQC](https://github.com/hypaq/hypaq-dqc) — hypergraph partitioning for static and adaptive quantum circuits.
- [HYPAQ DVS](https://github.com/hypaq/hypaq-dvs) — Distributed Viability Score and related research materials.

## Technology references

- [Ket Quantum Programming](https://quantumket.org/) — Python-based quantum programming and the KBW simulator.
- [Ket Programming Guide](https://quantumket.org/guide/index.html) — processes, Hamiltonians, and quantum algorithm examples.
- [OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver) — classical constraint optimization and solver status definitions.

## License

Unless explicitly stated otherwise, repository content is licensed under the **[Apache License 2.0](LICENSE)**. Third-party materials and dependencies retain their respective licenses. Any separately licensed datasets will identify their terms explicitly.

The software license does not grant general permission to use HYPAQ trademarks or imply endorsement by HYPAQ or by the developers of referenced technologies.
