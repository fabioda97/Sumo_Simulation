import os
import re
import sys
import xml.etree.ElementTree as ET
import subprocess
from calendar import month
from datetime import datetime
from re import match
import shutil

import pandas as pd
from libraries.classes.SumoSimulator import Simulator

class ScenarioGenerator:
    '''
    Questa Classe gestisce gli scenari delle traffic route: genera i file delle route per SUMOENV, configura e imposta
    gli scenari per la simulazione

    Attributi della classe:
    sumoConfiguration (str) --> Path del file di configurazione di SUMOENV
    sim (Simulator) --> istanza della classe Simulator (libraries -> classes -> SumoSimulator) che gestisce la simulazione

    Metodi della classe:
    __init__ --> Costruttore, inizializza un'istanza della classe ScenarioGenerator
    generateRoutes --> crea un file di route per la simulazione partendo da un edgefile (file che definisce le strade della rete)
    setScenario --> imposta lo scenario di simulazione (file di route preso automaticamente o caricato manualmente)
    '''
    sumoConfiguration: str
    sim: Simulator

    def __init__(self, sumocfg: str, sim: Simulator):

        self.sumoConfiguration = sumocfg
        self.sim = sim


    #ATTENZIONE: Controllare questa funzione!!!!!!
    def defineScenarioFolder(self, congestioned: bool = False) -> str:

        date= datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        scenarioFolder = "congestioned" if congestioned else "basic"
        newPath = os.path.join("configs/scenarioCollection", f"{date}_{scenarioFolder}")
        os.makedirs(newPath, exist_ok=True)
        return newPath

    def generateRoutes(self, edgefile: str, folderPath: str, totalVehicles: int, minLoops: int = 1,
                       congestioned: bool = False) -> str:
        '''
                Genera un route file (.rou.xml) per sumoenv utilizzando edgefile dato in ingresso

                :param edgefile: path dell'edge file che contiene il conteggio dei veicoli sulle varie strade
                :param folderPath:
                :param totalVehicles: numero totale di veicoli da inserire nel route file
                :param minLoops: numero minimo di loops o punti di conteggio che ogni veicolo deve attraversare
                :param congestioned:Flag che indica se lo scenario deve essere congestionato
                :return: percorso assoluto del route file generato
                '''

        # percorso ai tool di SUMO dove si trovano gli script Py come randomTrip.py
        sumo_tools_path = r"C:\Program Files (x86)\Eclipse\Sumo\tools"

        # percorso relativo della rete SUMO
        sumo_path = "configs/"

        # controllo sui parametri di input: verifica l'esistenza dell'edgefile, totalVehicle non nullo, path dei tool SUMO esistente
        if not edgefile:
            raise ValueError("No edge file provided.")
        if totalVehicles is None:
            raise ValueError("The total number of vehicles was not defined.")
        if not os.path.exists(sumo_tools_path):
            raise FileNotFoundError("sumoenv tools path does not exist.")

        # path assoluto allo script randomTrip.py di SUMO
        script1 = sumo_tools_path + "/randomTrips.py"

        # path assoluto al file joined_lanes.net.xml, che rappresenta la rete di SUMO
        arg1 = ""
        if sumo_path.startswith("./"):
            arg1 = sumo_path[2:]
        else:
            arg1 = sumo_path
        arg1 = os.path.join(sumo_path, "joined_lanes.net.xml")
        arg1 = os.path.abspath(arg1)
        print(arg1)
        print(edgefile)

        # esegue lo script di SUMO randomTrips.py, per generare delle route casuali per la simulazione
        '''
        randomTrips.py --> crea percorsi casuali sulla rete SUMO
        -n arg1 --> Specifica il file della rete joined_lanes.net.xml
        -"-r", folderPath + "sampleRoutes.rou.xml" --> salva il file di output
        -- random --> genera percorsi randomici
        --min-distance 100 --> imposta una distanza minima di 100 metri tra origine e destinazione
        --random-factor 200 --> Aumenta la casualità nella generazione delle rotte
        '''

        # Path dove verrà salvato il file finale .rou.xml delle route generate
        route_file_path = os.path.join(folderPath, "generatedRoutes.rou.xml")

        # ATTENZIONE: il commento sotto serve a generare delle rotte casuale!!!!!!

        subprocess.run(
            ['python', script1, "-n", arg1, "-r", folderPath + "sampleRoutes.rou.xml", "--fringe-factor", "10",
             "--random",
             "--min-distance", "100", "--random-factor", "200"])

        # esegue lo script di SUMO routeSampler.py, per generare le route in base ai dati reali per la simulazione
        script2 = sumo_tools_path + "/routeSampler.py"
        if congestioned:

            subprocess.run([sys.executable, script2, "-r", folderPath + "sampleRoutes.rou.xml", "--edgedata-files",
                            edgefile, "-o", route_file_path, "--total-count",
                            str(totalVehicles), "--optimize", "full", "--min-count", str(minLoops)])

        else:
            subprocess.run([sys.executable, script2, "-r", folderPath + "sampleRoutes.rou.xml", "--edgedata-files",
                            edgefile, "-o", route_file_path, "--total-count",
                            str(totalVehicles), "--optimize", "full", "--min-count", str(minLoops)])

        print("Routes Generated")

        relativeRouteFile = folderPath
        routeFilePath = os.path.abspath(relativeRouteFile)
        return routeFilePath

    def setScenario(self, routeFilePath=None, absolutePath: bool = False):

        if not absolutePath:
            routeFilePath = os.path.abspath(routeFilePath)
        if not os.path.exists(routeFilePath):
            raise FileNotFoundError(f"The route file '{routeFilePath}' does not exist.")
        self.sim.changeRoutePath(routePath=routeFilePath)

class Planner:

    simulator: Simulator
    scenarioGenerator: ScenarioGenerator

    def __init__(self, simulator: Simulator):

        self.simulator = simulator
        self.scenarioGenerator = ScenarioGenerator(sumocfg="run.sumocfg",sim=self.simulator)

    def generateRoutesFilesForAllHours(self, baseFolder: str, totalVehicles:int, minLoops:int, congestioned: bool, activeGui: bool):
        '''
        Genera un file 'generatedRoutes.rou.xml' per ogni 'edgedata_dd-mm-yyyy' nella cartella baseFolder

        :param baseFolder: Cartella con tutti i file 'edgedata_*.xml
        :param totalVhicles:numero totale di veicoli per ogni ora (ogni simulazione)
        :param minLoop: Numero minimo di loops per veicolo
        :param congestionated: flag per generare traffico congestionato
        :return:
        '''

        #Legge la lista dei file 'edgedata_*.xml' nella cartella
        file_list = sorted(os.listdir(baseFolder)) #ordina tutti i file nella cartella
        file_pattern = re.compile(r"edgedata_(\d{2})-(\d{2})-(\d{4})_(\d{2})\.xml") #espressione che identifica i file con nome tipo 'edgedata_gg-mm-aaaa_hh.xml'

        #itera su ogni file nella cartella e controlla se il nome corrisponde al pattern
        for file_name in file_list:
            match=file_pattern.match(file_name)
            if match:
                day, month, year, hour = match.groups() #estrae giorno, mese, anno e ora dal nome del file
                timestamp = f"{day}-{month}-{year}_{hour}-00" #stringa che sarà il nome della sottocartella dello scenario

                #creazione sottocartella per la simulazione per l'ora considerata
                scenarioFolder = os.path.join("configs/scenarioCollection", f"{timestamp}")
                os.makedirs(scenarioFolder, exist_ok=True)

                #percorso del file edgedata.xml corrente
                edgedata_path = os.path.join(baseFolder, file_name)
                shutil.copy(edgedata_path,scenarioFolder) #copia l'edgefile_*.xml nella cartella dello scenario


                #generazione del Route file, usando la funzione generateRoute()
                routeFilePath = self.scenarioGenerator.generateRoutes(
                    edgefile=edgedata_path,
                    folderPath = scenarioFolder,
                    totalVehicles=totalVehicles,
                    minLoops=minLoops,
                    congestioned=congestioned
                )

                print(f"Route file generato: {routeFilePath}")
                self.scenarioGenerator.setScenario(routeFilePath=scenarioFolder, absolutePath=False)
                logFilePath = os.path.join(scenarioFolder, "sumo_log.txt")
                self.simulator.start(activeGui=activeGui, logFilePath=logFilePath)

        print("\n Tutti i file sono stati creati cin successo")


