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

def extract_date_from_filename(filename):
    # Пример: CHUM0010.02O -> день года (001), год (0.02)
    # Берём 3 цифры после имени станции и 2 цифры года перед 'O'
    import re
    match = re.search(r'(\d{3})\w*\.(\d{2})[Oo]$', filename)
    if match:
        day_of_year = int(match.group(1))
        year = int(match.group(2))
        # Преобразуем в формат YYYY-MM-DD
        year_full = 2000 + year if year < 80 else 1900 + year
        date = datetime.datetime.strptime(f'{year_full} {day_of_year}', '%Y %j').date()
        return date.strftime('%Y-%m-%d')
    return '-'

def date_to_bernese_format(date_str):
    # Преобразует YYYY-MM-DD в YYYY MM DD 00 00 00
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

def get_combined_periods(stations):
    # Группируем по станции, находим min FROM и max TO, выбираем один StationInfo
    from collections import defaultdict
    import datetime
    station_data = defaultdict(list)
    for st in stations:
        # Используем комбинацию имени и номера как уникальный ID станции
        station_key = (st.marker_name[:4].strip(), st.marker_number[:9].strip())
        from_date_str = extract_date_from_filename(st.filename)
        if from_date_str != '-':
             # Преобразуем дату в объект datetime для сравнения
            from_date = datetime.datetime.strptime(from_date_str, '%Y-%m-%d').date()
            station_data[station_key].append({
                'station_info': st,
                'from_date': from_date,
                'filename': st.filename # Сохраняем имя файла для REMARK
            })

    combined_periods = []
    for key, data_list in station_data.items():
        if not data_list: # Пропускаем пустые группы
            continue
        
        # Находим самую раннюю дату начала
        min_from_date_obj = min(data_list, key=lambda x: x['from_date'])['from_date']
        # Находим самую позднюю дату (для TO берем дату из файла и прибавляем 1 день минус 1 секунду)
        # Если нужно ТОЧНОЕ время из TIME OF LAST OBS, потребуется парсить его тоже
        # Сейчас берем FROM самой поздней даты и считаем ТО концом этого дня
        max_from_date_obj = max(data_list, key=lambda x: x['from_date'])['from_date']
        max_to_date_obj = max_from_date_obj + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)

        # Выбираем StationInfo объект для представления станции (например, с самой ранней датой)
        representative_station = min(data_list, key=lambda x: x['from_date'])['station_info']

        combined_periods.append({
            'station_info': representative_station,
            'from_date': min_from_date_obj.strftime('%Y-%m-%d'),
            'to_date': max_to_date_obj.strftime('%Y-%m-%d'), # Преобразуем обратно в строку YYYY-MM-DD
            'remark_filename': representative_station.filename # Имя файла для REMARK
        })
        
    # Сортируем итоговый список по STATION NAME для последовательности в файле
    combined_periods.sort(key=lambda x: (x['station_info'].marker_name, x['station_info'].marker_number))
    
    return combined_periods

def format_sta_type_001(station_data):
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
    print(f'Собрано информации о {len(stations)} записях из файлов.')
    
    combined_periods = get_combined_periods(stations)
    print(f'Сформировано {len(combined_periods)} уникальных записей станций с объединенными периодами.')

    save_sta_file(combined_periods, '2025_05_22-Задание на практику/2025.STA')

if __name__ == '__main__':
    main() 