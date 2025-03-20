import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
# from libraries.constants import *
import sumolib
import os


def filterWithAccuracy(file_input: str, file_accuracy: str, date_column: str, sensor_id_column: str, output_file: str,
                       accepted_percentage: int):
    '''
       A partire dal dataset di traffico, rilevato dalle spire, (file_input) e dal dataset di accuratezza (file_accuracy)
       di rilevamento delle spire, viene generato un file filtrato (output filters) contenente il dataset con una certa
       percentuale di accuratezza. Entrambi i file di input sono organizzati per data e per sensor ID in modo da avere la
       la corretta percentuale di accuratezza per ogni giorno, per ogni ora di lavoro rispetto allo specifico sensore.
       :param file_input: path del traffic loop dataset
       :param file_accuracy: path del file di accuratezza
       :param date_column: Il nome della colonna DATA in entrambi i file
       :param sensor_id_column: Nome della colonna SENSOR ID in entrambi i file
       :param output_file: Path del file di output
       :param accepted_percentage: Percentuale minima di accuratezza per il filtraggio
       :return:
       '''
    # Load the input data and accuracy data from the specified file paths
    df_input = pd.read_csv(file_input, sep=';', encoding="UTF-8")
    df_accuracy = pd.read_csv(file_accuracy, sep=';', encoding="UTF-8")

    # Clean and filter the accuracy data to only include measurements above `accepted_percentage`
    for ind, column in enumerate(df_accuracy.columns):
        if ind > 1:  # Ignore the first two columns, assumed to be `date_column` and `sensor_id_column`
            # Remove '%' and convert to integers
            df_accuracy[column] = df_accuracy[column].str.replace('%', '').astype(int)
            # Drop rows where the accuracy is below `accepted_percentage`
            df_accuracy = df_accuracy[df_accuracy[column] >= accepted_percentage]

    # Extract date and sensor ID columns as an identifier for filtering
    identifier = df_accuracy[[date_column, sensor_id_column]]
    keys = list(identifier.columns)

    # Create indices based on the date and sensor ID columns for both dataframes
    i1 = df_input.set_index(keys).index
    i2 = df_accuracy.set_index(keys).index

    # Filter `df_input` to include only rows that match the high-accuracy entries in `df_accuracy`
    filtered_df = df_input[i1.isin(i2)]

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Directory '{output_dir}' created for the output file.")

    # Save the filtered data to the specified output file
    filtered_df.to_csv(output_file, sep=';', index=False)
    print(f"Output with filtered accuracy created at '{output_file}'.")

def generateRealFlow(inputFile: str, outputFile: str):
    '''
    Funzione che genera un file con il traffico reale con determinate colonne. Legge da un file CSV contenente i dati
    del traffico, seleziona specifiche colonne e salva i dati filtrati in un nuovo CSV 'real_traffic_flow.csv' nel path
    `REAL_TRAFFIC_FLOW_DATA_MVENV_PATH`
        :param inputFile:
        :return:
        '''
    # Load the input CSV file
    df = pd.read_csv(inputFile, sep=';')

    # Select the relevant columns for real traffic flow data
    columns_to_keep = [
        'data', 'codice_spira', '00:00-01:00', '01:00-02:00', '02:00-03:00', '03:00-04:00', '04:00-05:00',
        '05:00-06:00', '06:00-07:00', '07:00-08:00', '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00',
        '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00', '18:00-19:00',
        '19:00-20:00', '20:00-21:00', '21:00-22:00', '22:00-23:00', '23:00-24:00', 'Nome via', 'direzione',
        'longitudine', 'latitudine', 'geopoint', 'ID_univoco_stazione_spira']

    df = df[columns_to_keep]

    # Ensure the output directory exists
    output_dir = os.path.dirname(outputFile)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Directory '{output_dir}' created for the output file.")

    # Save the filtered data to the specified output file
    df.to_csv(outputFile, sep=';', index=False)
    print(f"Output with filtered accuracy created at '{outputFile}'.")

def generateRoadNamesFile (inputFile: str, sumoNetFile: str, detectorFilePath: str, roadNamesFilePath: str):
    '''
    Associa le strade ad un EDGE ID della rete SUMO usando le coordinate GPS delle strade
        :param inputFile: PATH con i nomi delle strade e le coordinate GPS
        :param sumoNetFile: Il file con gli ID della rete SUMO
        :param detectorFilePath: Path del file output contendnete la definizione dei sensori di traffico (inductionLoop) per SUMO
        :param roadNamesFilePath: Path del file csv contente i nomi delle strade e gli edgeID associati
        :return:
    '''
    #Load the SUMO network using sumolib
    net=sumolib.net.readNet(sumoNetFile)

    # Load input data and filter unique road names and geopoints
    input_df = pd.read_csv(inputFile, sep=';')
    df_unique = input_df[['Nome via', 'geopoint']].drop_duplicates()

    # Create the root element for the XML file
    root = ET.Element('additional')

    for index, row in df_unique.iterrows():
        # Extract latitude and longitude from the geopoint
        coord = row['geopoint']
        lat, lon = map(float, coord.split(','))

        # Convert geographic coordinates to SUMO's (x, y) coordinates
        x, y = net.convertLonLat2XY(lon, lat)
        print(f"SUMO reference coordinates (x, y): ({x}, {y})")

        # Find neighboring edges within a 25m radius, sorted by distance
        candidate_edges = net.getNeighboringEdges(x, y, r=25)
        edges_and_dist = sorted(candidate_edges, key=lambda edge: edge[1])

        # Attempt to find the closest edge that matches the road name or is suitable
        closest_edge = None
        if edges_and_dist:
            for edge, dist in edges_and_dist:
                edge_name = edge.getName().lower()
                road_name = row["Nome via"].lower()

                # Check if the edge name matches the road name, or find a suitable edge type
                if edge_name == road_name or edge.getType() not in ["highway.pedestrian", "highway.track",
                                                                    "highway.footway", "highway.path",
                                                                    "highway.cycleway", "highway.steps"]:
                    closest_edge = edge
                    break
            else:
                # If no matching edge is found, set closest_edge to the first suitable edge
                closest_edge = next((edge for edge, dist in edges_and_dist if
                                     edge.getType() not in ["highway.pedestrian", "highway.track", "highway.footway",
                                                            "highway.path", "highway.cycleway", "highway.steps"]), None)

        if closest_edge:
            print(f"Name: {closest_edge.getName()}")
            print(f"Edge ID: {closest_edge.getID()}")

            # Assign the closest edge ID to the row in df_unique
            df_unique.at[index, 'edge_id'] = closest_edge.getID()

            # Add an induction loop element to the XML structure
            ET.SubElement(root, 'inductionLoop', id=f"{index}_0", lane=f"{closest_edge.getID()}_0", pos="-5",
                          freq="1800", file="e1_real_output.xml")
        else:
            # Drop rows where no suitable edge is found within the network
            print(f"No suitable edge found for road '{row['Nome via']}' at coordinates ({lat}, {lon}).")
            df_unique.drop(index, inplace=True)

    # Ensure the directory for the XML output file exists
    os.makedirs(os.path.dirname(detectorFilePath), exist_ok=True)

    # Save the XML tree with pretty formatting
    tree = ET.ElementTree(root)
    ET.indent(tree, '  ')
    tree.write(detectorFilePath, encoding="UTF-8", xml_declaration=True)
    print(f"XML file saved at '{detectorFilePath}'")

    # Ensure the directory for the CSV output file exists
    os.makedirs(os.path.dirname(roadNamesFilePath), exist_ok=True)

    # Save the updated DataFrame with edge IDs to the specified CSV file path
    df_unique.to_csv(roadNamesFilePath, sep=';', index=False)
    print(f"CSV file with road names and edge IDs saved at '{roadNamesFilePath}'")

def fillMissingEdgeId(roadnameFile: str):
    '''
    Funzione che cerca nel roadnamefile le entry dei nomi delle strade alle quali non è associato un EDGE_ID.
    Per tali entry tenta di trovare un'altra voce che ha lo stesso nome_via e con EDGE_ID valido, se lo trava
    assegna tale valore alla strada con EDGE_ID mancante. La funzione segnala la strada per la quale non si riesce ad
    assegnare un EDGE_ID.
    :param roadnameFile:
    :return:
    '''
    # Load the road names data from the specified file
    df = pd.read_csv(roadnameFile, sep=';')
    empty = 0

    # Iterate over each row to check for missing edge IDs
    for index, row in df.iterrows():
        if pd.isnull(row['edge_id']):
            # Find other rows with the same road name ('Nome via') that have a valid edge ID
            sameStreet = df[(df['Nome via'] == row['Nome via']) & (df['edge_id'].notna())]
            if not sameStreet.empty:
                # Fill in the missing edge_id with the first matching edge_id found
                df.at[index, 'edge_id'] = sameStreet['edge_id'].values[0]
            else:
                # Increment count if no matching edge ID is found
                empty += 1

    # Report the number of roads without an edge ID
    print("Roads without edge ID: " + str(empty))
    # Save the updated DataFrame back to the CSV file
    df.to_csv(roadnameFile, sep=';', index=False)

def linkEdgeID(inputFile: str, roadNamesFile: str, outputFile: str):
    '''
        Funzione che collega gli EDGE_ID di SUMO alle strade. Per ogni riga dell'inputFile, trova il corrispondente EDGE_ID
        nel roadnameFile e lo assegna.
        :param inputFile:
        :param roadnaleFile:
        :param outputFile:
        :return:
    '''
    # Load input and road names data
    df = pd.read_csv(inputFile, sep=';')
    dfRoadnames = pd.read_csv(roadNamesFile, sep=';')


    # Iterate over each row in the input DataFrame to find and link edge IDs
    for index, row in df.iterrows():
        print(f"Processing row {index}: Nome via = {row['Nome via']}, Geopoint = {row['geopoint']}")  # DEBUG 1
        # Find matching edge_id in the road names file based on road name and geopoint
        edge = dfRoadnames.loc[
            (dfRoadnames['Nome via'] == row['Nome via']) &
            (dfRoadnames['geopoint'] == row['geopoint']),
            'edge_id'
        ]
        print(f"Found edges: {edge.values}")  # DEBUG 2: Mostra i valori trovati


        # If no matching edge_id is found, remove the row; otherwise, link the edge_id
        if len(edge) == 0:
            df.drop(index, inplace=True)
            continue
        df.at[index, 'edge_id'] = edge.values[0]  # Assign the first match

    # Save the modified DataFrame to the output file
    df.to_csv(outputFile, sep=';', index=False)
    print(f"Updated file with linked edge IDs saved at '{outputFile}'")

def generateEdgeDataFile(input_file: str,  outputFile: str, date: str = "01/02/2024", time_slot: str = "00:00-01:00", duration: str = '3600'):
    '''
    Funzione che genera il file EdgeData.xml contenente i dati di traffico per gli edge SUMO basandosi su un dataset
    che registra il numero di veicoli contati in varie strade e per una determinata fascia oraria.
    :param inputFile: Path del file contenente i dati di traffico
                    -'edge_id' --> ID della strada
                    -'data' --> Data della misura del traffico
                    -'time_slot' --> colonne della fascia oraria con il conteggio dei veicoli
    :param date:
    :param time_slot:
    :param duration:
    :return:
    '''
    # Create the root element for the XML structure
    root = ET.Element('data')
    interval = ET.SubElement(root, 'interval', begin='0', end=duration)

    # Load and filter data based on the specified date
    df = pd.read_csv(input_file, sep=';')
    df = df[df['data'].str.contains(date)]

    for index, row in df.iterrows():
        edge_id = str(row['edge_id'])
        first = int(time_slot[:2])
        last = int(time_slot[6:8])

        # Calculate the vehicle count for the specified time slot
        if last - first > 1:  # If the time slot spans multiple hours
            total_count = sum(row[f"{hour:02d}:00-{(hour + 1) % 24:02d}:00"] for hour in range(first, last))
            count = str(total_count)
        else:
            count = str(row[time_slot])

        # Add the edge element to the XML with the calculated count
        ET.SubElement(interval, 'edge', id=edge_id, entered=count)

    # Ensure the directory for the output file exists
    os.makedirs(os.path.dirname(outputFile), exist_ok=True)

    # Save the XML tree with indentation
    tree = ET.ElementTree(root)
    ET.indent(tree, '  ')
    tree.write(outputFile, encoding="UTF-8", xml_declaration=True)
    print(f"Edge data XML saved at '{outputFile}'")

def dailyFilter(inputFilePath: str, date: str):
    '''
    Funzione che filtra i dati di traffico per una data specifica e salva i risultati in un file di output
    :param inputFilePath:
    :param date:
    :return:
    '''
    # Load the input CSV file
    df = pd.read_csv(inputFilePath, sep=';')

    # Filter data by the specified date
    df_filtered = df[df['data'].str.contains(date)]

    #crea un nome file corretto, sostituendo "/" con "-"
    safe_date = date.replace("/", "-")
    outputFile = f"data/daily_flow_{safe_date}.csv"

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(outputFile), exist_ok=True)

    # Save the filtered data to the daily traffic flow file path
    df_filtered.to_csv(outputFile, sep=';', index=False)
    print(f"Filtered data for date '{date}' saved in {outputFile}")


def reorderDataset(inputFilePath: str, outputFilePath: str):
    '''
    Riordina il dataset cronologicamente in base alla colonna 'date'
    :param inputFilePath:
    :param outputFilePath:
    :return:
    '''
    # Load the dataset
    df = pd.read_csv(inputFilePath, sep=';')

    # Ensure `data` column is in datetime format
    df['data'] = pd.to_datetime(df['data'], format='%Y-%m-%d')

    # Sort the dataset by date
    df_sorted = df.sort_values(by='data')

    # Save the reordered dataset
    df_sorted.to_csv(outputFilePath, sep=';', index=False)
    print(f"Dataset reordered by date and saved at '{outputFilePath}'")

def filteringDataset(inputFilePath: str, start_date: str, end_date: str, outputFilePath: str):
    '''
    Filtra il dataset per uno specifico range di sate e salva in uno specifico file
    :param inputFilePath:
    :param start_date:
    :param end_date:
    :param outputFilePath:
    :return:
    '''
    # Load the dataset
    df = pd.read_csv(inputFilePath, sep=';')

    # Convert `start_date` and `end_date` from 'mm/dd/yyyy' to 'yyyy-mm-dd' format for consistent comparison
    start_date = datetime.strptime(start_date, '%m/%d/%Y').strftime('%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%m/%d/%Y').strftime('%Y-%m-%d')

    # Ensure `data` column is parsed as datetime in 'dd/mm/yyyy' format
    df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')

    # Filter the dataset for the specified date range
    mask = (df['data'] >= start_date) & (df['data'] <= end_date)
    filtered_df = df.loc[mask]

    # Save the filtered dataset
    filtered_df.to_csv(outputFilePath, sep=';', index=False)
    print(f"Filtered data from {start_date} to {end_date} saved at '{outputFilePath}'")









