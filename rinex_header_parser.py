import os
import re
import datetime

INPUT_DIR = '2025_05_22-Задание на практику/Образец/input'
RINEX_EXTENSIONS = ('.O', '.o')

# Какие поля будем искать в заголовке
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
        self.filename = filename  # для извлечения даты

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

def yd_to_ymd(day_of_year, year):
    # Проверка на високосный год
    is_leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    DM = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
    if is_leap:
        for i in range(2, len(DM)):
            DM[i] += 1
    for month in range(1, len(DM)):
        if day_of_year <= DM[month]:
            day = day_of_year - DM[month - 1]
            return f"{year:04d} {month:02d} {day:02d} 00 00 00"
    return "0000 00 00 00 00 00"

def extract_date_from_filename(filename):
    # Пример: CHUM0010.02O -> день года (001), год (02)
    import re
    match = re.search(r'(\d{3})\w*\.(\d{2})[Oo]$', filename)
    if match:
        day_of_year = int(match.group(1))
        year = int(match.group(2))
        year_full = 2000 + year if year < 80 else 1900 + year
        return yd_to_ymd(day_of_year, year_full)
    return '0000 00 00 00 00 00'

def date_to_bernese_format(date_str):
    # Если дата уже в формате Bernese, возвращаем как есть
    if len(date_str.split()) == 6:
        return date_str
    try:
        dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%Y %m %d 00 00 00')
    except Exception:
        return '0000 00 00 00 00 00'

def parse_rec_fields(rec_line):
    rec_serial = rec_line[0:6].strip()
    rec_type = rec_line[20:40].strip()
    return rec_serial, rec_type

def parse_ant_fields(ant_line):
    ant_serial = ant_line[0:6].strip()
    ant_type = ant_line[20:40].strip()
    return ant_serial, ant_type

def parse_delta_hen(delta_line):
    up = delta_line[8:15].strip()
    east = delta_line[22:29].strip()
    north = delta_line[36:43].strip()
    return up, east, north

def format_sta_type_002(station: StationInfo, from_date, to_date):
    name = station.marker_name[:4].strip()
    number = station.marker_number[:9].strip()
    station_id = f'{name} {number}'
    flg = '001'
    from_date_fmt = date_to_bernese_format(from_date)
    to_date_fmt = date_to_bernese_format(to_date)
    rec_serial, rec_type = parse_rec_fields(station.receiver)
    ant_serial, ant_type = parse_ant_fields(station.antenna)
    up, east, north = parse_delta_hen(station.delta_hen)
    description = f'{name} {number}'
    remark = f'From {name}{number}.SMT'
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

def format_sta_type_001(station: StationInfo, from_date, to_date):
    name = station.marker_name[:4].strip()
    number = station.marker_number[:9].strip()
    station_id = f'{name} {number}'
    flg = '001'
    from_date_fmt = date_to_bernese_format(from_date)
    to_date_fmt = date_to_bernese_format(to_date)
    old_station_name = f'{name}*'
    remark = f'From {name}{number}.SMT'
    return (
        f'{station_id:<13}' + ' '*8 +
        f'{flg:<3}' + '  ' +
        f'{from_date_fmt:<17}' + '  ' +
        f'{to_date_fmt:<17}' + '  ' +
        f'{old_station_name:<20}' + '  ' +
        f'{remark:<24}'
    )

def get_periods(stations):
    # Группируем по станции, сортируем по from_date, формируем пары (from, to)
    from collections import defaultdict
    import operator
    station_groups = defaultdict(list)
    for st in stations:
        from_date = extract_date_from_filename(st.filename)
        station_groups[(st.marker_name[:4].strip(), st.marker_number[:9].strip())].append((st, from_date))
    periods = []
    for group in station_groups.values():
        group_sorted = sorted(group, key=lambda x: x[1])
        for i, (st, from_date) in enumerate(group_sorted):
            if i+1 < len(group_sorted):
                to_date = group_sorted[i+1][1]
            else:
                to_date = '9999-12-31'
            periods.append((st, (from_date, to_date)))
    return periods

def save_sta_file(stations, output_path, periods):
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
        for st, (from_date, to_date) in periods:
            f.write(format_sta_type_001(st, from_date, to_date) + '\n')
        f.write(type2_header)
        for st, (from_date, to_date) in periods:
            f.write(format_sta_type_002(st, from_date, to_date) + '\n')
        f.write(type3)
        f.write(type4)
        f.write(type5)
    print(f'Файл {output_path} успешно создан!')

def main():
    files = find_rinex_files(INPUT_DIR)
    print('Найдено файлов:', len(files))
    for file in files:
        print(' -', file)
    print('=' * 40)
    stations = []
    for file in files:
        header = parse_rinex_header(file)
        station = extract_station_info(header, os.path.basename(file))
        stations.append(station)
    print(f'Собрано информации о {len(stations)} станциях.')
    periods = get_periods(stations)
    save_sta_file(stations, '2025_05_22-Задание на практику/2025.STA', periods)

if __name__ == '__main__':
    main() 