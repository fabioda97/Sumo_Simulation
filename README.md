# Sumo_Simulation Project

## Sumo_Simulation Repository Structure
```plaintext

├── Sumo_Simulation
|    ├── Configs
|    |    ├── ScenarioCollection 
|    |    |    ├── dd-mm-YYYY_hh-mm
|    |    |    |    ├── edgedata_dd-mm-YYYY_hh.xml
|    |    |    |    ├── fcd.xml
|    |    |    |    ├── generatedRoutes.rou.xml
|    |    |    |    ├── queue.xml
|    |    |    |    ├── tripinfos.xml
|    |    |    |    └── vehroute.xml
|    |    |    |
|    |    |    └── dd-mm-YYYY_hh-mmsampleRoutes.rou.xml
|    |    |
|    |    ├── TestData_UnMese
|    |    |    └── edgedata_dd-mm-YYYY_hh.xml
|    |    |
|    |    ├── detectors.add.xml
|    |    ├── e1_real_output.xml
|    |    ├── joined_lanes.net.xml
|    |    ├── joined_tls.add.xml
|    |    ├── joined_vtypes.add.xml
|    |    └── run.sumocfg
|    |
|    |
|    ├── data
|    |    ├── accuracy_loops_2024.csv
|    |    ├── accurate_traffic_flow.csv
|    |    ├── processed_traffic_flow.csv
|    |    ├── real_traffic_flow.csv
|    |    ├── road_names.csv
|    |    ├── traffic_flow_2024.csv
|    |    └── preprocessingSetup.py
|    |
|    |
|    ├── libraries
|    |    ├── classes
|    |    |    ├── Planner.py
|    |    |    └── SumoSimulator.py
|    |    |
|    |    └── utils
|    |        └── preprocessingUtils.py
|    |
|    |
|    ├── main.py
|    └── README.md
```
