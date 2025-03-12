import os
import sys
import xml.etree.ElementTree as ET
import pandas as pd
import subprocess
from datetime import datetime
from tkinter import Tk
from tkinter.filedialog import askopenfilename

from contributed.sumopy.agilepy.lib_base.xmlman import begin
from contributed.sumopy.coremodules.simulation.sumo_virtualpop import logfilepath

from libraries import constants
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
        '''

        :param sumocfg: Path del file di configurazione sumoenv
        :param sim: Istanza della calsse Simulator (libraries -> classes -> SumoSimulator)
        '''

        self.sumoConfiguration = sumocfg
        self.sim = sim

    def defineScenarioFolder(self, congestioned: bool = False) -> str:
        '''
        Definisce e crea un Folder per lo scenario che si vuole simulare

        :param congestioned: Flag che indica se lo scenario deve essere congestionato
        :return: Percorso del folder creato
        '''

        #genero un timestamp con la data e l'ora attuale nel formato YYYY-MM-DD_HH-MM-SS
        #in modo da creare cartelle con nomi unici, basate sul momento in cui vengono generate
        date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        scenarioFolder = "congestioned" if congestioned else "basic"

        #costruisco il percorso della cartella
        newPath = os.path.join(constants.SCENARIO_COLLECTION_PATH, f"{date}_{scenarioFolder}/")

        #crea fisicamente la cartella: se non esiste già la crea
        os.makedirs(newPath,exist_ok=True)
        return newPath

    def generateRoutes(self, edgefile: str, folderPath: str, totalVehicles: int, minLoops: int = 1, congestioned: bool = False) -> str:
        '''
        Genera un route file (.rou.xml) per sumoenv utilizzando edgefile dato in ingresso

        :param edgefile: path dell'edge file che contiene il conteggio dei veicoli sulle varie strade
        :param folderPath:
        :param totalVehicles: numero totale di veicoli da inserire nel route file
        :param minLoops: numero minimo di loops o punti di conteggio che ogni veicolo deve attraversare
        :param congestioned:Flag che indica se lo scenario deve essere congestionato
        :return: percorso assoluto del route file generato
        '''

        #controllo sui parametri di input
        if not edgefile:
            raise ValueError("No edge file provided.")
        if totalVehicles is None:
            raise ValueError("The total number of vehicles was not defined.")

        if not os.path.exists(constants.SUMO_TOOLS_PATH):
            raise FileNotFoundError("sumoenv tools path does not exist.")

        script1 = constants.SUMO_TOOLS_PATH + "/randomTrips.py"
        arg1 = ""
        if constants.SUMO_PATH.startswith("./"):
            arg1 = constants.SUMO_PATH[2:]
        else:
            arg1 = constants.SUMO_PATH
        arg1 = os.path.join(arg1, "static/joined_lanes.net.xml")
        arg1 = os.path.abspath(arg1)
        print(arg1)
        print(edgefile)

        #esegue lo script di SUMO randomTrips.py, per generare delle route casuali per la simulazione
        '''
        randomTrips.py --> crea percorsi casuali sulla rete SUMO
        -n arg1 --> Specifica il file della rete joined_lanes.net.xml
        -"-r", folderPath + "sampleRoutes.rou.xml" --> salva il file di output
        -- random --> genera percorsi randomici
        --min-distance 100 --> imposta una distanza minima di 100 metri tra origine e destinazione
        --random-factor 200 --> Aumenta la casualità nella generazione delle rotte
        '''
        subprocess.run(['python', script1, "-n", arg1, "-r", folderPath + "sampleRoutes.rou.xml", "--fringe-factor", "10", "--random",
                        "--min-distance", "100", "--random-factor", "200"])

        # esegue lo script di SUMO routeSampler.py, per generare le route in base ai dati reali per la simulazione
        script2 = constants.SUMO_TOOLS_PATH + "/routeSampler.py"
        if congestioned:

            subprocess.run([sys.executable, script2, "-r", folderPath + "sampleRoutes.rou.xml", "--edgedata-files",
                            edgefile, "-o", folderPath + "generatedRoutes.rou.xml", "--total-count",
                            str(totalVehicles), "--optimize", "full", "--min-count", str(minLoops)])

        else:
            subprocess.run([sys.executable, script2, "-r", folderPath + "sampleRoutes.rou.xml", "--edgedata-files",
                            edgefile, "-o", folderPath + "generatedRoutes.rou.xml", "--total-count",
                            str(totalVehicles), "--optimize", "full", "--min-count", str(minLoops)])

        print("Routes Generated")

        relativeRouteFile = folderPath
        routeFilePath = os.path.abspath(relativeRouteFile)
        return routeFilePath


    def setScenario(self, routeFilePath=None, manual: bool = False, absolutePath: bool = False):
        '''
        Sets the scenario in the simulator by selecting a route file.
A       manual file can also be selected using a file dialog.
        :param routeFilePath:The path to the route file (optional if manual=True).
        :param manual:If True, opens a file dialog for manual route file selection.
        :param absolutePath:Boolean indicating if the provided routeFilePath is an absolute path.
        :return:
        '''

        #controllo della modalità manuale: permette, mediante una finestra, di selezioanre manualmente il file .rou.xml
        if manual:
            Tk().withdraw()
            routeFilePath = askopenfilename(title="Select a Route File", filetypes=(("route files", "*.rou.xml"), ("xml files", "*.xml")))

            if not routeFilePath:
                print("No route file was selected.")
                return
            print("The chosen file was " + routeFilePath)

        #controllo del percorso e verifica l'esistenza del file
        if routeFilePath:
            if not absolutePath:
                routeFilePath = os.path.abspath(routeFilePath)
            if not os.path.exists(routeFilePath):
                raise FileNotFoundError(f"The route file '{routeFilePath}' does not exist.")
            self.sim.changeRoutePath(routePath=routeFilePath)
        else:
            print("No route file path was provided or selected")

class Planner:
    '''

    '''
    simulator: Simulator
    scenarioGenerator: ScenarioGenerator

    def __init__(self, simulator: Simulator):
        '''

        :param simulator:
        '''
        self.simulator = simulator
        self.scenarioGenerator = ScenarioGenerator(sumocfg="run.sumocfg",sim=self.simulator)

    def planBasicScenarioForOneHourSlot(self, collectedData: pd.DataFrame, entityType: str, totalVehicles: int, minLoops: int, congestioned: bool, activeGui: bool=False):
        '''

        :param collectedData:
        :param entityType:
        :param totalVehicles:
        :param minLoops:
        :param congestioned:
        :param activeGui:
        :return:
        '''
        if entityType.lower() not in ["road segment", "roadsegment"]:
            raise ValueError(f"Invalid entity type: {entityType}. Simulation requires edge IDs to generate a scenario.")

        root = ET.Element('data')
        interval = ET.SubElement(root, 'interval', begin='0', end='3600')
        scenarioFolder = self.scenarioGenerator.defineScenarioFolder(congestioned=congestioned)
        for _, row in collectedData.interrows():
            edgeID = row.get('edgeid')
            trafficFlow = row.get('trafficflow')
            if edgeID is None:
                raise ValueError("Edge ID is missing for one of the rows in the collected data.")
            ET.SubElement(interval, 'edge', id=edgeID, entered=str(trafficFlow))

        tree = ET.ElementTree(root)
        ET.indent(tree, ' ')
        edgeFilePath = os.path.join(scenarioFolder, "edgefile.xml")
        tree.write(edgeFilePath, "UTF-8")
        routeFilePath = self.scenarioGenerator.generateRoutes(edgefile=edgeFilePath, folderPath=scenarioFolder, totalVehicles=totalVehicles, minLoops=minLoops, congestioned=congestioned)
        self.scenarioGenerator.setScenario(routeFilePath=routeFilePath, manual=False, absolutePath=True)
        logfilepath = os.path.join(scenarioFolder, "sumo_log.txt")
        self.simulator.start(activeGui=activeGui, logFilePath=logfilepath)

        return scenarioFolder





