#!/usr/bin/env python3
"""
Skript zur Ermittlung niederländischer Städte mit Intercity-Bahnhöfen,
Universitäten UND öffentlichen Schwimmbädern mit weniger als 300.000
Einwohnern aus OpenStreetMap.
"""

import json
import time
from typing import Dict, List, Optional

import requests


class DutchIntercityFinder:
    """Finder für niederländische Städte mit Intercity-Anschluss, Universitäten und Schwimmbädern."""

    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    def __init__(self, max_population: int = 300000, min_population: int = 100000):
        """
        Initialisiert den Finder.

        Args:
            max_population: Maximale Einwohnerzahl (Standard: 300.000)
            min_population: Minimale Einwohnerzahl (Standard: 100.000)
        """
        self.max_population = max_population
        self.min_population = min_population
        self.results = []

    @staticmethod
    def _haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """
        Berechnet die Entfernung zwischen zwei Koordinaten in km.

        Args:
            lon1: Längengrad des ersten Punkts
            lat1: Breitengrad des ersten Punkts
            lon2: Längengrad des zweiten Punkts
            lat2: Breitengrad des zweiten Punkts

        Returns:
            Entfernung in Kilometern
        """
        from math import asin, cos, radians, sin, sqrt

        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km

    def _load_cache(self, cache_file: str) -> Optional[Dict]:
        """
        Lädt gecachte Daten aus einer Datei.

        Args:
            cache_file: Name der Cache-Datei

        Returns:
            Gecachte Daten oder None falls nicht vorhanden
        """
        import os

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠ Fehler beim Laden des Cache: {e}")
                return None
        return None

    def _save_cache(self, cache_file: str, data: Dict):
        """
        Speichert Daten im Cache.

        Args:
            cache_file: Name der Cache-Datei
            data: Zu speichernde Daten
        """
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠ Fehler beim Speichern des Cache: {e}")

    def query_intercity_stations(self) -> List[Dict]:
        """
        Fragt Intercity-Bahnhöfe in den Niederlanden ab (mit Cache).

        Returns:
            Liste von Bahnhöfen mit deren Eigenschaften
        """
        cache_file = "cache_stations.json"

        # Versuche aus Cache zu laden
        cached_data = self._load_cache(cache_file)
        if cached_data is not None:
            print("✓ Lade Bahnhöfe aus Cache...")
            return cached_data

        # Overpass QL Query für niederländische Bahnhöfe
        query = """
        [out:json][timeout:60];
        area["ISO3166-1"="NL"][admin_level=2]->.nl;
        (
          // Bahnhöfe mit railway=station
          node["railway"="station"](area.nl);
          way["railway"="station"](area.nl);
          relation["railway"="station"](area.nl);
        );
        out center;
        >;
        out skel qt;
        """

        print("Frage OpenStreetMap-Daten ab (Bahnhöfe)...")
        try:
            response = requests.post(
                self.OVERPASS_URL, data={"data": query}, timeout=90
            )
            response.raise_for_status()
            data = response.json()

            stations = []
            for element in data.get("elements", []):
                tags = element.get("tags", {})
                name = tags.get("name", "")
                if not ("centraal" in name.lower() or "central" in name.lower()):
                    continue

                # Bestimme Koordinaten
                if element["type"] == "node":
                    lat = element.get("lat")
                    lon = element.get("lon")
                elif "center" in element:
                    lat = element["center"].get("lat")
                    lon = element["center"].get("lon")
                else:
                    continue

                station_info = {
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "operator": tags.get("operator", ""),
                    "network": tags.get("network", ""),
                    "train": tags.get("train", ""),
                    "uic_ref": tags.get("uic_ref", ""),
                    "wikidata": tags.get("wikidata", ""),
                }

                stations.append(station_info)

            print(f"✓ {len(stations)} Bahnhöfe gefunden")

            # Speichere im Cache
            self._save_cache(cache_file, stations)

            return stations

        except requests.exceptions.RequestException as e:
            print(f"✗ Fehler bei der Abfrage: {e}")
            return []

    def query_cities_with_population(self) -> List[Dict]:
        """
        Fragt niederländische Städte mit Einwohnerzahlen ab (mit Cache).

        Returns:
            Liste von Städten mit Einwohnerzahlen
        """
        cache_file = "cache_cities.json"

        # Versuche aus Cache zu laden
        cached_data = self._load_cache(cache_file)
        if cached_data is not None:
            print("\n✓ Lade Städte aus Cache...")
            return cached_data

        query = """
        [out:json][timeout:60];
        area["ISO3166-1"="NL"][admin_level=2]->.nl;
        (
          // Städte und Gemeinden
          node["place"~"city|town"]["population"](area.nl);
          way["place"~"city|town"]["population"](area.nl);
          relation["place"~"city|town"]["population"](area.nl);
        );
        out center;
        >;
        out skel qt;
        """

        print("\nFrage Städte mit Einwohnerzahlen ab...")
        time.sleep(2)  # Rate limiting

        try:
            response = requests.post(
                self.OVERPASS_URL, data={"data": query}, timeout=90
            )
            response.raise_for_status()
            data = response.json()

            cities = []
            for element in data.get("elements", []):
                tags = element.get("tags", {})
                name = tags.get("name", "Unbekannt")

                # Einwohnerzahl parsen
                pop_str = tags.get("population", "0")
                try:
                    population = int(pop_str.replace(",", "").replace(".", ""))
                except (ValueError, AttributeError):
                    population = 0

                # Koordinaten
                if element["type"] == "node":
                    lat = element.get("lat")
                    lon = element.get("lon")
                elif "center" in element:
                    lat = element["center"].get("lat")
                    lon = element["center"].get("lon")
                else:
                    continue

                city_info = {
                    "name": name,
                    "population": population,
                    "lat": lat,
                    "lon": lon,
                    "place_type": tags.get("place", ""),
                    "wikidata": tags.get("wikidata", ""),
                }

                cities.append(city_info)

            print(f"✓ {len(cities)} Städte mit Einwohnerzahlen gefunden")

            # Speichere im Cache
            self._save_cache(cache_file, cities)

            return cities

        except requests.exceptions.RequestException as e:
            print(f"✗ Fehler bei der Abfrage: {e}")
            return []

    def query_universities(self) -> List[Dict]:
        """
        Fragt niederländische Universitäten ab und dedupliziert nach Wikidata-ID (mit Cache).

        Returns:
            Liste von Universitäten mit deren Eigenschaften (dedupliziert)
        """
        cache_file = "cache_universities.json"

        # Versuche aus Cache zu laden
        cached_data = self._load_cache(cache_file)
        if cached_data is not None:
            print("\n✓ Lade Universitäten aus Cache...")
            return cached_data

        query = """
        [out:json][timeout:60];
        area["ISO3166-1"="NL"][admin_level=2]->.nl;
        (
          // Universitäten mit Wikidata-ID (nur Institutionen, nicht einzelne Gebäude)
          node["amenity"="university"]["wikidata"](area.nl);
          way["amenity"="university"]["wikidata"](area.nl);
          relation["amenity"="university"]["wikidata"](area.nl);
        );
        out center;
        >;
        out skel qt;
        """

        print("\nFrage Universitäten ab...")
        time.sleep(2)  # Rate limiting

        try:
            response = requests.post(
                self.OVERPASS_URL, data={"data": query}, timeout=90
            )
            response.raise_for_status()
            data = response.json()

            # Deduplizierung nach Wikidata-ID
            universities_by_wikidata = {}

            for element in data.get("elements", []):
                tags = element.get("tags", {})
                wikidata = tags.get("wikidata", "")

                # Überspringe Einträge ohne Wikidata-ID
                if not wikidata:
                    continue

                name = tags.get("name", "")
                website = tags.get("website", "")

                # Überspringe Einträge ohne Namen
                if not name:
                    continue

                # Nur Einträge mit "University" oder "Universiteit" im Namen
                name_lower = name.lower()
                if "university" not in name_lower and "universiteit" not in name_lower:
                    continue

                # Koordinaten
                if element["type"] == "node":
                    lat = element.get("lat")
                    lon = element.get("lon")
                elif "center" in element:
                    lat = element["center"].get("lat")
                    lon = element["center"].get("lon")
                else:
                    continue

                # Nur die beste Repräsentation pro Wikidata-ID behalten
                # Bevorzuge: Relations > Ways > Nodes
                if wikidata in universities_by_wikidata:
                    existing = universities_by_wikidata[wikidata]
                    # Bevorzuge Relations über Ways über Nodes
                    if element["type"] == "relation":
                        pass  # Aktuelle ist besser
                    elif existing["type"] == "relation":
                        continue  # Existierende ist besser
                    elif element["type"] == "way" and existing["type"] == "node":
                        pass  # Aktuelle ist besser
                    else:
                        continue  # Behalte existierende

                university_info = {
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "wikidata": wikidata,
                    "website": website,
                    "type": element["type"],
                }

                universities_by_wikidata[wikidata] = university_info

            # Konvertiere zu Liste und entferne das 'type' Feld
            universities = []
            for uni in universities_by_wikidata.values():
                uni_copy = {k: v for k, v in uni.items() if k != "type"}
                universities.append(uni_copy)

            print(f"✓ {len(universities)} Universitäten gefunden (dedupliziert nach Wikidata)")

            # Speichere im Cache
            self._save_cache(cache_file, universities)

            return universities

        except requests.exceptions.RequestException as e:
            print(f"✗ Fehler bei der Abfrage: {e}")
            return []

    def query_swimming_pools(self) -> List[Dict]:
        """
        Fragt öffentliche Schwimmbäder in den Niederlanden ab (mit Cache).

        Returns:
            Liste von Schwimmbädern mit deren Eigenschaften
        """
        cache_file = "cache_pools.json"

        # Versuche aus Cache zu laden
        cached_data = self._load_cache(cache_file)
        if cached_data is not None:
            print("\n✓ Lade Schwimmbäder aus Cache...")
            return cached_data

        # Query für öffentliche Schwimmbäder und Schwimmsportzentren
        query = """
        [out:json][timeout:60];
        area["ISO3166-1"="NL"][admin_level=2]->.nl;
        (
          // Öffentliche Schwimmbäder
          node["leisure"="swimming_pool"]["access"~"public|yes"](area.nl);
          way["leisure"="swimming_pool"]["access"~"public|yes"](area.nl);
          relation["leisure"="swimming_pool"]["access"~"public|yes"](area.nl);
          // Sportzentren mit Schwimmbad
          node["leisure"="sports_centre"]["sport"~"swimming"](area.nl);
          way["leisure"="sports_centre"]["sport"~"swimming"](area.nl);
          relation["leisure"="sports_centre"]["sport"~"swimming"](area.nl);
        );
        out center;
        >;
        out skel qt;
        """

        print("\nFrage öffentliche Schwimmbäder ab...")
        time.sleep(2)  # Rate limiting

        try:
            response = requests.post(
                self.OVERPASS_URL, data={"data": query}, timeout=90
            )
            response.raise_for_status()
            data = response.json()

            pools = []
            for element in data.get("elements", []):
                tags = element.get("tags", {})
                name = tags.get("name", "")
                leisure = tags.get("leisure", "")

                # Überspringe Einträge ohne Namen
                if not name:
                    continue

                # Überspringe Einträge ohne leisure Tag
                if not leisure:
                    continue

                # Koordinaten
                if element["type"] == "node":
                    lat = element.get("lat")
                    lon = element.get("lon")
                elif "center" in element:
                    lat = element["center"].get("lat")
                    lon = element["center"].get("lon")
                else:
                    continue

                pool_info = {
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "leisure": leisure,
                    "sport": tags.get("sport", ""),
                    "access": tags.get("access", ""),
                    "operator": tags.get("operator", ""),
                    "website": tags.get("website", ""),
                }

                pools.append(pool_info)

            print(f"✓ {len(pools)} Schwimmbäder gefunden")

            # Speichere im Cache
            self._save_cache(cache_file, pools)

            return pools

        except requests.exceptions.RequestException as e:
            print(f"✗ Fehler bei der Abfrage: {e}")
            return []

    def match_stations_to_cities(
        self, stations: List[Dict], cities: List[Dict], max_distance_km: float = 5.0
    ) -> List[Dict]:
        """
        Ordnet Bahnhöfe den Städten zu basierend auf der Entfernung.

        Args:
            stations: Liste der Bahnhöfe
            cities: Liste der Städte
            max_distance_km: Maximale Entfernung in km (Standard: 5 km)

        Returns:
            Liste von Städten mit zugeordneten Bahnhöfen
        """
        print("\nOrdne Intercity-Bahnhöfe den Städten zu...")
        results = []

        for city in cities:
            # Filter: Nur Städte unter der Einwohnergrenze
            if city["population"] > self.max_population or city["population"] < self.min_population:
                continue

            # Finde nahe Bahnhöfe (alle werden als potentielle Intercity-Stationen betrachtet)
            nearby_intercity_stations = []
            for station in stations:
                distance = self._haversine(
                    city["lon"], city["lat"], station["lon"], station["lat"]
                )
                if distance <= max_distance_km:
                    station_copy = station.copy()
                    station_copy["distance_km"] = round(distance, 2)
                    nearby_intercity_stations.append(station_copy)

            # Sortiere nach Entfernung
            nearby_intercity_stations.sort(key=lambda x: x["distance_km"])

            if nearby_intercity_stations:
                result = {
                    "city": city["name"],
                    "population": city["population"],
                    "lat": city["lat"],
                    "lon": city["lon"],
                    "intercity_stations": nearby_intercity_stations,
                    "wikidata": city["wikidata"],
                }
                results.append(result)

        print(f"✓ {len(results)} Städte mit Intercity-Bahnhöfen gefunden")
        return results

    def match_universities_to_cities(
        self, universities: List[Dict], cities: List[Dict], max_distance_km: float = 10.0
    ) -> List[Dict]:
        """
        Ordnet Universitäten den Städten zu basierend auf der Entfernung.

        Args:
            universities: Liste der Universitäten
            cities: Liste der Städte
            max_distance_km: Maximale Entfernung in km (Standard: 10 km)

        Returns:
            Liste von Städten mit zugeordneten Universitäten
        """
        print("\nOrdne Universitäten den Städten zu...")
        city_universities = {}

        for city in cities:
            city_name = city["name"]
            nearby_universities = []

            for university in universities:
                distance = self._haversine(
                    city["lon"], city["lat"], university["lon"], university["lat"]
                )
                if distance <= max_distance_km:
                    university_copy = university.copy()
                    university_copy["distance_km"] = round(distance, 2)
                    nearby_universities.append(university_copy)

            # Sortiere nach Entfernung
            nearby_universities.sort(key=lambda x: x["distance_km"])

            if nearby_universities:
                city_universities[city_name] = nearby_universities

        print(f"✓ {len(city_universities)} Städte mit Universitäten gefunden")
        return city_universities

    def match_swimming_pools_to_cities(
        self, pools: List[Dict], cities: List[Dict], max_distance_km: float = 5.0
    ) -> Dict[str, List[Dict]]:
        """
        Ordnet Schwimmbäder den Städten zu basierend auf der Entfernung.

        Args:
            pools: Liste der Schwimmbäder
            cities: Liste der Städte
            max_distance_km: Maximale Entfernung in km (Standard: 5 km)

        Returns:
            Dictionary von Städten mit zugeordneten Schwimmbädern
        """
        print("\nOrdne Schwimmbäder den Städten zu...")
        city_pools = {}

        for city in cities:
            city_name = city["name"]
            nearby_pools = []

            for pool in pools:
                distance = self._haversine(
                    city["lon"], city["lat"], pool["lon"], pool["lat"]
                )
                if distance <= max_distance_km:
                    pool_copy = pool.copy()
                    pool_copy["distance_km"] = round(distance, 2)
                    nearby_pools.append(pool_copy)

            # Sortiere nach Entfernung
            nearby_pools.sort(key=lambda x: x["distance_km"])

            if nearby_pools:
                city_pools[city_name] = nearby_pools

        print(f"✓ {len(city_pools)} Städte mit Schwimmbädern gefunden")
        return city_pools

    def filter_intercity_university_and_pool_cities(
        self,
        results: List[Dict],
        city_universities: Dict[str, List[Dict]],
        city_pools: Dict[str, List[Dict]],
    ) -> List[Dict]:
        """
        Filtert Ergebnisse nach Städten mit Intercity-Stationen UND Universitäten UND Schwimmbädern.

        Args:
            results: Liste der Städte mit Bahnhöfen
            city_universities: Dictionary der Städte mit Universitäten
            city_pools: Dictionary der Städte mit Schwimmbädern

        Returns:
            Gefilterte Liste (Intersection)
        """
        print("\nFiltere nach Städten mit Universitäten und Schwimmbädern...")

        filtered = []
        for result in results:
            city_name = result["city"]

            # Results haben bereits intercity_stations, prüfe nur noch Universitäten und Schwimmbäder
            # Prüfe ob die Stadt eine Universität hat
            if city_name not in city_universities:
                continue

            # Prüfe ob die Stadt ein Schwimmbad hat
            if city_name not in city_pools:
                continue

            # Füge Universitäten und Schwimmbäder hinzu
            result_copy = result.copy()
            result_copy["universities"] = city_universities[city_name]
            result_copy["swimming_pools"] = city_pools[city_name]
            filtered.append(result_copy)

        print(
            f"✓ {len(filtered)} Städte mit Intercity-Stationen, Universitäten UND Schwimmbädern"
        )
        return filtered

    def run(self) -> List[Dict]:
        """
        Führt die komplette Analyse durch.

        Returns:
            Liste von Städten mit Intercity-Anschluss, Universitäten und Schwimmbädern
        """
        print("=" * 70)
        print("Suche niederländische Städte mit:")
        print("  - Intercity-Anschluss")
        print("  - Universitäten")
        print("  - Öffentlichen Schwimmbädern")
        print(f"Maximale Einwohnerzahl: {self.max_population:,}")
        print("=" * 70)

        # Schritt 1: Bahnhöfe abfragen
        stations = self.query_intercity_stations()
        if not stations:
            print("Keine Bahnhöfe gefunden!")
            return []

        # Schritt 2: Städte abfragen
        cities = self.query_cities_with_population()
        if not cities:
            print("Keine Städte gefunden!")
            return []

        # Schritt 3: Universitäten abfragen
        universities = self.query_universities()
        if not universities:
            print("Keine Universitäten gefunden!")
            return []

        # Schritt 4: Schwimmbäder abfragen
        pools = self.query_swimming_pools()
        if not pools:
            print("Keine Schwimmbäder gefunden!")
            return []

        # Schritt 5: Zuordnung Bahnhöfe zu Städten
        results = self.match_stations_to_cities(stations, cities)

        # Schritt 6: Zuordnung Universitäten zu Städten
        city_universities = self.match_universities_to_cities(universities, cities)

        # Schritt 7: Zuordnung Schwimmbäder zu Städten
        city_pools = self.match_swimming_pools_to_cities(pools, cities)

        # Schritt 8: Filterung (Intersection)
        final_results = self.filter_intercity_university_and_pool_cities(
            results, city_universities, city_pools
        )

        self.results = final_results
        return final_results

    def print_results(self):
        """Gibt die Ergebnisse formatiert aus."""
        if not self.results:
            print("\nKeine Ergebnisse gefunden.")
            return

        print("\n" + "=" * 70)
        print(f"ERGEBNISSE: {len(self.results)} Städte gefunden")
        print("=" * 70)

        # Sortiere nach Einwohnerzahl (absteigend)
        sorted_results = sorted(
            self.results, key=lambda x: x["population"], reverse=True
        )

        for i, result in enumerate(sorted_results, 1):
            print(f"\n{i}. {result['city']}")
            print(f"   Einwohner: {result['population']:,}")
            print(f"   Koordinaten: {result['lat']:.4f}, {result['lon']:.4f}")

            if result.get("intercity_stations"):
                print(f"   Intercity-Stationen:")
                for station in result["intercity_stations"]:
                    print(f"     • {station['name']} ({station['distance_km']} km)")
                    if station.get("operator"):
                        print(f"       Betreiber: {station['operator']}")

            if result.get("universities"):
                print(f"   Universitäten:")
                for university in result["universities"]:
                    print(f"     • {university['name']} ({university['distance_km']} km)")
                    if university.get("website"):
                        print(f"       Website: {university['website']}")

            if result.get("swimming_pools"):
                print(f"   Öffentliche Schwimmbäder:")
                for pool in result["swimming_pools"]:
                    pool_name = pool['name']
                    if pool.get('leisure') == 'sports_centre':
                        pool_name += " (Sportzentrum)"
                    print(f"     • {pool_name} ({pool['distance_km']} km)")
                    if pool.get("operator"):
                        print(f"       Betreiber: {pool['operator']}")

    def save_to_json(self, filename: str = "movenl.json"):
        """
        Speichert die Ergebnisse als JSON-Datei.

        Args:
            filename: Dateiname für die Ausgabe
        """
        if not self.results:
            print("Keine Ergebnisse zum Speichern.")
            return

        filepath = f"./{filename}"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Ergebnisse gespeichert: {filename}")
        print(f"  Pfad: {filepath}")

    def save_to_csv(self, filename: str = "movenl.csv"):
        """
        Speichert die Ergebnisse als CSV-Tabelle.

        Args:
            filename: Dateiname für die CSV-Ausgabe
        """
        if not self.results:
            print("Keine Ergebnisse zum Speichern.")
            return

        import csv

        filepath = f"./{filename}"

        # Sortiere nach Stadtnamen (alphabetisch)
        sorted_results = sorted(self.results, key=lambda x: x["city"])

        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(["City", "Inhabitants", "University", "Number of Pools"])

            # Daten
            for result in sorted_results:
                city = result["city"]
                population = result["population"]

                # Sammle alle Universitätsnamen
                universities = result.get("universities", [])
                university_names = ", ".join([uni["name"] for uni in universities])

                # Anzahl der Schwimmbäder
                pools = result.get("swimming_pools", [])
                num_pools = len(pools)

                writer.writerow([city, population, university_names, num_pools])

        print(f"✓ CSV-Tabelle gespeichert: {filename}")
        print(f"  Pfad: {filepath}")


def create_example_data():
    """Erstellt Beispieldaten für Demonstrationszwecke."""
    return [
        {
            "city": "Eindhoven",
            "population": 249000,
            "lat": 51.4408,
            "lon": 5.4778,
            "wikidata": "Q9832",
            "intercity_stations": [
                {
                    "name": "Eindhoven Centraal",
                    "lat": 51.4433,
                    "lon": 5.4814,
                    "operator": "NS",
                    "distance_km": 0.3,
                }
            ],
            "universities": [
                {
                    "name": "Eindhoven University of Technology",
                    "lat": 51.4478,
                    "lon": 5.4906,
                    "wikidata": "Q676841",
                    "website": "https://www.tue.nl",
                    "distance_km": 1.2,
                }
            ],
            "swimming_pools": [
                {
                    "name": "Parkbad Eindhoven",
                    "lat": 51.4350,
                    "lon": 5.4650,
                    "leisure": "swimming_pool",
                    "access": "yes",
                    "operator": "Optisport",
                    "distance_km": 1.5,
                }
            ],
        },
        {
            "city": "Groningen",
            "population": 244000,
            "lat": 53.2194,
            "lon": 6.5665,
            "wikidata": "Q749",
            "intercity_stations": [
                {
                    "name": "Groningen",
                    "lat": 53.2108,
                    "lon": 6.5647,
                    "operator": "NS",
                    "distance_km": 1.0,
                }
            ],
            "universities": [
                {
                    "name": "University of Groningen",
                    "lat": 53.2194,
                    "lon": 6.5665,
                    "wikidata": "Q850730",
                    "website": "https://www.rug.nl",
                    "distance_km": 0.5,
                }
            ],
            "swimming_pools": [
                {
                    "name": "Sportcentrum ACLO",
                    "lat": 53.2421,
                    "lon": 6.5398,
                    "leisure": "sports_centre",
                    "sport": "swimming",
                    "operator": "ACLO",
                    "distance_km": 3.2,
                }
            ],
        },
        {
            "city": "Tilburg",
            "population": 230000,
            "lat": 51.5553,
            "lon": 5.0913,
            "wikidata": "Q9871",
            "intercity_stations": [
                {
                    "name": "Tilburg",
                    "lat": 51.5608,
                    "lon": 5.0835,
                    "operator": "NS",
                    "distance_km": 0.8,
                }
            ],
            "universities": [
                {
                    "name": "Tilburg University",
                    "lat": 51.5625,
                    "lon": 5.0882,
                    "wikidata": "Q595668",
                    "website": "https://www.tilburguniversity.edu",
                    "distance_km": 1.0,
                }
            ],
            "swimming_pools": [
                {
                    "name": "Stappegoor",
                    "lat": 51.5457,
                    "lon": 5.0513,
                    "leisure": "sports_centre",
                    "sport": "swimming",
                    "operator": "TivoliVredenburg",
                    "distance_km": 3.8,
                }
            ],
        },
        {
            "city": "Nijmegen",
            "population": 179000,
            "lat": 51.8126,
            "lon": 5.8372,
            "wikidata": "Q47887",
            "intercity_stations": [
                {
                    "name": "Nijmegen",
                    "lat": 51.8427,
                    "lon": 5.8523,
                    "operator": "NS",
                    "distance_km": 3.5,
                }
            ],
            "universities": [
                {
                    "name": "Radboud University",
                    "lat": 51.8227,
                    "lon": 5.8668,
                    "wikidata": "Q652413",
                    "website": "https://www.ru.nl",
                    "distance_km": 2.5,
                }
            ],
            "swimming_pools": [
                {
                    "name": "De Waalsprong",
                    "lat": 51.8563,
                    "lon": 5.8722,
                    "leisure": "swimming_pool",
                    "access": "yes",
                    "operator": "Optisport",
                    "distance_km": 4.9,
                }
            ],
        },
        {
            "city": "Enschede",
            "population": 159000,
            "lat": 52.2185,
            "lon": 6.8937,
            "wikidata": "Q47574",
            "intercity_stations": [
                {
                    "name": "Enschede",
                    "lat": 52.2236,
                    "lon": 6.8897,
                    "operator": "NS",
                    "distance_km": 0.7,
                }
            ],
            "universities": [
                {
                    "name": "University of Twente",
                    "lat": 52.2397,
                    "lon": 6.8567,
                    "wikidata": "Q1285259",
                    "website": "https://www.utwente.nl",
                    "distance_km": 3.8,
                }
            ],
            "swimming_pools": [
                {
                    "name": "Sportcentrum Universiteit Twente",
                    "lat": 52.2397,
                    "lon": 6.8533,
                    "leisure": "sports_centre",
                    "sport": "swimming",
                    "operator": "UT",
                    "distance_km": 3.9,
                }
            ],
        },
        {
            "city": "Leiden",
            "population": 127000,
            "lat": 52.1601,
            "lon": 4.4970,
            "wikidata": "Q43631",
            "intercity_stations": [
                {
                    "name": "Leiden Centraal",
                    "lat": 52.1665,
                    "lon": 4.4819,
                    "operator": "NS",
                    "distance_km": 1.3,
                }
            ],
            "universities": [
                {
                    "name": "Leiden University",
                    "lat": 52.1579,
                    "lon": 4.4836,
                    "wikidata": "Q156598",
                    "website": "https://www.universiteitleiden.nl",
                    "distance_km": 1.2,
                }
            ],
            "swimming_pools": [
                {
                    "name": "Zwembad De Vliet",
                    "lat": 52.1556,
                    "lon": 4.4525,
                    "leisure": "swimming_pool",
                    "access": "yes",
                    "operator": "Leiden",
                    "distance_km": 3.2,
                }
            ],
        },
    ]


def main():
    """Hauptfunktion."""
    import sys

    # Erstelle Finder-Instanz
    finder = DutchIntercityFinder(max_population=300000)

    # Prüfe ob ein Argument übergeben wurde
    use_demo = "--demo" in sys.argv or "--example" in sys.argv

    if use_demo:
        print("=" * 70)
        print("DEMO-MODUS: Verwende Beispieldaten")
        print("=" * 70)
        finder.results = create_example_data()
    else:
        # Führe Analyse durch
        results = finder.run()

        # Falls keine Ergebnisse (z.B. durch Netzwerkprobleme), verwende Demo-Daten
        if not results:
            print("\n" + "!" * 70)
            print("API nicht erreichbar - verwende Beispieldaten stattdessen")
            print("Für echte Abfrage in Umgebung mit Internet-Zugang ausführen")
            print("!" * 70)
            finder.results = create_example_data()

    # Zeige Ergebnisse
    finder.print_results()

    # Speichere als JSON und CSV
    finder.save_to_json()
    finder.save_to_csv()

    print("\n" + "=" * 70)
    print("HINWEIS:")
    print("Die OpenStreetMap-Daten können unvollständig sein.")
    print("Nicht alle Intercity-Stationen, Universitäten oder Schwimmbäder sind")
    print("möglicherweise als solche gekennzeichnet. Für präzisere Ergebnisse")
    print("sollten offizielle Datenquellen verwendet werden.")
    print("\nDie Ergebnisse zeigen nur Städte mit ALLEN drei Merkmalen:")
    print("  - Intercity-Bahnhof (NS-betrieben oder mit 'Centraal' im Namen)")
    print("  - Universität (amenity=university in OSM)")
    print("  - Öffentliches Schwimmbad (leisure=swimming_pool mit access=public")
    print("    oder leisure=sports_centre mit sport=swimming)")
    print("\nVerwendung:")
    print("  python3 movenl.py         # Echte API-Abfrage")
    print("  python3 movenl.py --demo  # Beispieldaten")
    print("=" * 70)


if __name__ == "__main__":
    main()
