import csv
import re



def get_table_rows(table):
    """Given a table, returns all its rows"""
    rows = []
#    assert "Hele landet" == table.xpath(".//tr")[0].xpath('.//td')[NATIONAL_COLUMN].text_content().strip()
    for tr in table.xpath(".//tr")[1:]:
        cells = []
        # grab all td tags in this table row
        tds = tr.xpath(".//td")
        if len(tds) == 0:
            # if no td tags, search for th tags
            # can be found especially in wikipedia tables below the table
            ths = tr.xpath(".//th")
            for th in ths:
                cells.append(th.text_content().strip())
        else:
            # use regular td tags
            for td in tds:
                cells.append(td.text_content().strip())
        date_match = re.compile(DATE_REGEXP).match(cells[0])
        if not date_match:
            continue
        monthday = int(date_match.groups()[0])
        month = ['januar', 'februar', 'marts', 'april', 'maj', 'juni', 'juli'].index(date_match.groups()[1]) + 1
        cells[0] = f"2020-{month:02}-{monthday:02}"
        rows.append(cells)
    return rows


def sanitise_number(cell: str):
    if not cell:
        return None
    else:
        content = cell.replace('✱', '')
        if content == '':
            return 0
        else:
            return int(content.replace('.', ''))

def save_as_csv(table_name, headers, rows):
    with open("../" + table_name + '.csv', mode='w') as data_file:
        data_writer = csv.writer(data_file, lineterminator='\n', delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        data_writer.writerow(headers)
        for row in rows:
            assert len(row) == len(headers)
            data_writer.writerow(row)


def load_csv(table_name, skip_last = False):
    with open('../' + table_name + '.csv', mode='r') as csvDataFile:
        csvReader = csv.reader(csvDataFile, lineterminator='\n')
        rows = list(csvReader)
    headers = rows[0]
    data = dict()
    data_rows = rows[1:-1] if skip_last else rows[1:]
    for row in data_rows:
        assert row[0] not in data, f"Date {row[0]} already exists in {table_name}.csv"
        data[row[0]] = dict()
        for c in range(len(headers)):
            data[row[0]][headers[c]] = row[c]
    # pprint(data)
    # print(repr(data))
    return headers, data


def generate_national_table():
    tests_header, tests = load_csv('sst-raw-data-tests', True)
    hospitalised_header, hospitalised = load_csv('sst-raw-data-hospitalised')
    icu_header, icu = load_csv('sst-raw-data-icu')
    icu_vent_header, icu_vent = load_csv('sst-raw-data-icu_vent')
    deaths_header, deaths = load_csv('ssi-pdf-data-deaths', True)

    dates = set()
    dates.update(tests.keys())
    dates.update(hospitalised.keys())
    dates.update(icu.keys())
    dates.update(icu_vent.keys())
    dates.update(deaths.keys())

    sorted_dates = sorted(dates)
    rows = []
    headers = ['Date', 'Tested', 'Total tested', 'Confirmed', 'Total confirmed', 'Hospitalised', 'ICU', 'ICU-vent', 'Deaths', 'Total deaths']
    total_tested = 0
    total_confirmed = 0
    total_deaths = 0
    for date in sorted_dates:
        total_tested += sanitise_number(tests[date]['Testede for COVID-19']) if date in tests else 0
        total_confirmed += sanitise_number(tests[date]['Bekræftede COVID-19 smittede']) if date in tests else 0
        total_deaths += sanitise_number(deaths[date]['Antal dødsfald med COVID-19 infektion']) if date in deaths else 0
        row = [date,
               sanitise_number(tests[date]['Testede for COVID-19']) if date in tests else None,
               total_tested if date in tests else None,
               sanitise_number(tests[date]['Bekræftede COVID-19 smittede']) if date in tests else None,
               total_confirmed if date in tests else None,
               sanitise_number(hospitalised[date]['Hele landet']) if date in hospitalised else None,
               sanitise_number(icu[date]['Hele landet']) if date in icu else None,
               sanitise_number(icu_vent[date]['Hele landet']) if date in icu_vent else None,
               sanitise_number(deaths[date]['Antal dødsfald med COVID-19 infektion']) if date in deaths else None,
               total_deaths if date in deaths else None,
               ]
        rows.append(row)
    save_as_csv('total-covid-19-dk', headers, rows)

generate_national_table()
