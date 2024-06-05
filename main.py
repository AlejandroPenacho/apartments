import requests
import json
import csv
import os
import time
from bs4 import BeautifulSoup

DATA_DIR = "data"
DB_FILENAME = "apartments_db.csv"
FIELD_NAMES = ["Id", "Type", "Area", "Address", "Floor", "Orientation", "Living space", "Rent", "Contract start", "Electricity included", "Free rent summer", "Max 4 years", "Link", "Free text"]

class Apartment:
    def __init__(self):
        self.type: str = None
        self.address: str = None
        self.free_text: str = None
        self.id: str = None
        self.area: str = None
        self.floor: int = None
        self.orientation: str = None
        self.living_space: int = None
        self.rent: int = None
        self.link: str = None
        self.contract_start: str = None
        self.electricity_included: bool = None
        self.max_4_years: bool = None
        self.free_rent_summer: bool = None

    def __str__(self):
        output = ""
        output += f"Id:                  {self.id}\n"
        output += f"Type:                {self.type}\n"
        output += f"Area:                {self.area}\n"
        output += f"Address:             {self.address}\n"
        output += f"Floor:               {self.floor}\n"
        output += f"Orientation:         {self.orientation}\n"
        output += f"Living space:        {self.living_space}\n"
        output += f"Rent:                {self.rent} SEK\n"
        output += f"Contract start:      {self.contract_start}\n"
        output += f"Electricity free:    {self.electricity_included}\n"
        output += f"Free rent summer:    {self.free_rent_summer}\n"
        output += f"Max 4 years:         {self.max_4_years}\n"
        output += f"Link:                {self.link}\n"
        output += f"Free text:           {self.free_text}"

        return output

    @classmethod
    def from_csv_row(cls, row):
        self = cls()
        self.id = row["Id"]
        self.type = row["Type"]
        self.address = row["Address"]
        self.area = row["Area"]
        self.living_space = int(row["Living space"])
        self.floor = None if row["Floor"] == "" else int(row["Floor"])
        self.rent = int(row["Rent"])
        self.orientation = row["Orientation"]
        self.contract_start = row["Contract start"]
        self.electricity_included = row["Electricity included"]
        self.free_rent_summer = row["Free rent summer"]
        self.max_4_years = row["Max 4 years"]
        self.link = row["Link"]
        self.free_text = row["Free text"]
        return self

    @classmethod
    def from_html(cls, html):
        self = cls()
        self.type = html.find(class_="ObjektTyp").text.strip()
        self.link = html.find(class_="ObjektTyp").contents[0]["href"]
        self.address = html.find(class_="ObjektAdress").text.strip()
        self.free_text = html.find(class_="ObjektFritext").text.strip()

        self.id = html.find("dd", class_="ObjektNummer hidden-phone").text.strip()
        self.area = html.find("dd", class_="ObjektOmrade").text.strip()

        floor = html.find("dd", class_="ObjektVaning hidden-phone").text.strip()
        if floor == "GF" or floor == "Bottenvåning":
            self.floor = 0
        elif floor == "SU" or floor == "Sutterängvåning":
            self.floor = -1
        else:
            self.floor = int(floor)

        space = html.find("dd", class_="ObjektYta").text.strip()
        self.living_space = int(space.split()[0])

        rent = html.find("dd", class_="ObjektHyra").text.strip()
        self.rent = int("".join(rent.split()[:-1]))

        self.contract_start = html.find("dd", class_="ObjektInflytt hidden-phone").text.strip()

        self.electricity_included = html.find(class_="PropertyItem Egenskap-1036") is not None
        self.max_4_years = html.find(class_="PropertyItem Egenskap-1093") is not None
        self.free_rent_summer = html.find("find out what should go here") is not None

        return self


class SSSBPageItem:
    def __init__(self, html):
        self.apartment = Apartment.from_html(html)
        queue_data = html.find("dd", class_="ObjektAntalIntresse hidden-phone").text.strip()
        self.queue_max_days = int(queue_data.split()[0])
        self.queue_length = int(queue_data.split()[1][1:-3])

    def __str__(self):
        output = ""
        output += f"Type:                {self.apartment.type}\n"
        output += f"Area:                {self.apartment.area}\n"
        output += f"Address:             {self.apartment.address}\n"
        output += f"Id:                  {self.apartment.id}\n"
        output += f"Living space:        {self.apartment.living_space}\n"
        output += f"Rent:                {self.apartment.rent} SEK\n"
        output += f"Contract start:      {self.apartment.contract_start}\n"
        output += f"Electricity free:    {self.apartment.electricity_included}\n"
        output += f"Free rent summer:    {self.apartment.free_rent_summer}\n"
        output += f"Max 4 years:         {self.apartment.max_4_years}\n"
        output += f"Queue max days:      {self.queue_max_days}\n"
        output += f"Queue length:        {self.queue_length}\n"
        output += f"Free text:           {self.apartment.free_text}\n"

        return output


class ApartmentDatabase:
    def __init__(self, filename):
        self.filename = filename

    def get_all_ids(self):
        with open(self.filename) as file:
            file = csv.reader(file)
            return [x[0] for x in file][1:]

    def add_apartment(self, apartment: Apartment):
        with open(self.filename, "a") as file:
            file = csv.DictWriter(file, FIELD_NAMES)
            file.writerow({
                "Id": apartment.id,
                "Type": apartment.type,
                "Link": apartment.link,
                "Address": apartment.address,
                "Area": apartment.area,
                "Floor": apartment.floor,
                "Orientation": apartment.orientation,
                "Living space": apartment.living_space,
                "Rent": apartment.rent,
                "Contract start": apartment.contract_start,
                "Electricity included": apartment.electricity_included,
                "Free rent summer": apartment.free_rent_summer,
                "Max 4 years": apartment.max_4_years,
                "Link": apartment.link,
                "Free text": apartment.free_text
            })

    def get_apartments(self):
        with open(self.filename) as file:
            file = csv.DictReader(file)
            return [Apartment.from_csv_row(row) for row in file]

    @classmethod
    def create(cls, filename):
        with open(filename, "w") as file:
            file = csv.writer(file)
            file.writerow(FIELD_NAMES)

            return cls(filename)

class QueueStats:
    def __init__(self):
        self.data = None
        pass

    @classmethod
    def from_filename(cls, filename):
        self = cls()
        data = {}
        with open(filename) as file:
            file = csv.reader(file)
            next(file)
            for row in file:
                data[row[0]] = [int(row[1]), int(row[2])]

        self.data = data
        return self

    @classmethod
    def from_items(cls, items: list[SSSBPageItem]):
        self = cls()
        data = {}
        for item in items:
            data[item.apartment.id] = [item.queue_max_days, item.queue_length]

        self.data = data
        return self

    def save(self, filename: str):
        with open(filename, "w") as file:
            file = csv.writer(file)
            file.writerow(["Id", "Max queue days", "Queue length"])
            for (id, data) in self.data.items():
                file.writerow([id, data[0], data[1]])


class CompleteData:
    def __init__(self, directory, apartment_db_filename):
        apartment_db = ApartmentDatabase(os.path.join(directory, apartment_db_filename))
        apartments = apartment_db.get_apartments()

        self.apartment_data = {x.id : x for x in apartments}
        self.queue_data = {x.id: [] for x in apartments}
        self.datapoints = []
        
        all_filenames = filter(lambda x: x != apartment_db_filename, os.listdir(directory))
        all_filenames = sorted(all_filenames)

        for filename in all_filenames:
            self.datapoints.append(filename.split(".")[0])
            for x in self.queue_data.values():
                x.append(None)

            queue_stats = QueueStats.from_filename(os.path.join(directory, filename))
            for id in queue_stats.data.keys():
                self.queue_data[id][-1] = queue_stats.data[id]


def get_all_items():
    url = "https://sssb.se/widgets/?pagination=0&paginationantal=0&callback=jQuery17203738205469265453_1716401358472&widgets%5B%5D=alert&widgets%5B%5D=objektsummering%40lagenheter&widgets%5B%5D=objektfilter%40lagenheter&widgets%5B%5D=objektsortering%40lagenheter&widgets%5B%5D=objektlistabilder%40lagenheter&widgets%5B%5D=pagineringantal%40lagenheter&widgets%5B%5D=paginering%40lagenheter&widgets%5B%5D=pagineringgofirst%40lagenheter&widgets%5B%5D=pagineringgonew%40lagenheter&widgets%5B%5D=pagineringlista%40lagenheter&widgets%5B%5D=pagineringgoold%40lagenheter&widgets%5B%5D=pagineringgolast%40lagenheter"

    response = requests.get(url).text

    """
    with open("cached_data.json", "w") as file:
        file.write(response)
    """

    """
    with open("cached_data.json") as file:
        response = file.read()
    """

    paren_position = response.find("(")
    trimmed_response = response[paren_position+1:-2]

    all_data = json.loads(trimmed_response)

    data = BeautifulSoup(all_data["html"]["objektlistabilder@lagenheter"], features="html.parser")

    items = data.find_all(class_="Box ObjektListItem")

    return [SSSBPageItem(x) for x in items]

def collect_data():
    items = get_all_items()
    n_items = len(items)

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # Save stats
    local_time = time.localtime()
    stats_filename = f"{local_time.tm_year:0>4}{local_time.tm_mon:0>2}{local_time.tm_mday:0>2}-{local_time.tm_hour:0>2}{local_time.tm_min:0>2}.csv"
    stats_path = os.path.join(DATA_DIR, stats_filename)
    QueueStats.from_items(items).save(stats_path)

    # Update (or create) database
    db_path = os.path.join(DATA_DIR, DB_FILENAME)

    if not os.path.exists(db_path):
        db = ApartmentDatabase.create(db_path)
    else:
        db = ApartmentDatabase(db_path)

    n_new_ids = 0
    all_registered_id = db.get_all_ids()
    for item in items:
        if item.apartment.id not in all_registered_id:
            n_new_ids += 1
            db.add_apartment(item.apartment)

    print(f"Registered {n_items} apartments, {n_new_ids} of them new")


if __name__ == "__main__":
    collect_data()
    # data = CompleteData(DATA_DIR, DB_FILENAME)
    # print(data.queue_data)