import csv
import io

import lxml.html
import re
from zipfile import ZipFile
import urllib.request

import unicodecsv as unicodecsv

DATE_REGEXP = '^(\\d+) ?\\. ?(\\w*)$'
SOURCE_URL = 'https://www.sst.dk/da/corona/tal-og-overvaagning'
XPATH_TESTS = '       //div/h3[contains(., "2.4 Antallet af tests og bekræftede smittede med COVID-19")]/following-sibling::div[1]/table'
XPATH_HOSPITALISED = '//div/h3[.="3.7 Indlagte patienter med bekræftet COVID-19"]/following-sibling::div[1]/table'
XPATH_ICU = '         //div/h3[.="3.8 Indlagte patienter med bekræftet COVID-19 på intensivafdeling"]/following-sibling::div[1]/table'
XPATH_ICU_VENT = '    //div/h3[.="3.9 Indlagte patienter med bekræftet COVID-19 på intensivafdeling og i respirator"]/following-sibling::div[1]/table'
SSI_SOURCE_URL = 'https://www.ssi.dk/sygdomme-beredskab-og-forskning/sygdomsovervaagning/c/covid19-overvaagning'
XPATH_ZIP_URL =     "//*[@id='top']/div[2]/section[6]/blockquote/div/strong/a[@title='fil med overvågningsdata' and contains(text(),'fil med overvågningsdata')]/@href"

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
        assert headers == cur_rows[0], f"{table_name}: Expected {cur_rows[0]}. Got {headers}"
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
            assert new_rows[new_row][0] not in [r[0] for r in cur_data_rows]
            cur_data_rows.append(new_rows[new_row])
            new_row += 1
    save_as_csv(table_name, headers, cur_data_rows)


def get_page(url):
    """Constructs and returns a DOM of the HTML content of `url` passed"""

    contents = urllib.request.urlopen(url).read()
#    contents = open('https _www.sst.dk_da_corona_tal-og-overvaagning.html', 'r').read()
    print("File fetched")
    return lxml.html.document_fromstring(contents)


def sanitise_row(cells):
    date_match = re.compile(DATE_REGEXP).match(cells[0])
    if cells[0] == '':  # This is header.
        cells[0] = 'Dato'
    elif cells[0] != '' and not date_match:
        print(f"skipping row with date = '{cells[0]}'")
        return False
    else:
        monthday = int(date_match.groups()[0])
        months = [['jan','januar'],
                  ['feb', 'februar'],
                  ['mar', 'marts'],
                  ['apr', 'april'],
                  ['maj'],
                  ['jun', 'juni'],
                  ['jul', 'juli']]
        month = next(i for i,m in enumerate(months) if date_match.groups()[1] in m) + 1
        cells[0] = f"2020-{month:02}-{monthday:02}"
    for i in range(len(cells)):
        cells[i] = cells[i].replace('✱', '').strip()
    return True


def get_table_rows(dom, xpath):
    """Given a dom and xpath, returns all its rows"""
    table = dom.xpath(xpath)
    assert len(table) == 1, f"{xpath} => {len(table)}"
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
        if not sanitise_row(cells):
            continue
        rows.append(cells)
    return rows[:1] + sorted(rows[1:], key=lambda r: r[0])


def convert_from_zip(dom):
    link = dom.xpath(XPATH_ZIP_URL)
    assert len(link) == 1, f"{XPATH_ZIP_URL} => {len(link)}"
    with ZipFile(io.BytesIO(urllib.request.urlopen(link[0]).read())) as myzip:
        with myzip.open('Deaths_over_time.csv', mode='r') as csvDataFile:
            csvReader = unicodecsv.reader(csvDataFile, lineterminator='\n', encoding='utf-8-sig', delimiter=';')
            rows = list(csvReader)
            deaths = rows[:1] + sorted(rows[1:-1], key=lambda r: r[0])
            update_csv('ssi-raw-data-deaths', deaths[0], deaths[1:])

        with myzip.open('Test_pos_over_time.csv', mode='r') as csvDataFile:
            csvReader = unicodecsv.reader(csvDataFile, lineterminator='\n', encoding='utf-8-sig', delimiter=';')
            rows = list(csvReader)
            tests = rows[:1] + sorted(rows[1:-2], key=lambda r: r[0])
            update_csv('ssi-raw-data-tests', tests[0], tests[1:])

        # myzip.extract('Deaths_over_time.csv','../')
        # myzip.extract('Test_pos_over_time.csv','../')


dom = get_page(SOURCE_URL)

hospitalised = get_table_rows(dom, XPATH_HOSPITALISED)
update_csv('sst-raw-data-hospitalised', hospitalised[0], hospitalised[1:])

icu = get_table_rows(dom, XPATH_ICU)
update_csv('sst-raw-data-icu', icu[0], icu[1:])

icu_vent = get_table_rows(dom, XPATH_ICU_VENT)
update_csv('sst-raw-data-icu_vent', icu_vent[0], icu_vent[1:])

convert_from_zip(get_page(SSI_SOURCE_URL))

