# Scenario 0

No services are spawned, all the hosts are in the same slice and they can ping each other. This scenario tests the network topology and the two-level routing mechanism. 

## Known Issues

- Mininet `pingall` command does not work, although all the hosts can ping each other using the typical `ping` command.

# Parameters

```python
# network/globals.py
FAT_TREE_K = 4

slices = {
    0: [
        '10.0.0.2', '10.0.0.3', '10.0.1.2', '10.0.1.3', 
        '10.1.0.2', '10.1.0.3', '10.1.1.2', '10.1.1.3', 
        '10.2.0.2', '10.2.0.3', '10.2.1.2', '10.2.1.3', 
        '10.3.0.2', '10.3.0.3', '10.3.1.2', '10.3.1.3',
    ],
}

clients = [ ]

services = { }
```

# Mininet Output

Execution of `ping` between different hosts shows the correct connectivity, for instance:

```
mininet> p0_s1_h2 ping p3_s0_h3
PING 10.3.0.3 (10.3.0.3): 56 data bytes
64 bytes from 10.3.0.3: seq=4 ttl=64 time=0.748 ms
64 bytes from 10.3.0.3: seq=5 ttl=64 time=0.071 ms
64 bytes from 10.3.0.3: seq=6 ttl=64 time=0.131 ms
64 bytes from 10.3.0.3: seq=7 ttl=64 time=0.077 ms
```

# Controller Output

No interesting output is shown on the controller console, but it possible to see the ICMP flows in the core switch port statistics:

```
=============== Core Switch Port Statistics ===============
c11 :
         Port 1: [ TX: 980      RX: 0 ]
         Port 2: [ TX: 0        RX: 0 ]
         Port 3: [ TX: 0        RX: 0 ]
         Port 4: [ TX: 0        RX: 980 ]
c21 :
         Port 1: [ TX: 0        RX: 0 ]
         Port 2: [ TX: 0        RX: 0 ]
         Port 3: [ TX: 0        RX: 0 ]
         Port 4: [ TX: 0        RX: 0 ]
c22 :
         Port 1: [ TX: 0        RX: 0 ]
         Port 2: [ TX: 0        RX: 0 ]
         Port 3: [ TX: 0        RX: 0 ]
         Port 4: [ TX: 0        RX: 0 ]
c12 :
         Port 1: [ TX: 0        RX: 980 ]
         Port 2: [ TX: 0        RX: 0 ]
         Port 3: [ TX: 0        RX: 0 ]
         Port 4: [ TX: 980      RX: 0 ]
=============== =========================== ===============
```