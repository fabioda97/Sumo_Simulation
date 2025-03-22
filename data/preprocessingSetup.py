from libraries.utils import preprocessingUtils

def run():
    preprocessingUtils.filterWithAccuracy("data/traffic_flow_2024.csv", "data/accuracy_loops_2024.csv", 'data', 'codice_spira', "data/accurate_traffic_flow.csv", 90)

    #preprocessingUtils.generateRealFlow("data/accurate_traffic_flow.csv", "data/real_traffic_flow.csv")
    preprocessingUtils.generateRoadNamesFile("data/accurate_traffic_flow.csv", "configs/joined_lanes.net.xml", "configs/detectors.add.xml", "data/road_names.csv")
    preprocessingUtils.fillMissingEdgeId("data/road_names.csv")

    #ATTENZIONE: impiega molto tempo per eseguire!!!
    #preprocessingUtils1.linkEdgeID("data/accurate_traffic_flow.csv", "data/road_names.csv", "data/processed_traffic_flow.csv")

    preprocessingUtils.generateEdgeDataFile("data/processed_traffic_flow.csv", "configs/edgedata.xml", date='01/02/2024', time_slot='07:00-08:00')
    preprocessingUtils.dailyFilter("data/processed_traffic_flow.csv", "01/02/2024")
    preprocessingUtils.generateEdgeDataPerHour("data/processed_traffic_flow.csv", "configs/TestData_UnMese", "01/02/2024", "02/03/2024")