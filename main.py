import requests
import json
from bs4 import BeautifulSoup

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


url = "https://sssb.se/widgets/?pagination=0&paginationantal=0&callback=jQuery17203738205469265453_1716401358472&widgets%5B%5D=alert&widgets%5B%5D=objektsummering%40lagenheter&widgets%5B%5D=objektfilter%40lagenheter&widgets%5B%5D=objektsortering%40lagenheter&widgets%5B%5D=objektlistabilder%40lagenheter&widgets%5B%5D=pagineringantal%40lagenheter&widgets%5B%5D=paginering%40lagenheter&widgets%5B%5D=pagineringgofirst%40lagenheter&widgets%5B%5D=pagineringgonew%40lagenheter&widgets%5B%5D=pagineringlista%40lagenheter&widgets%5B%5D=pagineringgoold%40lagenheter&widgets%5B%5D=pagineringgolast%40lagenheter"

"""
response = requests.get(url).text
with open("cached_data.json", "w") as file:
    file.write(response)
"""

with open("cached_data.json") as file:
    response = file.read()



paren_position = response.find("(")
trimmed_response = response[paren_position+1:-2]

all_data = json.loads(trimmed_response)

data = BeautifulSoup(all_data["html"]["objektlistabilder@lagenheter"], features="html.parser")

items = data.find_all(class_="Box ObjektListItem")


print(f"{len(items)} apartments")

for element in items:
    item = Item(element)
    print(item)

# print(response)
