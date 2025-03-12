
from statistics import mean
from libraries.constants import *
import os
import traci
from typing import Optional

from build.lib.traci import inductionloop
from output.generateITetrisNetworkMetrics import interval
from purgatory.binary2plain import elements


class Simulator:
    def __init__(self, configurationPath: str, logFile: str):
        self.configurationPath = configurationPath
        self.routePath = configurationPath
        staticpath = os.path.abspath(self.configurationPath + "/static")
        if not os.path.exists(staticpath):
            print("Error: the given path does not exist.")
            return 
        
        os.environ["STATICPATH"] = staticpath
        self.logFile = logFile
        self.listener = ValueListener()
        traci.addStepListener(self.listener)

    def start(self, activeGui: bool = False, logFilePath: Optional[str] = None):

        '''
        Avvia una simulazione in SUMO, scegliendo se visualizzare o meno la GUI.
        Sovrascrive qualsiasi simulazione già in corso.
        scrivere un log della simulazione, se viene specificato un file di log.

        :param activeGui: If True, starts the simulation with the SUMO GUI (sumo-gui).
                          If False, starts the simulation without the GUI (sumo). Default is False.
        :param logFilePath:Optional path to a log file. If specified, the log file is used for the SUMO trace.
        :return:
        '''
        if traci.isLoaded():
            print("Warning: A previous simulation was loaded. It will be overwritten.")

        #Construct the command for starting SUMO or SUMO-GUI
        sumo_command = "sumo-gui" if activeGui else "sumo"
        command = [sumo_command, "-c", os.path.join(self.configurationPath, "run.sumocfg")]

        #set the log file path if specified
        self.logFile=logFilePath if logFilePath else self.logFile

        #start the simulation with the specified command and log file
        traci.start(command, traceFile=self.logFile)
        print("Note: Each simulation step is equivalent to " + str(traci.simulation.getDeltaT()) + " seconds.")

        #resume the simulation
        self.resume()

    def startBasic(self, activeGui=False):
        '''
        Avvia una simulazione in SUMOENV con una configurazione di base.
        Sostituisce una simulazione già in esecuzione, se presente.
        :param activeGui:If True, starts the simulation with the sumoenv GUI (sumo-gui).
                         If False, starts the simulation without the GUI (sumo). Default is False.
        :return:
        '''
        if traci.simulation.isLoaded():
            print("Warning: A previous simulation was loaded. It will be overwritten.")
        sumo_command = "sumo-gui" if activeGui else "sumo"
        command = [sumo_command, "-c", os.path.join(self.configurationPath, "run.sumocfg")]
        traci.start(command, traceFile=self.logFile)
        self.resume()

    def startCongesioned(self, activeGui=False):
        '''
        Avvia una simulazione in SUMOENV con lo scenario congestionato.
        Sostituisce una simulazione già in esecuzione, se presente.
        :param activeGui:If True, starts the simulation with the sumoenv GUI (sumo-gui).
                                 If False, starts the simulation without the GUI (sumo). Default is False.
        :return:
        '''
        if traci.simulation.isLoaded():
            print("Warning: A previous simulation was loaded. It will be overwritten.")
        sumo_command = "sumo-gui" if activeGui else "sumo"
        command = [sumo_command, "-c", os.path.join(self.configurationPath, "run.sumocfg")]
        traci.start(command, traceFile=self.logFile)
        self.resume()

    def step(self, quantity=1):
        '''
        Fa avanzare la simulazione di un certo numero di passi (steps) (di default 1).
        Ogni step solitamente corrisponde a un secondo di tempo simulato.
        :param quantity:
        :return:
        '''
        step=0
        while step < quantity and self.RemainingVehicles() > 0:
            traci.simulationStep()
            self.vehiclesSummary = self.getVehiclesSummary()
            self.checkSubscription()
            self.getInductionLoopSummary()
            print(self.getRemainingVehicles())
            step += 1

    def oneHourStep(self):
        '''
        Fa avanzare la simulazione di 3600 secondi (1 ora), ma solo se ci sono ancora veicoli nella simulazione.
        :return:
        '''
        if traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep(3600)

    def resume(self):
        '''
        Resumes the simulation, esegue fino a quando non ci sono più veicoli nella simulazione
        :return:
        '''
        while traci.simulation.getMinExpectedNumber() > 0:
            self.step()
        self.end()

    def end(self):
        '''
        Interrompe la simulazione in corso.
        Chiude la connessione con SUMOENV, liberando eventuali risorse utilizzate.

        :return:
        '''

        return traci.close()

    def getRemainingVehicles(self):
        '''
        Conta i veicoli ancora presenti nella simulazione.
        Include sia i veicoli attualmente sulla strada sia quelli in attesa di entrare nella simulazione.
        :return:
        '''
        return traci.simulation.getMinExpectedNumber()

    def changeRoutePath(self, routePath: str):
        '''
        changes the route path fo the simulation
        Questa funzione permette di cambiare dinamicamente
        il file delle rotte usato nella simulazione SUMO,
        a patto che il file esista. Se il file non esiste,
        non cambia nulla e avvisa l’utente con un messaggio di errore.
        :param routePath:
        :return:
        '''
        if not os.path.exists(routePath):
            print("Error: the given path does not exist.")
            return
        self.routePath = routePath
        os.environ["SIMULATIONPATH"] = routePath
        print("the path was set to " + routePath)

    ### VEHICLE FUNCTIONS
    def getVehiclesSummary(self):
        '''
        Analizza tutti i veicoli attualmente presenti nella simulazione.
        Calcola le seguenti statistiche medie:
        Velocità media.
        time lost: tempo speso in rallentamenti o fermi.
        Distanza percorsa.
        Ritardo alla partenza (departure delay).
        waiting time: tempo trascorso in attesa di muoversi.

        :return: A dictionary containing average statistics for the vehicles in the simulation.
        '''

        vehicleSummary = {}
        vehiclesList = traci.vehicle.getIDList()
        summary = []
        if len(vehiclesList) > 1:
            for vehicleID in vehiclesList:
                element = {}
                element["speed"] = traci.vehicle.getSpeed(vehicleID)
                element["timeLost"] = traci.vehicle.getTimeLoss(vehicleID)
                element["distance"] = traci.vehicle.getDistance(vehicleID)
                element["departDelay"] = traci.vehicle.getDepartDelay(vehicleID)
                element["totalWaitingTime"] = traci.vehicle.getAccumulatedWaitingTime(vehicleID)
                summary.append(element)

            vehicleSummary["averageSpeed"] = mean(element["speed"] for element in summary)
            vehicleSummary["averangeTimeLost"] = mean(element["timeLost"] for element in summary)
            vehicleSummary["averageDepartDelay"] = mean(element["departDelay"] for element in summary)
            vehicleSummary["averageWaitingTime"] = mean(element["totalWaitingTime"] for element in summary)
            self.vehicleSummary = vehicleSummary
            return vehicleSummary
        print("There are no vehicles ")
        return None

    ### INDUCTION LOOP FUNCTIONS
    def getDetectorList(self):
        '''
        :return: list of all induction loop detectors in the simulation.
        '''
        return traci.inductionloop.getIDList()

    def getAverageOccupationTime(self):
        '''
        Analizza tutti gli induction loop detectors nella simulazione

        :return: (float) il tempo medio di occupazione dei veicoli sopra i rilevatori
        '''
        detectorList= self.getDetectorList()
        intervalOccupancies = []
        for detector in detectorList:
            intervalOccupancies.append(traci.inductionloop.getIntervalOccupancy(detector))
        average = mean(intervalOccupancies)
        return average

    def getInductionLoopSummary(self):
        '''
        Analizza tutti gli induction loop detectors nella simulazione
        Calcola le seguenti statistiche:
        (interval occupancy) → quanto tempo i veicoli occupano il loop .
        (mean speed) → velocità media dei veicoli che passano sopra i loop.
        (vehicle numbers) → quanti veicoli sono passati sopra i loop.
        :return: dizionario contenente le statistiche calcolate prima
        '''
        detectorList = self.getDetectorList()
        detectors = []
        inductionLoopSummary = {}
        for detector in detectorList:
            element = {}
            element["intervalOccupancy"] = traci.inductionloop.getIntervalOccupancy(detector)
            element["meanSpeed"] = traci.inductionloop.getIntervalMeanSpeed(detector)
            element["vehicleNumber"] = traci.inductionloop.getIntervalVehicleNumber(detector)
            detectors.append(element)
        inductionLoopSummary["averageIntervalOccupancy"] = mean(element["intervalOccupancy"] for element in detectors)
        inductionLoopSummary["averageMeanSpeed"] = mean(element["meanSpeed"] for element in detectors)
        inductionLoopSummary["averageVehicleNumber"] = mean(element["vehicleNumber"] for element in detectors)
        return inductionLoopSummary

    def findLinkedTLS(self, detectorID: str):
        '''
        prende in ingresso l'ID di un detector e trova i semafori (TLS) collegati al detector

        :param detectorID:
        :return: (list) degli id dei TLS collegati al detector
        '''

        lane = traci.inductionloop.getLaneID(detectorID)
        tls = self.getTLSList()
        found = []
        for element in tls:
            lanes = traci.trafficlight.getControlledLanes(element)
            if lane in lanes:
                found.append(element)

        return found

    def subscriveToInductionLoop(self, inductionLoopID, value: str):
        '''
         Subscribes to an induction loop to monitor specified parameters (occupancy, speed, vehicle number).
        :param inductionLoopID: ID of Induction Loop
        :param value: The parameter to subscribe to ('intervalOccupancy', 'meanSpeed', 'vehicleNumber').
        :return:
        '''

        if value == "intervalOccupancy":
            traci.inductionloop.subscribe(inductionLoopID, [traci.constants.VAR_INTERVAL_OCCUPANCY])
        elif value == "meanSpeed":
            traci.inductionloop.subscribe(inductionLoopID, [traci.constants.VAR_INTERVAL_SPEED])
        elif value == "vehicleNumber":
            traci.inductionloop.subscribe(inductionLoopID, [traci.constants.VAR_INTERVAL_NUMBER])



    def checkSubscription(self):
        '''
        recupera i risultati delle subscription per tutti gli induction loop e modifica i programmi dei TLS se
        il numero di veicoli o l'occupazione eccede una data soglia

        '''

        results = traci.inductionloop.getAllSubscriptionResults()
        for key, value in results.items():
            #controlla se ci sono tanti veicoli
            if traci.constants.VAR_INTERVAL_NUMBER in value and value[traci.constants.VAR_INTERVAL_NUMBER] > 10:
                tlsIDs = self.findLinkedTLS(key)
                for element in tlsIDs:
                    self.setTLSProgram(element, "utopia")
                    print("New program is " + str(traci.trafficlight.getProgram(element)))
            if traci.constants.VAR_INTERVAL_OCCUPANCY in value and value[traci.constants.VAR_INTERVAL_OCCUPANCY] > 30:
                print("value in excess")


    ### TLS FUNCTIONS
    def getTLSList(self):

        '''

        :return: (list) if TLS IDs
        '''
        return traci.trafficlight.getIDList()
    def checkTLS(self, tlsID):
        '''
        controlla se l'ID del TLS in ingresso esiste nella simulazione
        :param tlsID:
        :return: (bool) --> true if exists, False otherwise
        '''
        tls = self.getTLSList()
        if tlsID in tls:
            return True
        else:
            return False

    def setTLSProgram(self, trafficLightID: str, programID: str, all=False):
        '''
        Setta un programma per uno o tutti i TLS
        :param trafficLightID: ID del TLS a cui si vuole cambiare programma
        :param programID: L'ID del nuovo programma
        :param all: se True lo setta a tutti i TLS della simulazione. False di Default
        :return:
        '''

        if all:
            tls = self.getTLSList()
            for traffic_light in tls:
                traci.trafficlight.setProgram(traffic_light,programID)
            print("The program of all traffic light is changed to" + str(programID))
        elif self.checkTLS(trafficLightID):
            traci.trafficlight.setProgram(trafficLightID, programID)
            print("The program of the TLS " +str(trafficLightID) + " is changed to " + str(programID))




class ValueListener(traci.StepListener):
    def step(self, t=0):
        return True