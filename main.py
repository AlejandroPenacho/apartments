import requests
import json
import csv
import os
import time
from bs4 import BeautifulSoup

DATA_DIR = "data"
DB_FILENAME = "apartments_db.csv"


class Item:
    def __init__(self, html):
        self.type = html.find(class_="ObjektTyp").text.strip()
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

        queue_data = html.find("dd", class_="ObjektAntalIntresse hidden-phone").text.strip()
        self.queue_max_days = int(queue_data.split()[0])
        self.queue_length = int(queue_data.split()[1][1:-3])

        self.electricity_included = html.find(class_="PropertyItem Egenskap-1036") is not None
        self.max_4_years = html.find(class_="PropertyItem Egenskap-1093") is not None
        self.free_rent_summer = html.find("find out what should go here") is not None



    def __str__(self):
        output = ""
        output += f"Type:                {self.type}\n"
        output += f"Address:             {self.address}\n"
        output += f"Free text:           {self.free_text}\n"
        output += f"Id:                  {self.id}\n"
        output += f"Area:                {self.area}\n"
        output += f"Living space:        {self.living_space}\n"
        output += f"Rent:                {self.rent} SEK\n"
        output += f"Contract start:      {self.contract_start}\n"
        output += f"Queue max days:      {self.queue_max_days}\n"
        output += f"Queue length:        {self.queue_length}\n"
        output += f"Electricity free:    {self.electricity_included}\n"
        output += f"Free rent summer:    {self.free_rent_summer}\n"
        output += f"Max 4 years:         {self.max_4_years}\n"

        return output


class ApartmentDatabase:
    def __init__(self, filename):
        self.filename = filename

    def get_all_ids(self):
        with open(self.filename) as file:
            file = csv.reader(file)
            return [x[0] for x in file][1:]

    def add_item(self, item: Item):
        with open(self.filename, "a") as file:
            file = csv.writer(file)
            file.writerow([
                item.id,
                item.type,
                item.address,
                item.area,
                item.living_space,
                item.rent,
                item.contract_start,
                item.electricity_included,
                item.free_rent_summer,
                item.max_4_years
            ])

    @classmethod
    def create(cls, filename):
        with open(filename, "w") as file:
            file = csv.writer(file)
            file.writerow(
                ["Id", "Type", "Address", "Area", "Living space", "Rent", "Contract start", "Electricity free", "Free rent summer", "Max 4 years"]
            )

            return cls(filename)


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

    return [Item(x) for x in items]

def save_stats(items, path):
    first_row = ["Id", "Max queue days", "Queue length"]
    rows = [
        [item.id, item.queue_max_days, item.queue_length]
        for item in items
    ]

    with open(path, "w") as file:
        file = csv.writer(file)
        file.writerow(first_row)
        file.writerows(rows)


if __name__ == "__main__":
    items = get_all_items()
    n_items = len(items)

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # Save stats
    local_time = time.localtime()
    stats_filename = f"{local_time.tm_year:0>4}{local_time.tm_mon:0>2}{local_time.tm_mday:0>2}-{local_time.tm_hour:0>2}{local_time.tm_min:0>2}.csv"
    stats_path = os.path.join(DATA_DIR, stats_filename)
    save_stats(items, stats_path)

    # Update (or create) database
    db_path = os.path.join(DATA_DIR, DB_FILENAME)

    if not os.path.exists(db_path):
        db = ApartmentDatabase.create(db_path)
    else:
        db = ApartmentDatabase(db_path)

    n_new_ids = 0
    all_registered_id = db.get_all_ids()
    for item in items:
        if item.id not in all_registered_id:
            n_new_ids += 1
            db.add_item(item)

    print(f"Registered {n_items} apartments, {n_new_ids} of them new")
