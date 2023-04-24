# SDN Slice Setup Optimization

This repository contains the source code for the project of the course Networking II (Softwarized and Virtualized Mobile Networks) at the University of Trento.

Goal of the project is to develop a RYU-based SDN controller to slice the network, dynamically re-allocate services and schedule new routes in order to maintain the desired QoS. The simulation is based on [Mininet](http://mininet.org/), a realistic virtual network running real kernel, switch and application code on a [Comnetsemu](https://git.comnets.net/public-repo/comnetsemu) Virtual Machine.

**Author**: Samuele Pozzani (samuele.pozzani@studenti.unitn.it)

# Topology

Software-defined networking (SDN) technology is a new approach to network architectures that enables efficient network configuration and improves performance and monitoring, mostly oriented to cloud computing. A first important step for this project consists of developing a network topology that simulates a real-world scenario in a modern data center.

The class contained in `network/topology.py` implements a special instance of a Clos topology called *Fat-Tree* to interconnect commodity ethernet switches, as described in the research article [*"A scalable, commodity data center network architecture"* (Mohammad Al-Fares et al., 2008)](https://dl.acm.org/doi/10.1145/1402946.1402967). The topology is described by a single parameter $K$ (number of pods, and ports of the switches). An instance of this architecture that employs 48-port Ethernet switches is capable of providing full bandwidth to up 27,648 hosts. The following image shows the first non-trivial Fat-Tree instance (with $K = 4$) used for the simulations in this project.

<img src="./docs/imgs/fattree.png" /> 

IP addresses of edge and aggregation switches are `10.pod.switch.1` where switches are numbered left to right and bottom to top. Core switches IP addresses are `10.k.j.i` where $K$ is the topology parameter, $j$ and $i$ denote the coordinates of the switch in the $(k/2)^2$ core switch grid starting from top-left. Servers have IP addresses of the form `10.pod.switch.serverID`.     

# SDN Controller

The SDN Controller is implemented using [RYU SDN Framework](https://ryu-sdn.org/) which provides well defined APIs to manage network switches using the OpenFlow protocol version 1.5.

## Two-Level Routing

To provide level 3 connectivity between all the hosts in the network, RYU is configured to implement the Two-Level Routing mechanism presented in the paper, using FlowTables instead of the classical routing tables. 

## SDN Network Slicing

The first level of switches (edge) act as a filtering traffic diffuser. When the simulation starts, the edge switches are configured to ask the controller for a rule to forward the packets. The controller first checks if the source host is allowed to communicate with the destination based on the slices defined in `network/params.py`. If allowed by the policy, the controller installs a FlowTable entry to the edge switch to forward the packet, otherwise the packet is dropped. 

## Flow Scheduler

The flow scheduler is started by the RYU controller and runs as a separate software thread. Its execution loop includes the following stages:

- Send OpenFlow port stats requests to core switches.
- Analyze port stats replies to estimate the presence of data flows running through the core switches. Then update the TTL field for the detected flows.
- Discover congested downlinks: more than one flows are using the same link from a core switch to a pod.
- Find available downlinks and update the FlowTable on the pod switches to move the traffic through an unused path.
- In case an unused path cannot be found because all the links to the pod are congested, migrate a destination service to another available host, update the network slices and the FlowTable on the pod switches to leverage an unused path.

## Flow Estimation

Goal of this project is to build a Proof of Concept for the SDN technology to work for network optimization. Hence flow estimation has been implemented in a very simple form to set the context and test the controller features. A flow is detected when more data than a certain threshold is forwarded by a core switch in a given amount of time. The flow is defined by that core switch, the source pod and the destination pod (there is no distinction between different hosts generating traffic from the same pod). A downlink is considered congested when more than one flow has the same destination through the same core switch.

More sophisticated flow estimation techniques should consider the type of traffic (used protocols) the source and destination hosts, the duration, the congestion on links inside the pods, and also perform probabilistic analysis on network traffic. An implementation is described in the paper [*"Hedera: Dynamic Flow Scheduling for Data Center Networks"* (Mohammad Al-Fares et al., 2010)](https://dl.acm.org/doi/10.5555/1855711.1855730).   

# Simulations

In the folder `simulations`, there is a series of markdown files which describe all the simulations/experiments that have been executed to test this project, including the used parameters and the outputs from Mininet and the controller.

# Future Work

Some different features, improvements, adaptations, tests and experiments have been left for the future, they include:

- Implement a dynamic flow scheduling with a more sophisticated flow/traffic estimation mechanism, like Hedera.
- Develop more complex services that also require a state to be saved and migrated through the network.
- Implement fault tolerance using a protocol like Bidirectional Forwarding Detection (BFD), then test the network after the deactivation of one or more links.  

# Getting Started 

Add repo to pythonpath env using: 
```bash
$ export PYTHONPATH=/path/to/repo
```  

Move to `services` folder and build the dockerfiles using: 
```bash
$ docker build -t service_migration --file ./Dockerfile.service_migration .   
$ docker build -t dev_test --file ./Dockerfile.dev_test .
```  

To run the simulation, first of all set the global parameters in `network/globals.py`

Then, run Ryu controller using: 
```bash
$ ryu run network/controller.py
```  

Create the network topology and start the mininet simulation using:
```bash
$ sudo python3 mininet_simulation.py
```

To clean the environment and kill the Docker containers run:

```bash
$ docker rm -f $(docker ps -a -q)
$ sudo mn -c   
```  

# Acknowledgments

<a href="https://www.unitn.it/"><img src="./docs/imgs/unitn-logo.jpg" width="300px"></a>

## Doxygen docs

To generate Doxygen documentation, install Doxygen and execute:  

```bash
$ doxygen Doxyfile
``` 

HTML docs will be generated inside the `docs` folder.

## Copyright

MIT License or otherwise specified. See [license](./LICENSE.txt) file for details.