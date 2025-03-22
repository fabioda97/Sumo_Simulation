from libraries.classes.Planner import *
from data import preprocessingSetup

"""
Script principale del progetto Sumo_Simulation, punto di ingresso per eseguire simulazioni giornaliere complete.

Esegue in sequenza tutte le operazioni necessarie per lanciare una simulazione SUMO:
1. Preprocessing dei dati reali (open data di Bologna)
2. Creazione e configurazione del simulatore SUMO
3. Inizializzazione del Planner per la generazione degli scenari di traffico
4. Generazione dei file di rotta (routes) per ogni ora del giorno
5. Avvio delle simulazioni 

"""

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