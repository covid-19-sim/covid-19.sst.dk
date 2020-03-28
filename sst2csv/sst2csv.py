import csv

import lxml.html
import re
import urllib.request

DATE_REGEXP = '^(\d+)\. (\w*)$'

URL = 'https://www.sst.dk/da/corona/tal-og-overvaagning'

XPATH_INDLAGT = ' /html/body/div[3]/main/article/div[2]/div/div[20]/div[1]/table'
XPATH_ICU = '     /html/body/div[3]/main/article/div[2]/div/div[20]/div[2]/table'
XPATH_ICU_RESP = '/html/body/div[3]/main/article/div[2]/div/div[20]/div[3]/table'
XPATH_TESTS = '   /html/body/div[3]/main/article/div[2]/div/div[4]/div/table'

DATE_COLUMN = 0
NATIONAL_COLUMN = 6

#CSS_SELECTOR = 'body > div.main__content > main > article > div.o-content-block.u-grid.u-grid--space-between.u-grid--no-gutter.u-ie > div > div:nth-child(33) > div > table'

#USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
# US english
#LANGUAGE = "en-US,en;q=0.5"

def get_soup(url):
    """Constructs and returns a soup using the HTML content of `url` passed"""

    contents = urllib.request.urlopen(URL).read()
#    contents = open('https _www.sst.dk_da_corona_tal-og-overvaagning.html', 'r').read()
    print("File fetched")
    tree = lxml.html.document_fromstring(contents)
    return tree
    # return the soup
    return bs(contents, "html.parser")


# def get_table_headers(table):
#     """Given a table soup, returns all the headers"""
#     headers = []
#     for th in table.find("tr").find_all("th"):
#         headers.append(th.text.strip())
#     return headers


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
            return None
        else:
            return int(content.replace('.', ''))

def merge_rows(hosp_list, icu_list, resp_list):
    """
    This assumes same number of columns, and first column to be date

    Parameters
    ----------
    hosp_list
    icu_list
    resp_list

    Returns
    -------

    """
    assert len(hosp_list) == len(icu_list)
    assert len(hosp_list) == len(resp_list)
    result_rows = []
    for i in range(len(hosp_list)):
        assert hosp_list[i][0] == icu_list[i][0]
        assert hosp_list[i][0] == icu_list[i][0]
        cols = [hosp_list[i][0],
                sanitise_number(hosp_list[i][NATIONAL_COLUMN]),
                sanitise_number(icu_list[i][NATIONAL_COLUMN]),
                sanitise_number(resp_list[i][NATIONAL_COLUMN])
                ]
        result_rows.append(cols)
    return sorted(result_rows, key=lambda r: r[0])


def save_as_csv(table_name, headers, rows):
    with open("../" + table_name + '.csv', mode='w') as data_file:
        data_writer = csv.writer(data_file, lineterminator='\n', delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        data_writer.writerow(headers)
        for row in rows:
            assert len(row) == len(headers)
            data_writer.writerow(row)


def add_early(complete_table):
    with open('sst-covid19-early.csv') as csvDataFile:
        csvReader = csv.reader(csvDataFile, lineterminator='\n')
        early_records = list(csvReader)
        assert len(early_records) == 6
        assert len(early_records[0]) == len(complete_table[0]), f'Number of columns mismatch {len(early_records[0])} != {len(complete_table[0])}'
        for row in early_records[1:]:
            complete_table.append(row)
    return sorted(complete_table, key=lambda r: r[0])


def add_deaths(full_time_table):
    with open('sst-covid19-deaths.csv') as csvDataFile:
        csvReader = csv.reader(csvDataFile, lineterminator='\n')
        death_table = sorted(list(csvReader)[1:], key=lambda r: r[0])
    # Death numbers are true registration by midnight, others numbers are half a day too old registered at noon.
    assert len(death_table) == len(full_time_table)-1, f'Number of rows mismatch {len(death_table)} != {len(full_time_table)-1}'
    death_count = 0
    for i in range(len(full_time_table)-1):
        assert full_time_table[i][0] == death_table[i][0], f"Date mismatch {full_time_table[i][0]} != {death_table[i][0]}"
        death_count += sanitise_number(death_table[i][1])
        full_time_table[i].append(death_count)
    full_time_table[-1].append(None)
    return full_time_table


def add_tests(table):
    tests = [['2020-03-11', None, None, None],
             ['2020-03-12', None, None, None],
             ['2020-03-13', None, None, None],
             ] + get_table_rows(table_test[0])
    tests[-1][1] = None  # Last day is inaccurate
    tests[-1][2] = None  # Last day is inaccurate
    tests[-1][3] = None  # Last day is inaccurate
    assert len(tests) == len(table), f"Tabel length mismath {len(tests)} != {len(table)}"
    result_rows = []
    test_count = 0
    confirmed_count = 0
    for i in range(len(table)):
        assert table[i][0] == tests[i][0], f"Date mismatch {table[i][0]} != {tests[i][0]}"
        day_tests = sanitise_number(tests[i][2])
        if day_tests:
            test_count += day_tests
        day_confirmed = sanitise_number(tests[i][1])
        if day_confirmed:
            confirmed_count += day_confirmed
        table[i] = [table[i][0],  # Date
                    test_count if day_tests else None,  # Tested
                    confirmed_count if day_confirmed else None,  # Infected
                    ] + table[i][1:]
    return table


tree = get_soup(URL)
table_hospital = tree.xpath(XPATH_INDLAGT)
assert len(table_hospital) == 1, len(table_hospital)
table_icu = tree.xpath(XPATH_ICU)
assert len(table_icu) == 1
table_resp = tree.xpath(XPATH_ICU_RESP)
assert len(table_resp) == 1
table_test = tree.xpath(XPATH_TESTS)
assert len(table_resp) == 1

hospital_table = merge_rows(get_table_rows(table_hospital[0]),
                            get_table_rows(table_icu[0]),
                            get_table_rows(table_resp[0])
                            )

full_time_table = add_early(hospital_table)
test_table = add_tests(full_time_table)
full_time_table_death = add_deaths(test_table)

headers = ['Date', 'Tested', 'Confirmed', 'Hospitalised', 'ICU', 'ICU and ventilator', 'Death count']

save_as_csv('covid-19-dk', headers, full_time_table_death)

# def xpath2regex(xpath: str):
#     elems1 = xpath.split('/')
#     elems = []
#     regexp = re.compile('^.*?\[(\d+)\]$')
#     for e in elems1:
#         for repeat = int(regexp.match(e).group(1))
#     regex = '.*?'
#     regex += '.*?'.join(['<' + e + '>' for e in elems])
#     print(regex)
#
# #pandas.read_html('https://www.sst.dk/da/corona/tal-og-overvaagning',)
#
# xpath2regex(XPATH)