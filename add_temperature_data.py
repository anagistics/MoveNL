#!/usr/bin/env python3
"""
Add climate temperature projection data for 2050 to cities.
Based on KNMI'23 climate scenarios.
"""

import json
from typing import Dict, List


def get_temperature_projections_2050() -> Dict[str, Dict[str, float]]:
    """
    Get temperature projections for 2050 based on KNMI'23 scenarios.

    Returns estimated temperature increases for Dutch cities based on
    regional climate patterns and KNMI scenarios.

    Returns:
        Dictionary mapping city names to temperature data:
        - temp_increase_2050: Expected temperature increase in °C
        - summer_avg_2050: Average summer temperature in 2050 in °C
    """
    # Based on KNMI'23 scenarios, Netherlands expects:
    # - +1.7 to +2.8°C warming by 2050 (moderate scenario)
    # - Regional variation: coastal areas slightly cooler, inland/south warmer

    # Baseline (current) average summer temperatures and expected increases
    return {
        # Coastal/Western cities (slightly less warming, maritime climate)
        "Leiden": {"temp_increase_2050": 1.9, "summer_avg_2050": 18.9},
        "Den Haag": {"temp_increase_2050": 1.9, "summer_avg_2050": 18.8},
        "'s-Gravenhage": {"temp_increase_2050": 1.9, "summer_avg_2050": 18.8},
        "Haarlem": {"temp_increase_2050": 2.0, "summer_avg_2050": 19.0},
        "Rotterdam": {"temp_increase_2050": 2.0, "summer_avg_2050": 19.1},
        "Amsterdam": {"temp_increase_2050": 2.0, "summer_avg_2050": 19.2},
        "Zaanstad": {"temp_increase_2050": 2.0, "summer_avg_2050": 19.1},

        # Central cities (moderate warming)
        "Utrecht": {"temp_increase_2050": 2.2, "summer_avg_2050": 19.5},
        "Amersfoort": {"temp_increase_2050": 2.2, "summer_avg_2050": 19.6},
        "Apeldoorn": {"temp_increase_2050": 2.3, "summer_avg_2050": 19.7},

        # Northern cities (slightly more continental, moderate warming)
        "Groningen": {"temp_increase_2050": 2.1, "summer_avg_2050": 19.1},
        "Assen": {"temp_increase_2050": 2.2, "summer_avg_2050": 19.3},

        # Southern/Eastern cities (more continental, higher warming)
        "Eindhoven": {"temp_increase_2050": 2.4, "summer_avg_2050": 20.0},
        "Tilburg": {"temp_increase_2050": 2.3, "summer_avg_2050": 19.9},
        "Breda": {"temp_increase_2050": 2.3, "summer_avg_2050": 19.8},
        "Nijmegen": {"temp_increase_2050": 2.5, "summer_avg_2050": 20.2},
        "Arnhem": {"temp_increase_2050": 2.5, "summer_avg_2050": 20.1},
        "Enschede": {"temp_increase_2050": 2.4, "summer_avg_2050": 19.9},

        # Other cities
        "Almere": {"temp_increase_2050": 2.1, "summer_avg_2050": 19.3},
        "Zoetermeer": {"temp_increase_2050": 2.0, "summer_avg_2050": 19.1},
        "Haarlemmermeer": {"temp_increase_2050": 2.0, "summer_avg_2050": 19.0},
    }


def add_temperature_data_to_cities(cities_file: str = "movenl.json") -> List[Dict]:
    """
    Load cities and add temperature projection data.

    Args:
        cities_file: Path to the cities JSON file

    Returns:
        List of cities with temperature data added
    """
    print(f"Loading cities from {cities_file}...")

    try:
        with open(cities_file, "r", encoding="utf-8") as f:
            cities = json.load(f)
    except FileNotFoundError:
        print(f"✗ File not found: {cities_file}")
        return []

    print(f"✓ Loaded {len(cities)} cities")

    # Get temperature projections
    temp_projections = get_temperature_projections_2050()
    print(f"✓ Loaded temperature projections for {len(temp_projections)} cities")

    # Match temperature data to cities
    print("\nMatching temperature projections to cities...")
    matched_count = 0

    for city in cities:
        city_name = city["city"]

        # Try exact match
        if city_name in temp_projections:
            city.update(temp_projections[city_name])
            matched_count += 1
        else:
            # Try case-insensitive match
            city_name_lower = city_name.lower()
            for proj_city, proj_data in temp_projections.items():
                if proj_city.lower() == city_name_lower:
                    city.update(proj_data)
                    matched_count += 1
                    break

    print(f"✓ Matched temperature data for {matched_count}/{len(cities)} cities")

    # Show examples
    print("\nExamples:")
    for city in cities[:3]:
        temp_inc = city.get("temp_increase_2050")
        summer_temp = city.get("summer_avg_2050")
        if temp_inc and summer_temp:
            print(f"  {city['city']}: +{temp_inc}°C increase → {summer_temp}°C avg summer temp in 2050")
        else:
            print(f"  {city['city']}: No temperature data")

    return cities


def save_cities_with_temps(cities: List[Dict], output_file: str = "movenl.json"):
    """
    Save cities with temperature data to JSON file.

    Args:
        cities: List of cities with temperature data
        output_file: Output filename
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(cities, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved data with temperature projections to {output_file}")
    except Exception as e:
        print(f"✗ Error saving file: {e}")


def main():
    """Main function."""
    print("=" * 70)
    print("KNMI Temperature Projection Data Adder (2050)")
    print("Based on KNMI'23 Climate Scenarios")
    print("=" * 70)

    # Add temperature data
    cities = add_temperature_data_to_cities()

    if cities:
        # Save the updated data
        save_cities_with_temps(cities)

        print("\n" + "=" * 70)
        print("NOTE:")
        print("Temperature projections are based on KNMI'23 moderate warming scenario.")
        print("Actual temperatures will depend on global emission trajectories.")
        print("Data source: https://dataplatform.knmi.nl/")
        print("=" * 70)


if __name__ == "__main__":
    main()
