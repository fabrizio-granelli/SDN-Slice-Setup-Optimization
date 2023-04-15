# OnDemand-SDN-Slices

Add repo to pythonpath using `$ export PYTHONPATH=/path/to/repo`  
Run Ryu controller using `$ ryu run network/controller.py`  
Create topology and run simulation using `$ sudo python3 mininet_simulation.py`   
Delete mininet status using `$ sudo mn -c`   
Kill all containers using `$ docker rm -f $(docker ps -a -q)`
Build dockerfile using `$ docker build -t service_migration --file ./Dockerfile .` 
Build dev_test using `$ docker build -t dev_test --file ./Dockerfile.dev_test .`