# Sumo_Simulation Project [In Progress]

Questo progetto si concentra sulla componente simulativa (SUMO) della repository [**BoMoDT**](https://github.com/alessandrasomma28/BoMoDT.git), con l'obiettivo di generare e collezionare dati, a partire da simulazioni di scenari di traffico realistici della durata di un mese.

Per effettuare le simulazioni con SUMO, vengono utilizzati i dati open source forniti dalla città di Bologna. Dopo alcune operazioni di preprocessing, questi dati vengono convertiti in input per il simulatore, che esegue 24 simulazioni giornaliere (una per ogni ora) per 30 giorni consecutivi.

> [In Progress]
> Oltre agli scenari di traffico realistici, sono previste simulazioni di scenari maliziosi, in cui viene contemplata la presenza di attacchi informatici. L'obiettivo è raccogliere una grande mole > di dati da utilizzare per addestrare algoritmi di machine learning e deep learning, in grado di riconoscere automaticamente la presenza di cyber attack durante le simulazioni.

## Sumo_Simulation Repository Structure
```plaintext

├── Sumo_Simulation
|    ├── Configs
|    |    ├── ScenarioCollection                           #Contiene le cartelle con gli output e l'EdgeData di ogni simulazione (una simulazione per ogni ora).
|    |    |    ├── dd-mm-YYYY_hh-mm                        #Cartella con gli output e l'edgeData della singola simulazione.Rinominata con il giorno, il mese, l'anno e l'ora dei dati di traffico utilizzati per la simulazione
|    |    |    |    ├── edgedata_dd-mm-YYYY_hh.xml         #SUMO input - Contiene i conteggi del traffico sulle strade per la simulazione corrente (generato nel preprocessingUtils.py)
|    |    |    |    ├── generatedRoutes.rou.xml            #SUMO input - Contiene i percorsi dei veicoli per la simulazione corrente basato su dati reali (generato nel Planner)
|    |    |    |    ├── fcd.xml                            #SUMO output - contiene valori relativi a posizione, velocità, accelerazione di ogni veicolo a ogni time-step
|    |    |    |    ├── queue.xml                          #SUMO output - Contiene info sul traffico (numero di veicoli in coda su ogni lane) ad ogni time-stamp
|    |    |    |    ├── tripinfos.xml                      #SUMO output - Riassunto sui dati di viaggio di ogni veicolo (ad es. Orario di partenza e arrivo, velocità media, tempo di viaggio totale, ecc.)
|    |    |    |    ├── vehroute.xml                       #SUMO output - Elenco degli edge attraversati effettivamente da ogni veicolo nella simulazione
|    |    |    |    └── sumo_log.txt                       #SUMO output - fileLog con le chiamate TRACI fatte dallo script SumoSimulator.py al simulatore
|    |    |    |
|    |    |    └── dd-mm-YYYY_hh-mmsampleRoutes.rou.xml    #Contiene i percorsi randomici (non basato su dati reali) dei veicoli per la simulazione indicata
|    |    |
|    |    ├── TestData_UnMese                              #Folder che contiene tutti gli EdgeData utili alle simulazioni (gli stessi di quelli presenti in ScenarioCollection) 
|    |    |    └── edgedata_dd-mm-YYYY_hh.xml              
|    |    |
|    |    ├── detectors.add.xml                            #SUMO input - Contiene la posizione e l'ID delle spire nella rete SUMO
|    |    ├── e1_real_output.xml                           #SUMO output - contiene i dati raccolti dai sensori durante la simulazione
|    |    ├── joined_lanes.net.xml                         #SUMO input - Definisce la rete SUMO
|    |    ├── joined_tls.add.xml                           #SUMO input - Contiene la logica dei semafori
|    |    ├── joined_vtypes.add.xml                        #SUMO input - Contiene i tipi e le caratteristiche dei veicoli per le simulazioni
|    |    └── run.sumocfg                                  #Configurazione di SUMO nel quale vengono definiti i file di I/O 
|    |
|    |
|    ├── data
|    |    ├── accuracy_loops_2024.csv                      #dataset con le percentuali di accuratezza delle misurazioni del traffico
|    |    ├── accurate_traffic_flow.csv                    #dataset risultato del filtraggio, contiene solo i dati del traffico con accuratezza >= 95%
|    |    ├── processed_traffic_flow.csv                   #dataset finale con i dati di traffico filtrati in base all'accuratezza e associazione con gli EdgeID della rete SUMO
|    |    ├── road_names.csv                               #dataset contente l'associazione tra nome delle strada, coordinate GPS e EdgeID associato alla rete SUMO
|    |    ├── traffic_flow_2024.csv                        #dataset delle misurazioni del traffico ottenute dalle spire da Gennaio 2024 ad Aprile 2024
|    |    └── preprocessingSetup.py                        #script con le chiamate alle funzioni utili al processamento dei dati definite in preprocessingUtils.py. Viene chiamato nel main.py
|    |
|    |
|    ├── libraries
|    |    ├── classes
|    |    |    ├── Planner.py                              #Genera gli scenari basati sui dati del traffico, chiama SumoSimulation per avviare le simulazioni
|    |    |    └── SumoSimulator.py                        #Avvia SUMO con le configurazioni impostate
|    |    |
|    |    └── utils
|    |        └── preprocessingUtils.py                    #Contiene funzioni per processare dati, il fine ultimo è la genarazione di edgedata.xml (utile al Planner per generare gli scenari)
|    |
|    |
|    ├── main.py                                           #script che avvia tutta la pipeline di simulazione: preprocessing, configurazione, generazione scenari e avvio delle simulazioni SUMO.
|    └── README.md
```
