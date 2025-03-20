import traci
import os
from libraries.utils import preprocessingUtils1
from libraries.classes.Planner1 import *
from libraries.classes.SumoSimulator import Simulator
import xml.etree.ElementTree as ET


from configs import *
from data import *

preprocessingUtils1.fillMissingEdgeId("data/road_names.csv")
preprocessingUtils1.filterWithAccuracy("data/traffic_flow_2024.csv", "data/accuracy_loops_2024.csv", 'data', 'codice_spira', "data/accurate_traffic_flow.csv", 90)

preprocessingUtils1.generateRealFlow("data/accurate_traffic_flow.csv", "data/real_traffic_flow.csv")
preprocessingUtils1.generateRoadNamesFile("data/accurate_traffic_flow.csv", "configs/joined_lanes.net.xml", "configs/detectors.add.xml", "data/road_names.csv")

#preprocessingUtils1.linkEdgeID("data/accurate_traffic_flow.csv", "data/road_names.csv", "data/processed_traffic_flow.csv")
preprocessingUtils1.generateEdgeDataFile("data/processed_traffic_flow.csv", "configs/edgedata.xml", date='01/02/2024', time_slot='07:00-08:00')
preprocessingUtils1.dailyFilter("data/processed_traffic_flow.csv", "01/02/2024")


edgedataPath = "C:/Users/fabio/Desktop/Sumo_Simulation/configs/edgedata.xml"
tree = ET.parse(edgedataPath)
root = tree.getroot()
data = []
for interval in root.findall("interval"):
    for edge in interval.findall("edge"):
        edge_id = edge.get("id")
        entered = int(edge.get("entered"))
        data.append({"edgeid": edge_id, "trafficFlow": entered})

collectedData = pd.DataFrame(data)
if collectedData.empty:
    raise ValueError("Il DataFrame generato da edgefile.xml è vuoto! Controlla il contenuto del file.")


#creo istanza del simulatore SUMO
simulator = Simulator(configurationPath="configs", logFile="sumo_log.txt")


#creo istanza Planner, che gestisce la simulazione
planner = Planner1(simulator=simulator)

entityType = "roadsegment"
totalVehicles = 500  # Numero totale di veicoli nella simulazione
minLoops = 2  # Numero minimo di loops o punti di conteggio attraversati dai veicoli
congestioned = True  # Cambia a True per simulare traffico congestionato
activeGui = True  # Se True, avvia SUMO con interfaccia grafica

scenario_folder = planner.planBasicScenarioForOneHourSlot(
    collectedData=collectedData,
    entityType=entityType,
    totalVehicles=totalVehicles,
    minLoops=minLoops,
    congestioned=congestioned,
    activeGui=activeGui
)
#Avvia SUMO prima di creare il simulatore
#sumo_binary = "sumo-gui"  # Cambia in "sumo" se non vuoi GUI
#sumo_binary = "sumo"
#sumo_config = os.path.abspath("configs/run.sumocfg")

#traci.start([sumo_binary, "-c", sumo_config])


#logFile="./command_log.txt"
#sumoSimulator = Simulator(configurationPath="configs", logFile=logFile)
#planner = Planner(simulator=sumoSimulator)



print("Esecuzione Completata")