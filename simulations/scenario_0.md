# Scenario 0

No services are spawned, all the hosts are in the same slice and they can ping each other. This scenario tests the network topology and the two-level routing mechanism. 

# Parameters

```python
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

# Controller Output