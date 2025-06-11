import os
import re
import datetime

# Constants
INPUT_DIR = '2025_05_22-Задание на практику/Образец/input'
RINEX_EXTENSIONS = ('.O', '.o')

# Header fields to search for
HEADER_FIELDS = [
    'MARKER NAME',
    'MARKER NUMBER',
    'REC # / TYPE / VERS',
    'ANT # / TYPE',
    'APPROX POSITION XYZ',
    'ANTENNA: DELTA H/E/N',
]

class StationInfo:
    def __init__(self, marker_name, marker_number, receiver, antenna, xyz, delta_hen, filename):
        self.marker_name = marker_name
        self.marker_number = marker_number
        self.receiver = receiver
        self.antenna = antenna
        self.xyz = xyz
        self.delta_hen = delta_hen
        self.filename = filename

# Common utility functions
def find_rinex_files(input_dir):
    rinex_files = []
    for root, dirs, files in os.walk(input_dir):
        for f in files:
            if f.endswith('O') or f.endswith('o'):
                rinex_files.append(os.path.join(root, f))
    return rinex_files

def parse_rinex_header(filepath):
    header = {}
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if 'END OF HEADER' in line:
                break
            for field in HEADER_FIELDS:
                if field in line:
                    header[field] = line.rstrip('\n')
    return header

def extract_station_info(header, filename):
    marker_name = header.get('MARKER NAME', '-')
    marker_number = header.get('MARKER NUMBER', '-')
    receiver = header.get('REC # / TYPE / VERS', '-')
    antenna = header.get('ANT # / TYPE', '-')
    xyz = header.get('APPROX POSITION XYZ', '-')
    delta_hen = header.get('ANTENNA: DELTA H/E/N', '-')
    return StationInfo(marker_name, marker_number, receiver, antenna, xyz, delta_hen, filename)

# CLU Parser Functions
def format_clu_line(station_id):
    """Format a line for the CLU file according to the template"""
    station_name = station_id[:4]
    station_number = station_id[4:]
    clu_value = "1"  # Default CLU value
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
        for station in stations:
            station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
            line = format_clu_line(station_id)
            f.write(line + '\n')
    
    print(f'Файл {output_path} успешно создан!')

# CRD Parser Functions
def parse_xyz_coordinates(xyz_line):
    """Parse X, Y, Z coordinates from APPROX POSITION XYZ line"""
    if xyz_line == '-':
        return '0.00000', '0.00000', '0.00000'
    
    x = xyz_line[2:15].strip()
    y = xyz_line[16:29].strip()
    z = xyz_line[30:43].strip()
    
    try:
        x = f"{float(x):.5f}"
        y = f"{float(y):.5f}"
        z = f"{float(z):.5f}"
    except ValueError:
        x = y = z = '0.00000'
    
    return x, y, z

def format_crd_line(num, station_id, x, y, z):
    """Format a line for the CRD file according to the template"""
    station_name = station_id[:4]
    station_number = station_id[4:]
    
    numeric_part = ''.join(filter(str.isdigit, station_number))
    formatted_number = f"{int(numeric_part):3d}" if numeric_part else "  0"
    
    return (
        f"{num:3d}  "
        f"{station_name} {formatted_number}     "
        f"{x:>14} "
        f"{y:>14} "
        f"{z:>14} "
        f"{'I':>3}"
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
        for i, station in enumerate(stations, 1):
            station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
            x, y, z = parse_xyz_coordinates(station.xyz)
            line = format_crd_line(i, station_id, x, y, z)
            f.write(line + '\n')
    
    print(f'Файл {output_path} успешно создан!')

# PLD Parser Functions
def format_pld_line(num, station_id, plate_name):
    """Format a line for the PLD file according to the template"""
    station_name = station_id[:4]
    station_number = station_id[4:]
    
    line = (
        f"{num:3d} "
        f"{station_name} {station_number:<9}"
        f"{' ' * 13}"
        f"{' ' * 13}"
        f"{' ' * 13}"
        f"{' ' * 4}"
    )
    
    line = line.ljust(75)
    line += plate_name
    
    return line

def save_pld_file(stations, output_path):
    """Save the PLD file with the formatted station information"""
    plate_name = input("Введите название плиты: ").strip()
    
    header = (
        "Example plate assignement\n"
        "--------------------------------------------------------------------------------\n"
        "LOCAL GEODETIC DATUM: IGS14           \n\n"
        "NUM  STATION NAME           VX (M/Y)       VY (M/Y)       VZ (M/Y)  FLAG   PLATE\n\n"
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        for i, station in enumerate(stations, 1):
            station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
            line = format_pld_line(i, station_id, plate_name)
            f.write(line + '\n')
    
    print(f'Файл {output_path} успешно создан!')

# ABB Parser Functions
def generate_station_id(station_name, station_number):
    """Generate station ID in format: NAME + NUMBER"""
    return f"{station_name[:4].strip()}{station_number[:9].strip()}"

def generate_sequence_id(index):
    """Generate sequence ID in format: 01-99, then 0A-ZZ"""
    if index < 0 or index > 945:
        raise ValueError("Index out of range for sequence ID generation")
    
    if index < 99:
        return f"{index + 1:02d}"
    
    index = index - 99
    first_char = chr(ord('0') + (index // 26)) if index < 26 else chr(ord('A') + ((index - 26) // 26))
    second_char = chr(ord('A') + (index % 26))
    return f"{first_char}{second_char}"

def format_abb_line(station_id, sequence_id, rinex_filename):
    """Format a line for the ABB file according to the template"""
    station_name = station_id[:4]
    station_number = station_id[4:]
    
    return (
        f"{station_name} {station_number:<9}"
        f"{' ' * 11}"
        f"{station_name:<4}"
        f"{' ' * 5}"
        f"{sequence_id:<2}"
        f"{' ' * 5}"
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
        for i, station in enumerate(stations):
            station_id = generate_station_id(station.marker_name, station.marker_number)
            sequence_id = generate_sequence_id(i)
            line = format_abb_line(station_id, sequence_id, station.filename)
            f.write(line + '\n')
    
    print(f'Файл {output_path} успешно создан!')

# STA Parser Functions
def extract_date_from_filename(filename):
    """Extract date from RINEX filename"""
    match = re.search(r'(\d{3})\w*\.(\d{2})[Oo]$', filename)
    if match:
        day_of_year = int(match.group(1))
        year = int(match.group(2))
        year_full = 2000 + year if year < 80 else 1900 + year
        date = datetime.datetime.strptime(f'{year_full} {day_of_year}', '%Y %j').date()
        return date.strftime('%Y-%m-%d')
    return '-'

def date_to_bernese_format(date_str):
    """Convert date to Bernese format"""
    try:
        dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%Y %m %d 00 00 00')
    except Exception:
        return '0000 00 00 00 00 00'

def parse_rec_fields(rec_line):
    """Parse receiver fields"""
    rec_serial = rec_line[0:6].strip()
    rec_type = rec_line[20:40].strip()
    return rec_serial, rec_type

def parse_ant_fields(ant_line):
    """Parse antenna fields"""
    ant_serial = ant_line[0:6].strip()
    ant_type = ant_line[20:40].strip()
    return ant_serial, ant_type

def parse_delta_hen(delta_line):
    """Parse delta H/E/N values"""
    up = delta_line[8:15].strip()
    east = delta_line[22:29].strip()
    north = delta_line[36:43].strip()
    return up, east, north

def get_combined_periods(stations):
    """Combine station periods"""
    from collections import defaultdict
    station_data = defaultdict(list)
    
    for st in stations:
        station_key = (st.marker_name[:4].strip(), st.marker_number[:9].strip())
        from_date_str = extract_date_from_filename(st.filename)
        if from_date_str != '-':
            from_date = datetime.datetime.strptime(from_date_str, '%Y-%m-%d').date()
            station_data[station_key].append({
                'station_info': st,
                'from_date': from_date,
                'filename': st.filename
            })

    combined_periods = []
    for key, data_list in station_data.items():
        if not data_list:
            continue
        
        min_from_date_obj = min(data_list, key=lambda x: x['from_date'])['from_date']
        max_from_date_obj = max(data_list, key=lambda x: x['from_date'])['from_date']
        max_to_date_obj = max_from_date_obj + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)

        representative_station = min(data_list, key=lambda x: x['from_date'])['station_info']

        combined_periods.append({
            'station_info': representative_station,
            'from_date': min_from_date_obj.strftime('%Y-%m-%d'),
            'to_date': max_to_date_obj.strftime('%Y-%m-%d'),
            'remark_filename': representative_station.filename
        })
    
    combined_periods.sort(key=lambda x: (x['station_info'].marker_name, x['station_info'].marker_number))
    return combined_periods

def format_sta_type_001(station_data):
    """Format STA type 001 line"""
    st = station_data['station_info']
    from_date = station_data['from_date']
    to_date = station_data['to_date']
    remark_filename = station_data['remark_filename']
    
    name = st.marker_name[:4].strip()
    number = st.marker_number[:9].strip()
    station_id = f'{name} {number}'
    flg = '001'
    from_date_fmt = date_to_bernese_format(from_date)
    to_date_fmt = date_to_bernese_format(to_date)
    old_station_name = f'{name}*'
    remark = f'From {remark_filename}'
    return (
        f'{station_id:<13}' + ' '*8 +
        f'{flg:<3}' + '  ' +
        f'{from_date_fmt:<17}' + '  ' +
        f'{to_date_fmt:<17}' + '  ' +
        f'{old_station_name:<20}' + '  ' +
        f'{remark:<24}'
    )

def format_sta_type_002(station_data):
    """Format STA type 002 line"""
    st = station_data['station_info']
    from_date = station_data['from_date']
    to_date = station_data['to_date']
    remark_filename = station_data['remark_filename']
    
    name = st.marker_name[:4].strip()
    number = st.marker_number[:9].strip()
    station_id = f'{name} {number}'
    flg = '001'
    from_date_fmt = date_to_bernese_format(from_date)
    to_date_fmt = date_to_bernese_format(to_date)
    rec_serial, rec_type = parse_rec_fields(st.receiver)
    ant_serial, ant_type = parse_ant_fields(st.antenna)
    up, east, north = parse_delta_hen(st.delta_hen)
    description = f'{name} {number}'
    remark = f'From {remark_filename}'
    return (
        f'{station_id:<13}' + ' '*8 +
        f'{flg:<3}' + '  ' +
        f'{from_date_fmt:<17}' + '  ' +
        f'{to_date_fmt:<17}' + '  ' +
        f'{rec_type:<22}' +
        f'{rec_serial:<22}' +
        f'{rec_serial:<8}' +
        f'{ant_type:<22}' +
        f'{ant_serial:<22}' +
        f'{ant_serial:<6}' + '  ' +
        f'{north:>8}' + '  ' +
        f'{east:>8}' + '  ' +
        f'{up:>8}' + '  ' +
        f'{description:<24}' +
        f'{remark:<24}'
    )

def save_sta_file(combined_periods, output_path):
    """Save the STA file with the formatted station information"""
    header = (
        'Station information file\n'
        '--------------------------------------------------------------------------------\n\n'
        'FORMAT VERSION: 1.01\n'
        'TECHNIQUE:      GNSS\n\n'
        'TYPE 001: RENAMING OF STATIONS\n'
        '--------------------------------------\n\n'
        'STATION NAME          FLG          FROM                   TO         OLD STATION NAME      REMARK\n'
    )
    type2_header = (
        '\nTYPE 002: STATION INFORMATION\n'
        '--------------------------------------\n\n'
        'STATION NAME          FLG          FROM                   TO         RECEIVER TYPE         RECEIVER SERIAL NBR   REC #   ANTENNA TYPE          ANTENNA SERIAL NBR    ANT #    NORTH      EAST      UP      DESCRIPTION             REMARK\n'
    )
    type3 = (
        '\n\nTYPE 003: HANDLING OF STATION PROBLEMS\n'
        '--------------------------------------\n\n'
        'STATION NAME          FLG          FROM                   TO         REMARK\n'
        '****************      ***  YYYY MM DD HH MM SS  YYYY MM DD HH MM SS  ************************************************************\n'
    )
    type4 = (
        '\n\nTYPE 004: STATION COORDINATES AND VELOCITIES (ADDNEQ)\n'
        '--------------------------------------\n'
        '                                            RELATIVE CONSTR. POSITION     RELATIVE CONSTR. VELOCITY\n'
        'STATION NAME 1        STATION NAME 2        NORTH     EAST      UP        NORTH     EAST      UP\n'
        '****************      ****************      **.*****  **.*****  **.*****  **.*****  **.*****  **.*****\n'
    )
    type5 = (
        '\n\nTYPE 005: HANDLING STATION TYPES\n'
        '--------------------------------------\n\n'
        'STATION NAME          FLG  FROM                 TO                   MARKER TYPE           REMARK\n'
        '****************      ***  YYYY MM DD HH MM SS  YYYY MM DD HH MM SS  ********************  ************************\n'
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        for item in combined_periods:
            f.write(format_sta_type_001(item) + '\n')
        f.write(type2_header)
        for item in combined_periods:
            f.write(format_sta_type_002(item) + '\n')
        f.write(type3)
        f.write(type4)
        f.write(type5)
    
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
    
    # Get combined periods for STA file
    combined_periods = get_combined_periods(stations)
    print(f'Сформировано {len(combined_periods)} уникальных записей станций с объединенными периодами.')
    
    # Save all files
    save_clu_file(stations, '2025_05_22-Задание на практику/2025.CLU')
    save_crd_file(stations, '2025_05_22-Задание на практику/2025.CRD')
    save_pld_file(stations, '2025_05_22-Задание на практику/2025.PLD')
    save_abb_file(stations, '2025_05_22-Задание на практику/2025.ABB')
    save_sta_file(combined_periods, '2025_05_22-Задание на практику/2025.STA')

if __name__ == '__main__':
    main() 