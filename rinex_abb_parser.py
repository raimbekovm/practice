import os
import re
from rinex_header_parser import (
    INPUT_DIR,
    find_rinex_files,
    parse_rinex_header,
    extract_station_info,
    StationInfo
)

def generate_station_id(station_name, station_number):
    """Generate station ID in format: NAME + NUMBER (first 4 chars of name + first 9 chars of number)"""
    return f"{station_name[:4].strip()}{station_number[:9].strip()}"

def generate_sequence_id(index):
    """Generate sequence ID in format: 01-99, then 0A-ZZ"""
    if index < 0 or index > 945:  # Maximum possible combinations (99 + 26*26)
        raise ValueError("Index out of range for sequence ID generation")
    
    # For numbers 01-99
    if index < 99:
        return f"{index + 1:02d}"
    
    # For letter combinations 0A-ZZ
    index = index - 99  # Adjust index for letter combinations
    first_char = chr(ord('0') + (index // 26)) if index < 26 else chr(ord('A') + ((index - 26) // 26))
    second_char = chr(ord('A') + (index % 26))
    return f"{first_char}{second_char}"

def format_abb_line(station_id, sequence_id, rinex_filename):
    """Format a line for the ABB file according to the template"""
    # Split station_id into name and number
    station_name = station_id[:4]
    station_number = station_id[4:]
    
    # Format: STATION_NAME(4) + SPACE + STATION_NUMBER(9) + 11 SPACES + 4-ID(4) + 5 SPACES + 2-ID(2) + 5 SPACES + Remark
    return (
        f"{station_name} {station_number:<9}"
        f"{' ' * 11}"  # 11 spaces after station number
        f"{station_name:<4}"
        f"{' ' * 5}"   # 5 spaces after 4-ID
        f"{sequence_id:<2}"
        f"{' ' * 5}"   # 5 spaces after 2-ID
        f"From {rinex_filename}"
    )

def save_abb_file(stations, output_path):
    """Save the ABB file with the formatted station information"""
    header = (
        "ABBREVIATON FILE\n"
        "--------------------------------------------------------------------------------\n\n"
        "Station name             4-ID    2-ID    Remark\n\n\n"
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        
        # Process each station
        for i, station in enumerate(stations):
            station_id = generate_station_id(station.marker_name, station.marker_number)
            sequence_id = generate_sequence_id(i)
            line = format_abb_line(station_id, sequence_id, station.filename)
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
    
    # Save ABB file
    save_abb_file(stations, '2025_05_22-Задание на практику/2025.ABB')

if __name__ == '__main__':
    main() 