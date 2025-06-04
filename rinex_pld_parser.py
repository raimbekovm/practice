import os
from rinex_header_parser import (
    INPUT_DIR,
    find_rinex_files,
    parse_rinex_header,
    extract_station_info,
    StationInfo
)

def format_pld_line(num, station_id):
    """Format a line for the PLD file according to the template"""
    # Split station_id into name and number
    station_name = station_id[:4]
    station_number = station_id[4:]
    
    # Format: NUM(2) + 2 spaces + STATION_NAME(4) + space + STATION_NUMBER(9) + spaces + VX(13) + spaces + VY(13) + spaces + VZ(13) + spaces + FLAG(4) + spaces + PLATE(4)
    line = (
        f"{num:02d}  "  # 2-digit number with leading zeros and 2 spaces
        f"{' ' * 1}"    # Add 2 spaces to reach column 6
        f"{station_name} {station_number:<9}"  # Station name and number
        f"{' ' * 13}"  # VX space
        f"{' ' * 13}"  # VY space
        f"{' ' * 13}"  # VZ space
        f"{' ' * 4}"   # FLAG space
    )
    
    # Ensure the line is exactly 75 characters before adding EURA
    line = line.ljust(75)
    line += "EURA"  # Add EURA in positions 76-80
    
    return line

def save_pld_file(stations, output_path):
    """Save the PLD file with the formatted station information"""
    header = (
        "Example plate assignement\n"
        "--------------------------------------------------------------------------------\n"
        "LOCAL GEODETIC DATUM: IGS14           \n\n"
        "NUM  STATION NAME           VX (M/Y)       VY (M/Y)       VZ (M/Y)  FLAG   PLATE\n\n"
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        
        # Process each station
        for i, station in enumerate(stations, 1):
            station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
            line = format_pld_line(i, station_id)
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
    
    # Save PLD file
    save_pld_file(stations, '2025_05_22-Задание на практику/2025.PLD')

if __name__ == '__main__':
    main() 