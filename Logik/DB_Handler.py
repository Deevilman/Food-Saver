import yaml
import os
import user_Login as UL

lager = {}  # Fyldes fra main.py når brugeren logger ind
opskrifter = {}

opskrift_mappe = r"C:\Users\oller\OneDrive\Desktop\KOD - Food saver\DB\Opskrifter"
def load_opskrifter():
    global opskrifter
    opskrifter = {}
    for fil in os.listdir(opskrift_mappe):
        if fil.endswith(".yml"):
            with open(os.path.join(opskrift_mappe, fil), "r", encoding="utf-8-sig") as f:
                data = yaml.safe_load(f)
                navn = fil.replace(".yml", "").replace("_", " ")
                opskrifter[navn] = data

def tilføj_ingredient(navn, mængde, bruger_data=None):
    navn = navn.lower()
    if navn in lager:
        lager[navn] += mængde
    else:
        lager[navn] = mængde
    print(f"{mængde} af {navn} er tilføjet til lageret.")

    if bruger_data:
        bruger_data["lager"] = lager
        UL.gem_bruger(bruger_data)

def slet_ingredient(navn, bruger_data=None):
    navn = navn.lower()
    if navn in lager:
        del lager[navn]
        print(f"{navn} er slettet fra lageret.")
    else:
        print(f"{navn} findes ikke i lageret.")

    if bruger_data:
        bruger_data["lager"] = lager
        UL.gem_bruger(bruger_data)

def vis_lager():
    if not lager:
        print("Dit lager er tomt.")
    else:
        print("Dit lager:")
        for ing, mængde in lager.items():
            print(f"- {ing}: {mængde}")



def find_opskrifter(antal_personer=1):
    """Find opskrifter der kan laves med lageret"""
    if not lager:
        print("Ingen ingredienser i lageret.\n")
        return

    load_opskrifter()
    fundet = False
    print(f"\nOpskrifter du kan lave til {antal_personer} person(er):")

    for navn, data in opskrifter.items():
        ingreds = data["ingredienser"]
        mangler = {}
        for ing, mængde in ingreds.items():
            total_mængde = mængde * antal_personer
            if ing not in lager or lager[ing] < total_mængde:
                mangler[ing] = max(total_mængde - lager.get(ing, 0), 0)

        if len(mangler) == 0:
            print(f"- {navn} (du har alle ingredienser)")
            fundet = True
        elif 0 < len(mangler) < len(ingreds):
            mangler_str = ", ".join(f"{k}: {v}" for k, v in mangler.items())
            print(f"- {navn} (mangler: {mangler_str})")
            fundet = True

    if not fundet:
        print("Ingen opskrifter kan laves med det lager, du har.\n")

def tilføj_opskrift_yml():
    """Tilføj en ny opskrift som .yml fil"""
    navn = input("Navn på opskrift: ").strip()
    ingred_input = input("Ingredienser med mængde (fx pasta:100, tomat:2): ").strip()

    if not navn or not ingred_input:
        print("Ugyldigt input.\n")
        return

    ingreds = {}
    for del_str in ingred_input.split(","):
        try:
            ing, mængde = del_str.split(":")
            ingreds[ing.strip().lower()] = float(mængde.strip())
        except:
            print(f"Fejl i input: '{del_str}' springes over.")

    tid = input("Hvor lang tid tager opskriften (minutter)? ").strip()
    beskrivelse = input("Skriv selve opskriften: ").strip()

    data = {
        "ingredienser": ingreds,
        "tid": tid,
        "opskrift": beskrivelse
    }

    filnavn = navn.replace(" ", "_") + ".yml"
    filsti = os.path.join(opskrift_mappe, filnavn)
    with open(filsti, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)

    print(f"Opskrift '{navn}' er tilføjet!\n")
