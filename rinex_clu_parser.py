import os
from rinex_header_parser import (
    INPUT_DIR,
    find_rinex_files,
    parse_rinex_header,
    extract_station_info,
    StationInfo
)

def format_clu_line(station_id):
    """Format a line for the CLU file according to the template"""
    # Split station_id into name and number
    station_name = station_id[:4]
    station_number = station_id[4:]
    
    # Get the first digit of the station number for CLU
    clu_value = station_number[0] if station_number else "*"
    
    # Format: STATION_NAME(4) + SPACE + STATION_NUMBER(9) + 5 SPACES + CLU(1)
    return f"{station_name} {station_number:<9}{' ' * 5}{clu_value}"

def save_clu_file(stations, output_path):
    """Save the CLU file with the formatted station information"""
    header = (
        "BSW 5.2: PROCESSING EXAMPLE                                      10-JAN-12 06:07\n"
        "--------------------------------------------------------------------------------\n\n"
        "STATION NAME      CLU\n"
        "****************  ***\n"
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        
        # Process each station
        for station in stations:
            station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
            line = format_clu_line(station_id)
            f.write(line + '\n')
    
    print(f'Файл {output_path} успешно создан!')

def main():
    # Find all RINEX files
    files = find_rinex_files(INPUT_DIR)
    print('Найдено файлов:', len(files))
    for file in files:
        print(' -', file)
    print('=' * 40)
    
    # Process each file
    stations = []
    for file in files:
        header = parse_rinex_header(file)
        station = extract_station_info(header, os.path.basename(file))
        stations.append(station)
    
    print(f'Собрано информации о {len(stations)} станциях.')
    
    # Save CLU file
    save_clu_file(stations, '2025_05_22-Задание на практику/2025.CLU')

if __name__ == '__main__':
    main() 