from libraries.classes.Planner import *
from data import preprocessingSetup


preprocessingSetup.run() #Richiama le funzioni utili al preprocessing del Dataset

# Definisco la cartella con gli edgedata.xml
baseFolder = "configs/test"
#creo istanza del simulatore SUMO
simulator = Simulator(configurationPath="configs", logFile="sumo_log.txt")


#creo istanza Planner, che gestisce la simulazione
planner = Planner(simulator=simulator)


totalVehicles = 500  # Numero totale di veicoli nella simulazione
minLoops = 2  # Numero minimo di loops o punti di conteggio attraversati dai veicoli
congestioned = True  # Cambia a True per simulare traffico congestionato
activeGui = False  # Se True, avvia SUMO con interfaccia grafica

scenario_folder = planner.generateRoutesFilesForAllHours(
    baseFolder=baseFolder,
    totalVehicles=100,
    minLoops=2,
    congestioned=False,
    activeGui=False

    )

print("Esecuzione Completata")