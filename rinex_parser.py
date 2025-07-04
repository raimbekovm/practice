import os
import re
import datetime
import numpy as np

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
    def __init__(self, marker_name, marker_number, receiver, antenna, xyz, delta_hen, filename, header):
        self.marker_name = marker_name
        self.marker_number = marker_number
        self.receiver = receiver
        self.antenna = antenna
        self.xyz = xyz
        self.delta_hen = delta_hen
        self.filename = filename
        self.header = header

# Common utility functions
def find_rinex_files(input_dir):
    """Find all RINEX files in the input directory"""
    rinex_files = []
    for root, dirs, files in os.walk(input_dir):
        for f in files:
            if f.endswith('O') or f.endswith('o'):
                full_path = os.path.join(root, f)
                rinex_files.append(full_path)
    return rinex_files

def parse_rinex_header(filepath):
    """Parse RINEX header"""
    header = {}
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if 'END OF HEADER' in line:
                    break
                for field in HEADER_FIELDS:
                    if field in line:
                        header[field] = line.rstrip('\n')
                        break
                if 'TIME OF FIRST OBS' in line:
                    header['TIME OF FIRST OBS'] = line.rstrip('\n')
                if 'TIME OF LAST OBS' in line:
                    header['TIME OF LAST OBS'] = line.rstrip('\n')
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
    return header

def extract_obs_time(line):
    """Extract time from TIME OF FIRST/LAST OBS line"""
    if not line:
        return '0000 00 00 00 00 00'
    try:
        year = line[2:6].strip()
        month = line[11:13].strip().zfill(2)
        day = line[16:18].strip().zfill(2)
        hour = line[22:24].strip().zfill(2)
        minute = line[28:30].strip().zfill(2)
        second = line[34:35].strip().zfill(2)
        return f"{year} {month} {day} {hour} {minute} {second}"
    except Exception:
        return '0000 00 00 00 00 00'

def extract_station_info(header, filename):
    """Extract station information from header"""
    marker_name = header.get('MARKER NAME', '-')
    marker_number = header.get('MARKER NUMBER', '-')
    receiver = header.get('REC # / TYPE / VERS', '-')
    antenna = header.get('ANT # / TYPE', '-')
    xyz = header.get('APPROX POSITION XYZ', '-')
    delta_hen = header.get('ANTENNA: DELTA H/E/N', '-')
    
    # Ensure marker number is exactly 9 characters
    if marker_number != '-':
        marker_number = marker_number[:9].ljust(9)
    
    # Special handling for AAC4 station
    if marker_name.strip() == 'AAC4':
        marker_number = 'AACH'.ljust(9)
    
    return StationInfo(marker_name, marker_number, receiver, antenna, xyz, delta_hen, filename, header)

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
    
    # Create a set to track unique station IDs
    seen_stations = set()
    unique_stations = []
    
    for station in stations:
        station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
        if station_id not in seen_stations:
            seen_stations.add(station_id)
            unique_stations.append(station)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        for station in unique_stations:
            station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
            line = format_clu_line(station_id)
            f.write(line + '\n')

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
    
    # Format the station number to be left-aligned in 9 characters
    formatted_number = station_number.ljust(9)
    
    return (
        f"{num:3d}  "
        f"{station_name} {formatted_number}   "
        f"{x:>14} "
        f"{y:>14} "
        f"{z:>14}   "
        f"{'I':>2}"
    )

def save_crd_file(stations, output_path):
    """Save the CRD file with the formatted station information"""
    header = (
        "PPP_210940: Collecting results                                   06-MAY-25 12:25\n"
        "--------------------------------------------------------------------------------\n"
        "LOCAL GEODETIC DATUM: IGS20             EPOCH: 2025-03-01 00:00:00\n\n"
        "NUM  STATION NAME           X (M)          Y (M)          Z (M)     FLAG\n\n"
    )
    
    # Create a dictionary to track unique stations with their creation times
    station_dict = {}
    
    for station in stations:
        station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
        file_path = os.path.join(INPUT_DIR, station.filename)
        
        try:
            # Get file creation time
            creation_time = os.path.getctime(file_path)
            
            # If station not in dict or current file is newer, update the entry
            if station_id not in station_dict or creation_time > station_dict[station_id]['time']:
                station_dict[station_id] = {
                    'station': station,
                    'time': creation_time
                }
        except Exception:
            # If we can't get creation time, keep the station anyway
            if station_id not in station_dict:
                station_dict[station_id] = {
                    'station': station,
                    'time': 0
                }
    
    # Sort stations by name and number
    sorted_stations = sorted(station_dict.values(), 
                           key=lambda x: (x['station'].marker_name, x['station'].marker_number))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        for i, station_data in enumerate(sorted_stations, 1):
            station = station_data['station']
            station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
            x, y, z = parse_xyz_coordinates(station.xyz)
            line = format_crd_line(i, station_id, x, y, z)
            f.write(line + '\n')

# PLD Parser Functions
def format_pld_line(num, station_id, plate_name):
    """Format a line for the PLD file according to the template"""
    station_name = station_id[:4]
    station_number = station_id[4:]
    
    line = (
        f"{num:3d}  "
        f"{station_name} {station_number:<9}"
        f"{' ' * 13}"
        f"{' ' * 13}"
        f"{' ' * 13}"
        f"{' ' * 4}"
    )
    
    line = line.ljust(75)
    line += plate_name
    
    return line

def save_pld_file(stations, output_path, plate_name):
    """Save the PLD file with the formatted station information"""
    header = (
        "Example plate assignement\n"
        "--------------------------------------------------------------------------------\n"
        "LOCAL GEODETIC DATUM: IGS14           \n\n"
        "NUM  STATION NAME           VX (M/Y)       VY (M/Y)       VZ (M/Y)  FLAG   PLATE\n\n"
    )
    
    # Create a set to track unique station IDs
    seen_stations = set()
    unique_stations = []
    
    for station in stations:
        station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
        if station_id not in seen_stations:
            seen_stations.add(station_id)
            unique_stations.append(station)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        for i, station in enumerate(unique_stations, 1):
            station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
            line = format_pld_line(i, station_id, plate_name)
            f.write(line + '\n')

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
    
    # Create a set to track unique station IDs
    seen_stations = set()
    unique_stations = []
    
    for station in stations:
        station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
        if station_id not in seen_stations:
            seen_stations.add(station_id)
            unique_stations.append(station)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        for i, station in enumerate(unique_stations):
            station_id = generate_station_id(station.marker_name, station.marker_number)
            sequence_id = generate_sequence_id(i)
            line = format_abb_line(station_id, sequence_id, station.filename)
            f.write(line + '\n')

# STA Parser Functions
def extract_date_from_filename(filename):
    """Extract date from RINEX filename"""
    # Handle different year formats (2-digit and 4-digit)
    match = re.search(r'(\d{3})\w*\.(\d{2,4})[Oo]$', filename)
    if match:
        day_of_year = int(match.group(1))
        year = int(match.group(2))
        
        # Handle 2-digit year
        if year < 100:
            year_full = 2000 + year if year < 80 else 1900 + year
        else:
            year_full = year
            
        try:
            date = datetime.datetime.strptime(f'{year_full} {day_of_year}', '%Y %j').date()
            return date.strftime('%Y-%m-%d')
        except ValueError:
            return '2005-01-01'
    return '2005-01-01'

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
        try:
            from_date = datetime.datetime.strptime(from_date_str, '%Y-%m-%d').date()
            station_data[station_key].append({
                'station_info': st,
                'from_date': from_date,
                'filename': st.filename
            })
        except ValueError as e:
            print(f"Warning: Could not parse date for station {st.marker_name} from file {st.filename}: {e}")
            # Use default date for files with incorrect dates
            from_date = datetime.datetime.strptime('2005-01-01', '%Y-%m-%d').date()
            station_data[station_key].append({
                'station_info': st,
                'from_date': from_date,
                'filename': st.filename
            })

    combined_periods = []
    for key, data_list in station_data.items():
        if not data_list:
            continue
        
        try:
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
        except Exception as e:
            print(f"Warning: Error processing station {key}: {e}")
            continue
    
    combined_periods.sort(key=lambda x: (x['station_info'].marker_name, x['station_info'].marker_number))
    return combined_periods

def format_sta_type_001(station_data):
    """Format STA type 001 line"""
    st = station_data['station_info']
    from_date = extract_obs_time(st.header.get('TIME OF FIRST OBS', ''))
    to_date = extract_obs_time(st.header.get('TIME OF LAST OBS', ''))
    remark_filename = station_data['remark_filename']
    
    name = st.marker_name[:4].strip()
    number = st.marker_number[:9]  # Already padded to 9 chars in extract_station_info
    station_id = f'{name} {number}'
    flg = '001'
    old_station_name = f'{name}*'
    remark = f'From {remark_filename}'
    
    # Format with exact spacing
    return (
        f'{station_id:<20}' + '  ' # Station name (20 chars)
        f'{flg:<3}' + '  ' +  # Flag (3 chars) + 2 spaces
        f'{from_date:<17}' + '  ' +  # From date (17 chars) + 2 spaces
        f'{to_date:<17}' + '  ' +  # To date (17 chars) + 2 spaces
        f'{old_station_name:<20}' + '  ' +  # Old station name (20 chars) + 2 spaces
        f'{remark:<24}'  # Remark (24 chars)
    )

def format_sta_type_002(station_data):
    """Format STA type 002 line"""
    st = station_data['station_info']
    from_date = extract_obs_time(st.header.get('TIME OF FIRST OBS', ''))
    to_date = extract_obs_time(st.header.get('TIME OF LAST OBS', ''))
    remark_filename = station_data['remark_filename']
    
    name = st.marker_name[:4].strip()
    number = st.marker_number[:9]  # Already padded to 9 chars in extract_station_info
    station_id = f'{name} {number}'
    flg = '001'
    rec_serial, rec_type = parse_rec_fields(st.receiver)
    ant_serial, ant_type = parse_ant_fields(st.antenna)
    up, east, north = parse_delta_hen(st.delta_hen)
    description = f'{name} {number}'
    remark = f'From {remark_filename}'
    
    # Format with exact spacing
    return (
        f'{station_id:<20}' + '  ' +  # Station name (20 chars) + 2 spaces
        f'{flg:<3}' + '  ' +  # Flag (3 chars) + 2 spaces
        f'{from_date:<17}' + '  ' +  # From date (17 chars) + 2 spaces
        f'{to_date:<17}' + '  ' +  # To date (17 chars) + 2 spaces
        f'{rec_type:<22}' +  # Receiver type (22 chars)
        f'{rec_serial:<22}' +  # Receiver serial (22 chars)
        f'{rec_serial:<8}' +  # REC # (8 chars)
        f'{ant_type:<22}' +  # Antenna type (22 chars)
        f'{ant_serial:<22}' +  # Antenna serial (22 chars)
        f'{ant_serial:<6}' + ' ' +  # ANT # (6 chars) + 2 spaces
        f'{north:>8}' + '   ' +  # North (8 chars) + 2 spaces
        f'{east:>8}' + '  ' +  # East (8 chars) + 2 spaces
        f'{up:>8}' + '  ' +  # Up (8 chars) + 2 spaces
        f'{description:<24}' +  # Description (24 chars)
        f'{remark:<24}'  # Remark (24 chars)
    )

def get_type002_periods(stations):
    """
    Для каждой станции разбить периоды по уникальным комбинациям (RECEIVER TYPE, ANTENNA TYPE).
    Период определяется по min/max дню из имени файла (3 цифры и год после точки),
    часы/мин/сек из TIME OF FIRST/LAST OBS.
    """
    from collections import defaultdict
    import re
    station_data = defaultdict(list)
    for st in stations:
        station_name = st.marker_name[:4].strip()
        rec_serial, rec_type = parse_rec_fields(st.receiver)
        ant_serial, ant_type = parse_ant_fields(st.antenna)
        key = (station_name, rec_type, ant_type)
        # Парсим день и год из имени файла
        m = re.search(r'(\d{4})(\d{3})\.(\d{2})[Oo]', st.filename)
        if m:
            # Например: CHUM001.02O -> day=001, year=02
            day_of_year = int(m.group(2))
            year = 2000 + int(m.group(3))
        else:
            # fallback: используем extract_date_from_filename
            day_of_year = 1
            year = 2000
        station_data[key].append({
            'station_info': st,
            'day_of_year': day_of_year,
            'year': year,
            'filename': st.filename
        })
    type002_periods = []
    for key, data_list in station_data.items():
        if not data_list:
            continue
        # Сортируем по году и дню
        data_list.sort(key=lambda x: (x['year'], x['day_of_year']))
        # Первый и последний файл в группе
        first = data_list[0]
        last = data_list[-1]
        # FROM: year, day_of_year, часы/мин/сек из TIME OF FIRST OBS
        st_first = first['station_info']
        st_last = last['station_info']
        # Получаем дату из года и дня
        from_date = datetime.datetime.strptime(f"{first['year']} {first['day_of_year']}", "%Y %j")
        to_date = datetime.datetime.strptime(f"{last['year']} {last['day_of_year']}", "%Y %j")
        # Часы/мин/сек из TIME OF FIRST/LAST OBS
        from_time = extract_obs_time(st_first.header.get('TIME OF FIRST OBS', ''))
        to_time = extract_obs_time(st_last.header.get('TIME OF LAST OBS', ''))
        # Подставляем часы/мин/сек
        from_date_str = f"{from_date.year} {from_date.month:02d} {from_date.day:02d} " + ' '.join(from_time.split()[3:])
        to_date_str = f"{to_date.year} {to_date.month:02d} {to_date.day:02d} " + ' '.join(to_time.split()[3:])
        period = {
            'station_info': st_first,
            'from_date': from_date_str,
            'to_date': to_date_str,
            'remark_filename': first['filename']
        }
        type002_periods.append(period)
    # Сортируем итоговый список по STATION NAME для последовательности в файле
    type002_periods.sort(key=lambda x: (x['station_info'].marker_name, x['station_info'].marker_number, x['from_date']))
    return type002_periods

def save_sta_file(combined_periods, output_path, stations=None):
    """Save the STA file with the formatted station information"""
    header = (
        'STATION INFORMATION FILE                                         03-JAN-24 22:57\n'
        '--------------------------------------------------------------------------------\n\n'
        'FORMAT VERSION: 1.01\n'
        'TECHNIQUE:      GNSS\n\n'
        'TYPE 001: RENAMING OF STATIONS\n'
        '------------------------------\n\n'
        'STATION NAME          FLG          FROM                   TO         OLD STATION NAME      REMARK\n'
        '****************      ***  YYYY MM DD HH MM SS  YYYY MM DD HH MM SS  ********************  ************************\n'
    )
    type2_header = (
        '\n\nTYPE 002: STATION INFORMATION\n'
        '--------------------------------------\n\n'
        'STATION NAME          FLG          FROM                   TO         RECEIVER TYPE         RECEIVER SERIAL NBR   REC #   ANTENNA TYPE          ANTENNA SERIAL NBR    ANT #    NORTH      EAST      UP      DESCRIPTION             REMARK\n'
        '****************      ***  YYYY MM DD HH MM SS  YYYY MM DD HH MM SS  ********************  ********************  ******  ********************  ********************  ******  ***.****  ***.****  ***.****  **********************  ************************\n'
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
        # TYPE 002: используем periods по receiver/antenna
        if stations is not None:
            type002_periods = get_type002_periods(stations)
            for item in type002_periods:
                f.write(format_sta_type_002(item) + '\n')
        else:
            for item in combined_periods:
                f.write(format_sta_type_002(item) + '\n')
        f.write(type3)
        f.write(type4)
        f.write(type5)

def parse_xyz_coordinates_float(xyz_line):
    """Parse X, Y, Z coordinates from APPROX POSITION XYZ line as floats"""
    if xyz_line == '-':
        return 0.0, 0.0, 0.0
    x = xyz_line[2:15].strip()
    y = xyz_line[16:29].strip()
    z = xyz_line[30:43].strip()
    try:
        x = float(x)
        y = float(y)
        z = float(z)
    except ValueError:
        x = y = z = 0.0
    return x, y, z

def format_vel_line(num, station_id, vx, vy, vz, plate_name):
    """Format a line for the VEL file with velocities"""
    station_name = station_id[:4]
    station_number = station_id[4:]
    if num < 10:
        num_str = f"  {num}"
    else:
        num_str = f" {num}"
    return (
        f"{num_str}  "
        f"{station_name} {station_number:<9}    "
        f"{vx:13.5f}  "
        f"{vy:13.5f}  "
        f"{vz:13.5f}    "
        f"{'V'}    "   # FLAG space
        f"{plate_name}"
    )

def save_vel_file(stations, output_path, plate_name):
    """Save the VEL file with calculated velocities"""
    header = (
        "NUVEL1A-NNR VELOCITIES                                           14-DEC-23 19:25\n"
        "--------------------------------------------------------------------------------\n"
        "LOCAL GEODETIC DATUM: IGS14           \n\n"
        "NUM  STATION NAME           VX (M/Y)       VY (M/Y)       VZ (M/Y)  FLAG   PLATE\n\n"
    )
    omega = np.array([-4.128e-10, -2.516e-9, 3.648e-9])  # rad/year
    seen_stations = set()
    unique_stations = []
    for station in stations:
        station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
        if station_id not in seen_stations:
            seen_stations.add(station_id)
            unique_stations.append(station)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        for i, station in enumerate(unique_stations, 1):
            station_id = f"{station.marker_name[:4].strip()}{station.marker_number[:9].strip()}"
            x, y, z = parse_xyz_coordinates_float(station.xyz)
            r = np.array([x, y, z])
            v = np.cross(omega, r)  # [m/year]
            vx, vy, vz = v
            line = format_vel_line(i, station_id, vx, vy, vz, plate_name)
            f.write(line + '\n')

def main():
    base_name = input("Введите имя для выходных файлов: ").strip()
    plate_name = input("Введите название плиты: ").strip()
    
    files = find_rinex_files(INPUT_DIR)
    
    stations = []
    for file in files:
        try:
            header = parse_rinex_header(file)
            station = extract_station_info(header, os.path.basename(file))
            stations.append(station)
        except Exception as e:
            print(f'Ошибка при обработке файла {file}: {str(e)}')
    
    combined_periods = get_combined_periods(stations)
    
    try:
        save_clu_file(stations, f'2025_05_22-Задание на практику/{base_name}.CLU')
        save_crd_file(stations, f'2025_05_22-Задание на практику/{base_name}.CRD')
        save_pld_file(stations, f'2025_05_22-Задание на практику/{base_name}.PLD', plate_name)
        save_abb_file(stations, f'2025_05_22-Задание на практику/{base_name}.ABB')
        save_sta_file(combined_periods, f'2025_05_22-Задание на практику/{base_name}.STA', stations)
        save_vel_file(stations, f'2025_05_22-Задание на практику/{base_name}.VEL', plate_name)
    except Exception as e:
        print(f'Ошибка при сохранении файлов: {str(e)}')

if __name__ == '__main__':
    main() 