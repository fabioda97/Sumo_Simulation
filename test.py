'''
TESTING PER PROVE... !!!
'''

import os
from libraries.classes.SumoSimulator import Simulator
from libraries.classes.Planner import Planner

# Inizializza il simulatore
#simulator = Simulator()

# Crea un'istanza di Planner
planner = Planner()

# Definisce la cartella con gli edgedata.xml
baseFolder = "configs/prova"

# Testa la generazione dei file `generatedRoutes.rou.xml` senza eseguire SUMO
print(" Avvio test: generazione dei file di route...")

planner.generateRouteFilesForAllHours(
    baseFolder=baseFolder,
    totalVehicles=500,
    minLoops=2,
    congestioned=False
)

print("Test completato: verifica i file `generatedRoutes.rou.xml` nelle cartelle di scenario!")