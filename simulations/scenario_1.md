# Scenario 1

Two services are spawned in pod 0 and two clients are in pod 1 and 2 respectively. This setup creates two initial flows running through the core switch c11 to pod 0, therefore the downlink becomes congested. The flow scheduler detects the congestion and moves the communication between 10.0.0.2 and 10.1.0.2 to a new available pathm through core switch c21. 

## Known Issues

None

# Parameters

```python
# network/globals.py
FAT_TREE_K = 4

slices = {
    0: ['10.0.0.2', '10.2.0.2', '10.1.0.2', '10.0.1.2',],
    1: ['10.3.0.2', '10.1.1.2',],
    2: ['10.0.1.3', '10.2.1.2', '10.1.1.3'],
}

clients = [
    ('c1', 'p1_s0_h2', '0'),
    ('c2', 'p2_s0_h2', '1'),
]

services = {
    '0': '10.0.0.2',
    '1': '10.0.1.2',
}
```

# Mininet Output

The only information shown in the mininet console regards the initial creation of the two services. 

```
Created service on host 10.0.0.2
Created service on host 10.0.1.2
```

# Controller Output

```
Flow on switch c11 from pod 1 to pod 0
Flow on switch c11 from pod 2 to pod 0
Flow on switch c11 from pod 0 to pod 1
Flow on switch c22 from pod 0 to pod 2
Discovered congested downlink on c11 to pod 0

=============== Core Switch Port Statistics ===============
c11 :
         Port 1: [ TX: 8854     RX: 8586 ]
         Port 2: [ TX: 8586     RX: 4462 ]
         Port 3: [ TX: 70       RX: 4462 ]
         Port 4: [ TX: 70       RX: 70 ]
c21 :
         Port 1: [ TX: 70       RX: 70 ]
         Port 2: [ TX: 70       RX: 70 ]
         Port 3: [ TX: 70       RX: 70 ]
         Port 4: [ TX: 70       RX: 70 ]
c12 :
         Port 1: [ TX: 70       RX: 70 ]
         Port 2: [ TX: 70       RX: 70 ]
         Port 3: [ TX: 70       RX: 70 ]
         Port 4: [ TX: 70       RX: 70 ]
c22 :
         Port 1: [ TX: 70       RX: 8586 ]
         Port 2: [ TX: 70       RX: 70 ]
         Port 3: [ TX: 8586     RX: 70 ]
         Port 4: [ TX: 70       RX: 70 ]
=============== =========================== ===============

...

Found available core switch: c21
Create path to 10.0.0.2 via c21

...

Flow on switch c11 from pod 2 to pod 0
Flow on switch c11 from pod 0 to pod 1
Flow on switch c21 from pod 1 to pod 0
Flow on switch c22 from pod 0 to pod 2

=============== Core Switch Port Statistics ===============
c11 :
         Port 1: [ TX: 4470     RX: 9450 ]
         Port 2: [ TX: 9450     RX: 0 ]
         Port 3: [ TX: 0        RX: 4540 ]
         Port 4: [ TX: 0        RX: 70 ]
c21 :
         Port 1: [ TX: 4890     RX: 70 ]
         Port 2: [ TX: 70       RX: 4820 ]
         Port 3: [ TX: 0        RX: 70 ]
         Port 4: [ TX: 0        RX: 0 ]
c12 :
         Port 1: [ TX: 70       RX: 70 ]
         Port 2: [ TX: 70       RX: 0 ]
         Port 3: [ TX: 0        RX: 0 ]
         Port 4: [ TX: 0        RX: 70 ]
c22 :
         Port 1: [ TX: 0        RX: 8508 ]
         Port 2: [ TX: 0        RX: 0 ]
         Port 3: [ TX: 8508     RX: 0 ]
         Port 4: [ TX: 0        RX: 0 ]
=============== =========================== ===============
```
