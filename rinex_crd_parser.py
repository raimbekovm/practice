import os
from rinex_header_parser import (
    INPUT_DIR,
    find_rinex_files,
    parse_rinex_header,
    extract_station_info,
    StationInfo
)

def parse_xyz_coordinates(xyz_line):
    """Parse X, Y, Z coordinates from APPROX POSITION XYZ line"""
    if xyz_line == '-':
        return '0.00000', '0.00000', '0.00000'
    
    # Extract coordinates from the line using exact character positions
    # X – символы с 3 по 15
    # Y – символы с 17 по 29
    # Z – символы с 31 по 43
    x = xyz_line[2:15].strip()  # 3-15 (0-based index: 2-14)
    y = xyz_line[16:29].strip()  # 17-29 (0-based index: 16-28)
    z = xyz_line[30:43].strip()  # 31-43 (0-based index: 30-42)
    
    # Format to 5 decimal places
    try:
        x = f"{float(x):.5f}"
        y = f"{float(y):.5f}"
        z = f"{float(z):.5f}"
    except ValueError:
        x = y = z = '0.00000'
    
    return x, y, z

def format_crd_line(num, station_id, x, y, z):
    """Format a line for the CRD file according to the template"""
    # Split station_id into name and number
    station_name = station_id[:4]
    station_number = station_id[4:]
    
    # Extract only numeric part from station number
    numeric_part = ''.join(filter(str.isdigit, station_number))
    # If no numeric part found, use "0"
    formatted_number = f"{int(numeric_part):3d}" if numeric_part else "  0"
    
    # Format with proper spacing for alignment
    # NUM(3) + space + STATION_NAME(4) + STATION_NUMBER(9) + space + X(14) + space + Y(14) + space + Z(14) + space + FLG(3)
    return (
        f"{num:3d}  "  # 3-digit number + space
        f"{station_name} {formatted_number}     "  # Station name and number + space
        f"{x:>14} "  # X coordinate + space
        f"{y:>14} "  # Y coordinate + space
        f"{z:>14} "  # Z coordinate + space
        f"{'I':>3}"  # Flag
    )

def save_crd_file(stations, output_path):
    """Save the CRD file with the formatted station information"""
    header = (
        "PPP_210940: Collecting results                                   06-MAY-25 12:25\n"
        "--------------------------------------------------------------------------------\n"
        "LOCAL GEODETIC DATUM: IGS20             EPOCH: 2025-03-01 00:00:00\n\n"
        "NUM  STATION NAME           X (M)          Y (M)          Z (M)     FLAG\n\n"
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        
        # Process each station
        for i, station in enumerate(stations, 1):
            station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
            x, y, z = parse_xyz_coordinates(station.xyz)
            line = format_crd_line(i, station_id, x, y, z)
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
    
    # Save CRD file
    save_crd_file(stations, '2025_05_22-Задание на практику/2025.CRD')

if __name__ == '__main__':
    main() 