# main.py

import DB_Handler
import user_Login as UL

def start_app():
    print("=== Velkommen til Food Saver ===")
    bruger_data = None

    # Login / Opret konto
    while not bruger_data:
        print("1. Login")
        print("2. Opret konto")
        valg = input("Vælg: ").strip()
        if valg == "1":
            bruger_data = UL.login()
        elif valg == "2":
            bruger_data = UL.opret_bruger()
        else:
            print("Ugyldigt valg.\n")

    DB_Handler.lager = {k.lower(): v for k, v in bruger_data.get("lager", {}).items()}

    DB_Handler.load_opskrifter()

    # Hovedmenu
    while True:
        print("\n=== Food Saver App ===")
        print("1. Tilføj ingrediens til lager")
        print("2. Slet ingrediens fra lager")
        print("3. Vis lager")
        print("4. Find opskrifter")
        print("5. Tilføj opskrift")
        print("6. Afslut")

        valg = input("Vælg et nummer: ").strip()

        if valg == "1":
            navn = input("Navn på ingrediens: ").strip().lower()
            mængde = input(f"Mængde af {navn}: ").strip()
            try:
                mængde = float(mængde)
                DB_Handler.tilføj_ingredient(navn, mængde, bruger_data)  
            except ValueError:
                print("Ugyldig mængde.\n")

        elif valg == "2":
            navn = input("Navn på ingrediens du vil slette: ").strip().lower()
            DB_Handler.slet_ingredient(navn, bruger_data)  


        elif valg == "3":
            DB_Handler.vis_lager()

        elif valg == "4":
            antal = input("Hvor mange personer skal opskriften være til? ").strip()
            try:
                antal = int(antal)
                DB_Handler.find_opskrifter(antal_personer=antal)
            except ValueError:
                print("Ugyldigt antal.\n")

        elif valg == "5":
            DB_Handler.tilføj_opskrift_yml()

        elif valg == "6":
            # Gem lager tilbage til brugerdata
            bruger_data["lager"] = DB_Handler.lager
            UL.gem_bruger(bruger_data)
            print("Farvel!")
            break

        else:
            print("Ugyldigt valg, prøv igen.\n")


if __name__ == "__main__":
    start_app()
