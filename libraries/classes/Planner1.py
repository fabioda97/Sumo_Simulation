import os
import sys
import xml.etree.ElementTree as ET
import subprocess
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from datetime import datetime

import pandas as pd
#from contributed.sumopy.agilepy.lib_base.xmlman import begin
#from output.generateITetrisNetworkMetrics import interval

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

    def defineScenarioFolder(self, congestioned: bool = False) -> str:

        date= datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        scenarioFolder = "congestioned" if congestioned else "basic"
        newPath = os.path.join("configs/scenarioCollection", f"{date}_{scenarioFolder}")
        os.makedirs(newPath, exist_ok=True)
        return newPath

    def generateRoutes(self, edgefile: str, folderPath: str, totalVehicles: int, minLoops: int = 1, congestioned: bool= False) -> str:
        '''
                Genera un route file (.rou.xml) per sumoenv utilizzando edgefile dato in ingresso

                :param edgefile: path dell'edge file che contiene il conteggio dei veicoli sulle varie strade
                :param folderPath:
                :param totalVehicles: numero totale di veicoli da inserire nel route file
                :param minLoops: numero minimo di loops o punti di conteggio che ogni veicolo deve attraversare
                :param congestioned:Flag che indica se lo scenario deve essere congestionato
                :return: percorso assoluto del route file generato
                '''

        sumo_tools_path = r"C:\Program Files (x86)\Eclipse\Sumo\tools"
        sumo_path = "configs/"

        #sumo_path = os.path.abspath("configs/")


        # controllo sui parametri di input
        if not edgefile:
            raise ValueError("No edge file provided.")
        if totalVehicles is None:
            raise ValueError("The total number of vehicles was not defined.")

        if not os.path.exists(sumo_tools_path):
            raise FileNotFoundError("sumoenv tools path does not exist.")

        script1 = sumo_tools_path + "/randomTrips.py"
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
        #####
        route_file_path = os.path.join(folderPath, "generatedRoutes.rou.xml")
        ########
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

class Planner1:

    simulator: Simulator
    scenarioGenerator: ScenarioGenerator

    def __init__(self, simulator: Simulator):

        self.simulator = simulator
        self.scenarioGenerator = ScenarioGenerator(sumocfg="run.sumocfg",sim=self.simulator)

    def planBasicScenarioForOneHourSlot(self, collectedData: pd.DataFrame, entityType: str, totalVehicles: int, minLoops: int, congestioned: bool, activeGui: bool=False):

        if entityType.lower() not in ["road segment", "roadsegment"]:
            raise ValueError(f"Invalid entity type: {entityType}. Simulation requires edge IDs to generate a scenario.")

        root = ET.Element('data')
        interval = ET.SubElement(root, 'interval', begin='0', end='3600')
        scenarioFolder = self.scenarioGenerator.defineScenarioFolder(congestioned=congestioned)
        for _, row in collectedData.iterrows():
            edgeID = row.get('edgeid')
            trafficFlow = row.get('trafficFlow')
            if edgeID is None:
                raise ValueError("Edge ID is missing for one of the rows in the collected data.")
            ET.SubElement(interval, 'edge', id=edgeID, entered=str(trafficFlow))


        tree = ET.ElementTree(root)
        ET.indent(tree, ' ')
        edgeFilePath = os.path.join(scenarioFolder, "edgefile.xml")
        tree.write(edgeFilePath, "UTF-8")
        routeFilePath = self.scenarioGenerator.generateRoutes(edgefile=edgeFilePath, folderPath=scenarioFolder,
                                                              totalVehicles=totalVehicles, minLoops=minLoops,
                                                              congestioned=congestioned)
        self.scenarioGenerator.setScenario(routeFilePath=routeFilePath, absolutePath=True)
        logFilePath = os.path.join(scenarioFolder, "sumo_log.txt")
        self.simulator.start(activeGui=activeGui, logFilePath=logFilePath)

        return scenarioFolder



