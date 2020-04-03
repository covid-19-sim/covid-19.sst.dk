import csv

import lxml.html
import re
import urllib.request

DATE_REGEXP = '^(\\d+)\\. (\\w*)$'

SOURCE_URL = 'https://www.sst.dk/da/corona/tal-og-overvaagning'
XPATH_HOSPITALISED = ' /html/body/div[3]/main/article/div[2]/div/div[20]/div[1]/table'
XPATH_ICU = '     /html/body/div[3]/main/article/div[2]/div/div[20]/div[2]/table'
XPATH_ICU_VENT = '/html/body/div[3]/main/article/div[2]/div/div[20]/div[3]/table'
XPATH_TESTS = '   /html/body/div[3]/main/article/div[2]/div/div[4]/div/table'


def save_as_csv(table_name, headers, rows):
    with open("../" + table_name + '.csv', mode='w') as data_file:
        data_writer = csv.writer(data_file, lineterminator='\n', delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        data_writer.writerow(headers)
        for row in rows:
            assert len(row) == len(headers)
            data_writer.writerow(row)

def update_csv(table_name, headers, new_rows):
    with open('../' + table_name + '.csv', mode='r') as csvDataFile:
        csvReader = csv.reader(csvDataFile, lineterminator='\n')
        cur_rows = list(csvReader)
        cur_data_rows = sorted(cur_rows[1:], key=lambda r: r[0])
        assert headers == cur_rows[0]
        cur_row = 0
        new_row = 0
        while cur_row < len(cur_data_rows) and new_row < len(new_rows):
            assert len(cur_data_rows[cur_row]) == len(cur_rows[0])
            assert len(new_rows[new_row]) == len(headers)
            if cur_data_rows[cur_row][0] < new_rows[new_row][0]:
                cur_row += 1
                continue
            elif cur_data_rows[cur_row][0] > new_rows[new_row][0]:
                new_row += 1
                continue
            else:
                assert cur_data_rows[cur_row][0] == new_rows[new_row][0]
                for c in range(len(headers)):
                    if cur_data_rows[cur_row][c] == new_rows[new_row][c]:
                        continue
                    else:
                        print(f"Updating {table_name} with most recent data at {cur_data_rows[cur_row][0]}: {cur_data_rows[cur_row][c]} -> {new_rows[new_row][c]}")
                        cur_data_rows[cur_row][c] = new_rows[new_row][c]
                cur_row += 1
                new_row += 1
        while new_row < len(new_rows):
            cur_data_rows.append(new_rows[new_row])
            new_row += 1
    save_as_csv(table_name, headers, cur_data_rows)


def get_page(url):
    """Constructs and returns a DOM of the HTML content of `url` passed"""

    contents = urllib.request.urlopen(url).read()
#    contents = open('https _www.sst.dk_da_corona_tal-og-overvaagning.html', 'r').read()
    print("File fetched")
    return lxml.html.document_fromstring(contents)


def get_table_rows(dom, xpath):
    """Given a dom and xpath, returns all its rows"""
    table = dom.xpath(xpath)
    assert len(table) == 1, len(table)
    rows = []
    #    assert "Hele landet" == table.xpath(".//tr")[0].xpath('.//td')[NATIONAL_COLUMN].text_content().strip()
    for tr in table[0].xpath(".//tr"):
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
                cells.append(td.text_content().replace('✱', '').strip())
        date_match = re.compile(DATE_REGEXP).match(cells[0])
        if cells[0] == '':  # This is header.
            cells[0] = 'Dato'
        elif cells[0] != '' and not date_match:
            print(f"skipping row with date = '{cells[0]}'")
            continue
        else:
            monthday = int(date_match.groups()[0])
            month = ['januar', 'februar', 'marts', 'april', 'maj', 'juni', 'juli'].index(date_match.groups()[1]) + 1
            cells[0] = f"2020-{month:02}-{monthday:02}"
        rows.append(cells)
    return rows[:1] + sorted(rows[1:], key=lambda r: r[0])


dom = get_page(SOURCE_URL)

hospitalised = get_table_rows(dom, XPATH_HOSPITALISED)
update_csv('covid-19-hospitalised', hospitalised[0], hospitalised[1:])

icu = get_table_rows(dom, XPATH_ICU)
update_csv('covid-19-icu', icu[0], icu[1:])

icu_vent = get_table_rows(dom, XPATH_ICU_VENT)
update_csv('covid-19-icu_vent', icu_vent[0], icu_vent[1:])

tests = get_table_rows(dom, XPATH_TESTS)
update_csv('covid-19-tests', tests[0], tests[1:-1])  # Skip last observation as it is inaccurate

