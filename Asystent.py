import pandas as pd
from pathlib import Path
pd.options.mode.chained_assignment = None

class DataProcessing:
    @staticmethod
    def norm(X):
        print("Przygotowuje baze danych, prosze czekac...")
        result = X.select_dtypes(exclude="object")
        for i in result:
            min_value = result[i].min()
            max_value = result[i].max()
            for j in range(0, len(result[i])):
                result[i].iloc[j] = (result[i].iloc[j] - min_value)/max_value
        result = result.join(X.select_dtypes(include="object"))
        print("Gotowe")
        return result
    @staticmethod
    def norm_sample(X, sample, min_budget, max_budget):
        result = X.select_dtypes(exclude="object")
        for i in result:
            min_value = result[i].min()
            max_value = result[i].max()
            sample[i] = (sample[i] - min_value)/max_value
            if i == "price":
                min_budget = (min_budget - min_value)/max_value
                max_budget = (max_budget - min_value)/max_value
        result = result.join(X.select_dtypes(include="object"))
        return sample, min_budget, max_budget
    @staticmethod
    def unnorm(sample, X):
        result = X.select_dtypes(exclude="object")
        for i in result:
            min_value = result[i].min()
            max_value = result[i].max()
            sample[i] = int(sample[i]*max_value + min_value)
        return sample
        
    
class KNearestNeighbors:
    @staticmethod
    # Metoda glowna
    def Classifier(sample, x_org, k, min_budget, max_budget):
        x = x_org.copy()
        # ================Ograniczenie wyszukiwan================#
        # ====Wybranie rekordow ograniczonych zadanym budzetem====#
        x_limited = x.loc[(x['price'] > min_budget) & (x['price'] < max_budget)]
        x = x_limited.copy()
        # ====Sprawdzenie czy uzytkownik podal wybor dotyczacy uszkodzonych aut====#
        if sample['notRepairedDamage'] == "":  # W przypadku braku wyboru domyslna opcja jest "no"
            x_limited = x.loc[(x['notRepairedDamage'] == "no")]
        elif sample['notRepairedDamage'] != "":
            if sample['notRepairedDamage'] == "no":
                # ====Jezeli uzytkownik nie dopuscil wyszukiwania uszkodzonych aut, wyszukiwanie jest ograniczane====#
                x_limited = x.loc[(x['notRepairedDamage'] == sample['notRepairedDamage'])]
        x = x_limited.copy()
        # ====Ograniczenie wyboru nadwozia====#
        # ====Jezeli uzytkownik nie podal typu, algorytm nie ogranicza bazy====#
        if sample['vehicleType'] != "none":
            x_limited = x.loc[x['vehicleType'] == sample['vehicleType']]
        x = x_limited.copy()
        # ====Ograniczenie wyboru skrzyni biegow====#
        # ====Jezeli uzytkownik nie podal typu, algorytm nie ogranicza bazy====#
        if sample['gearbox'] != "none":
            x_limited = x.loc[x['gearbox'] == sample['gearbox']]
        x = x_limited.copy()
        # ====Ograniczenie wyboru typu paliwa
        # ====Jezeli uzytkownik nie podal typu, algorytm nie ogranicza bazy====#
        if sample['fuelType'] != "none":
            x_limited = x.loc[x['fuelType'] == sample['fuelType']]
        x = x_limited.copy()
        # ================Obliczenie odleglosci przy uzyciu metryki Minkowskiego================#
        distances = []
        result = []
        for i in range(0, len(x_limited), 1):
            distances.append(KNearestNeighbors.metric(sample, x_limited.iloc[i], 2))
        # ================Sortowanie zbioru od najmniejszej odleglosci, dla k sasiadow================#
        for i in range(0, k):
            for j in range(i, len(distances)):
                if distances[i] > distances[j]:
                    distances[j], distances[i] = distances[i], distances[j]
                    x_limited.iloc[j], x_limited.iloc[i] = x_limited.iloc[i], x_limited.iloc[j]
        # ================Zwrocenie wyniku================#
        if not x_limited.empty:
            if len(x_limited) < k:
                for i in range(0, len(x_limited), 1):
                    result.append(x_limited.iloc[[i]])
            else:
                for i in range(0, k, 1):
                    result.append(x_limited.iloc[[i]])
        return result
        # Metryka Minkowskiego

    def metric(v1, v2, m):
        distance = 0
        for i in ('price', 'powerPS', 'kilometer', 'Age'):
            distance += abs(v1[i] - v2[i]) ** m
        distance = distance ** (1 / m)
        return distance


class Interface:
    @staticmethod
    def MainMenu():
        while True:
            print("Asystent Wyboru Auta Uzywanego\n")
            print("-> 1. Start")
            print("-> 2. Pokaz Informacje")
            print("-> 9. Zakoncz program")
            option = input("--> ")
            if option == "1":
                program = Interface.Menu()
                if program == 0:
                    continue
            if option == "2":
                Interface.Info()
                continue
            if option == "9":
                break

    @staticmethod
    def Info():
        try:
            with open('readme.txt', encoding="utf-8") as info:
                lines = info.readlines()
            for line in lines:
                print(line.rstrip())
            _ = input("Wcisnij aby kontynuowac")
        except:
            print("Brak pliku readme.txt")

    @staticmethod
    def Menu():
        # =====Default values=====#
        min_budget = 0
        max_budget = 0
        avg_budget = 0
        car_type = "none"
        gearbox = "none"
        horsepower = 0
        mileage = 0
        fuel_type = "none"
        damage = "no"
        age = 0.0
        k = 5
        # =====BUDZET=====#
        
        print("Podaj budzet ktory chcesz przeznaczyc na zakup auta:")
        min_budget = input("--> Minimalny Budzet: ")
        while not min_budget.isnumeric():
            if (min_budget == "-1"):
                return 0
            print("Podaj wartosc numeryczna!")
            min_budget = input("--> Minimalny Budzet: ")
        min_budget = int(min_budget)
        max_budget = input("--> Maksymalny Budzet: ")
        while not max_budget.isnumeric():
            if (max_budget == "-1"):
                return 0
            print("Podaj wartosc numeryczna!")
            max_budget = input("--> Maksymalny Budzet: ")
        if int(max_budget) > cars["price"].max():
            max_budget = str(cars["price"].max())
        if int(min_budget) > cars["price"].max():
            min_budget = str(cars["price"].max())
        max_budget = int(max_budget)
        min_budget = int(min_budget)
        avg_budget = (min_budget + max_budget) / 2

        # =====TYP NADWOZIA=====#
        print("\nPodaj typ nadwozia ktory Cie interesuje:")
        print("Pytanie mozna pominac, algorytm uwzgledni wtedy wszystkie typy nadwozia")
        print("-> 1. Sedan\n-> 2. Kabriolet\n-> 3. Coupe\n-> 4. Auto miejskie")
        print("-> 5. Kombie\n-> 6. Suv\n-> 7. Bus\n-> 8. Inne")
        car_type = input("--> Wybierz typ: ")
        if (car_type == "-1"):
            return 0
        dictonary = {"1": "limousine", "2": "cabrio", "3": "coupe", "4": "small car", "5": "kombi", "6": "suv",
                     "7": "bus", "8": "others"}
        car_type = dictonary.get(car_type, "none")

        # =====TYP SKRZYNI BIEGOW=====#
        print("\nPodaj typ skrzyni biegow ktory Cie interesuje:")
        print("Pytanie mozna pominac, algorytm uwzgledni wtedy wszystkie typy skrzyni biegow")
        print("-> 1. Manualna\n-> 2. Automatyczna")
        gearbox = input("--> Wybierz typ: ")
        if (gearbox == "-1"):
            return 0
        dictonary = {"1": "manual", "2": "automatic"}
        gearbox = dictonary.get(gearbox, "none")

        # =====MOC=====#
        print("\nPodaj pozadana ilosc koni mechanicznych:")
        print("Domyslna wartosc to 100 koni mechanicznych")
        horsepower = input("--> ")
        if (horsepower == "-1"):
            return 0
        if horsepower.isnumeric():
            horsepower = int(horsepower)
        else:
            horsepower = 100
        if horsepower > cars["powerPS"].max():
            horsepower = cars["powerPS"].max()

        # =====PALIWO=====#
        print("\nPodaj typ paliwa, ktory cie interesuje:")
        print("Pytanie mozna pominac, algorytm uwzgledni wtedy wszystkie typy paliwa")
        print("-> 1. Benzyna\n-> 2. Diesel\n-> 3. LPG\n-> 4. CNG")
        print("-> 5. Hybryda\n-> 6. Elektryczny\n-> 7. Inny")
        dictonary = {"1": "petrol", "2": "diesel", "3": "lpg", "4": "cng", "5": "hybrid", "6": "electric",
                     "7": "others"}
        fuel_type = input("--> Wybierz typ: ")
        if (fuel_type == "-1"):
            return 0
        fuel_type = dictonary.get(fuel_type, "none")

        # =====PRZEBIEG=====#
        print("Podaj interesujacy Cie przebieg auta:")
        print("Pominiecie pytania spowoduje, ze algorytm bedzie szukal aut o jak najmniejszym przebiegu")
        mileage = input("--> ")
        if (mileage == "-1"):
            return 0
        if mileage.isnumeric():
            mileage = int(mileage)
            if mileage < 0:
                mileage = 0
        else:
            mileage = 0
        if mileage > cars["kilometer"].max():
            mileage = cars["kilometer"].max()

        # =====USZKODZONE=====#
        print("Czy w wyszukiwaniu uwzglednic auta uszkodzone?")
        print("Domyslnie algorytm nie uwzglednia aut uszkodzonych")
        print("-> 1. Tak")
        print("-> 2. Nie")
        dictonary = {"1": "yes", "2": "no"}
        damage = input("--> ")
        if (damage == "-1"):
            return 0
        damage = dictonary.get(damage, "no")

        # =====WIEK=====#
        print("Podaj wiek auta ktory Cie interesuje:")
        print("Pominiecie pytania spowoduje, ze algorytm bedzie szukal najmlodszego auta")
        age = input("--> ")
        if (age == "-1"):
            return 0
        if age.isnumeric():
            age = int(age)
            if age < 0:
                age = 0
        else:
            age = 0
        if age > cars["Age"].max():
            age = cars["Age"].max()    

        # =====ILE AUT====#
        print("Ile proponowanych samochodow program ma wyswietlic?")
        print("Domyslne program wyswietla 5 proponowanych aut")
        k = input("--> ")
        if (k == "-1"):
            return 0
        if k.isnumeric():
            k = int(k)
            if k < 0:
                k = 5
        else:
            k = 5

        # ========WYWOLANIE ALGORYTMU========#
        sample = {"price": min_budget, "vehicleType": car_type, "gearbox": gearbox, "powerPS": horsepower,
                  "kilometer": mileage, "fuelType": fuel_type, "notRepairedDamage": damage, "Age": age}
        sample, min_budget, max_budget = DataProcessing.norm_sample(cars, sample, min_budget, max_budget)
        zgadywana = KNearestNeighbors.Classifier(sample, cars_norm, k, min_budget, max_budget)
        for i in range(0, len(zgadywana), 1):
            zgadywana[i] = DataProcessing.unnorm(zgadywana[i], cars)
        # ========WYPISANIE WYNIKoW========#
        if len(zgadywana) != 0:
            if len(zgadywana) < k:
                print(len(zgadywana), "aut najbardziej spelniajacych wymagania: ")
                for i in range(0, len(zgadywana), 1):
                    zgadywana[i] = zgadywana[i].astype(str)
                    print(
                        f"{'Brand:':7}{zgadywana[i]['brand'].values[0]:14}{'| Model:':7}{zgadywana[i]['model'].values[0]:12}{'| Price:':7}{zgadywana[i]['price'].values[0]:7}{'| Horse Power: ':12}{zgadywana[i]['powerPS'].values[0]:5}{'| Mileage:':9}{zgadywana[i]['kilometer'].values[0]:8}{'| Gearbox:':9}{zgadywana[i]['gearbox'].values[0]:12}{'| Vehicle Type:':15}{zgadywana[i]['vehicleType'].values[0]:10}{'| Fuel Type:':11}{zgadywana[i]['fuelType'].values[0]:9}{'| Wiek auta:':11}{zgadywana[i]['Age'].values[0]:5}")
            elif len(zgadywana) >= k:
                print(k, "aut najbardziej spelniajacych wymagania: ")
                for i in range(0, k, 1):
                    zgadywana[i] = zgadywana[i].astype(str)
                    print(
                        f"{'Brand:':7}{zgadywana[i]['brand'].values[0]:14}{'| Model:':7}{zgadywana[i]['model'].values[0]:12}{'| Price:':7}{zgadywana[i]['price'].values[0]:7}{'| Horse Power: ':12}{zgadywana[i]['powerPS'].values[0]:5}{'| Mileage:':9}{zgadywana[i]['kilometer'].values[0]:8}{'| Gearbox:':9}{zgadywana[i]['gearbox'].values[0]:12}{'| Vehicle Type:':15}{zgadywana[i]['vehicleType'].values[0]:10}{'| Fuel Type:':11}{zgadywana[i]['fuelType'].values[0]:9}{'| Wiek auta:':11}{zgadywana[i]['Age'].values[0]:5}")
        else:
            print("Nie znaleziono aut pasujacych do wymagan!")
        print("\n\n")
        _ = input("Wcisnij aby kontynuowac")
        return 0

#Otworzenie pliku i aktywowanie menu glownego`
database = Path("cleanedCar.csv")
if(database.is_file()):
    cars = pd.read_csv('cleanedCar.csv')
    # Usuniecie pustych rekordow
    cars.dropna(subset=["vehicleType"], inplace=True)
    cars.dropna(subset=["gearbox"], inplace=True)
    cars.dropna(subset=["powerPS"], inplace=True)
    cars.dropna(subset=["model"], inplace=True)
    cars.dropna(subset=["kilometer"], inplace=True)
    cars.dropna(subset=["fuelType"], inplace=True)
    cars.dropna(subset=["brand"], inplace=True)
    cars.dropna(subset=["Age"], inplace=True)
    cars.dropna(subset=["notRepairedDamage"], inplace=True)
    pd.set_option('display.max_columns', None)
    cars_norm = DataProcessing.norm(cars)
    Interface.MainMenu()
else:
    print("Nie udalo sie otworzyc bazy danych")
    print("Umiesc baze danych(cleanedCar.csv) w lokalizacji skryptu i uruchom program ponownie")
    _ = input("Wcisnij aby kontynuowac")
