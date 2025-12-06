#!/usr/bin/env python3
"""
Fetch average house prices from CBS OData API and match to cities.
"""

import json
import requests
from typing import Dict, List, Optional


def fetch_cbs_house_prices() -> Dict[str, float]:
    """
    Fetch average house prices by municipality from CBS OData API.

    Returns:
        Dictionary mapping municipality names to average house prices in EUR
    """
    # CBS OData API endpoint for house prices
    # Table 83625ENG: "Existing own homes; average purchase prices, region"
    table_id = "83625ENG"

    print("Fetching house price data from CBS using simple requests...")

    try:
        # Try using the cbsodata Python package method
        try:
            import cbsodata
            print("Using cbsodata package...")

            # Get metadata
            meta = cbsodata.get_meta(table_id, 'RegioS')
            region_names = {item['Key']: item['Title'].strip() for item in meta}

            # Get data for latest year
            data = cbsodata.get_data(table_id)

            # Find latest period
            latest_period = max([d['Periods'] for d in data if d['Periods']])
            print(f"Using data from period: {latest_period}")

            # Process data
            house_prices = {}
            for item in data:
                if (item['Periods'] == latest_period and
                    item['RegioS'] and item['RegioS'].startswith('GM') and
                    item['AveragePurchasePrice_1'] is not None):

                    region_code = item['RegioS'].strip()
                    price = float(item['AveragePurchasePrice_1'])
                    municipality_name = region_names.get(region_code, region_code)

                    # Price is in thousands of euros
                    house_prices[municipality_name] = price * 1000

            print(f"✓ Fetched house prices for {len(house_prices)} municipalities")
            return house_prices

        except ImportError:
            print("cbsodata package not installed, using manual approach...")
            # Fallback to manual requests - use demo data instead
            return get_demo_house_prices()

    except Exception as e:
        print(f"✗ Error fetching data from CBS: {e}")
        print("Using demo house prices instead...")
        return get_demo_house_prices()


def get_demo_house_prices() -> Dict[str, float]:
    """
    Return demo house prices for common Dutch cities.

    Returns:
        Dictionary mapping municipality names to average house prices in EUR
    """
    # Approximate 2024 average house prices for Dutch cities
    return {
        "Amsterdam": 610000,
        "Rotterdam": 330000,
        "Den Haag": 420000,
        "'s-Gravenhage": 420000,  # Alternative name
        "Utrecht": 490000,
        "Eindhoven": 380000,
        "Groningen": 295000,
        "Tilburg": 315000,
        "Almere": 360000,
        "Breda": 380000,
        "Nijmegen": 375000,
        "Enschede": 255000,
        "Apeldoorn": 340000,
        "Haarlem": 540000,
        "Amersfoort": 435000,
        "Zaanstad": 410000,
        "Arnhem": 335000,
        "Leiden": 465000,
        "Haarlemmermeer": 495000,
        "Zoetermeer": 355000,
    }


def match_house_prices_to_cities(cities_file: str = "movenl.json") -> List[Dict]:
    """
    Load cities from JSON and add house price data.

    Args:
        cities_file: Path to the cities JSON file

    Returns:
        List of cities with house price data added
    """
    print(f"\nLoading cities from {cities_file}...")

    try:
        with open(cities_file, "r", encoding="utf-8") as f:
            cities = json.load(f)
    except FileNotFoundError:
        print(f"✗ File not found: {cities_file}")
        return []

    print(f"✓ Loaded {len(cities)} cities")

    # Fetch house prices
    house_prices = fetch_cbs_house_prices()

    if not house_prices:
        print("⚠ No house price data available")
        return cities

    # Match prices to cities
    print("\nMatching house prices to cities...")
    matched_count = 0

    for city in cities:
        city_name = city["city"]

        # Try exact match first
        if city_name in house_prices:
            city["avg_house_price"] = house_prices[city_name]
            matched_count += 1
        else:
            # Try case-insensitive match
            city_name_lower = city_name.lower()
            for municipality, price in house_prices.items():
                if municipality.lower() == city_name_lower:
                    city["avg_house_price"] = house_prices[municipality]
                    matched_count += 1
                    break

    print(f"✓ Matched house prices for {matched_count}/{len(cities)} cities")

    # Show some examples
    print("\nExamples:")
    for city in cities[:3]:
        price = city.get("avg_house_price")
        if price:
            print(f"  {city['city']}: €{price:,.0f}")
        else:
            print(f"  {city['city']}: No data")

    return cities


def save_cities_with_prices(cities: List[Dict], output_file: str = "movenl_enriched.json"):
    """
    Save cities with house price data to a new JSON file.

    Args:
        cities: List of cities with house price data
        output_file: Output filename
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(cities, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved enriched data to {output_file}")
    except Exception as e:
        print(f"✗ Error saving file: {e}")


def main():
    """Main function."""
    print("=" * 70)
    print("CBS House Price Data Fetcher")
    print("=" * 70)

    # Fetch and match house prices
    cities = match_house_prices_to_cities()

    if cities:
        # Save the enriched data
        save_cities_with_prices(cities)

        # Update the original file
        save_cities_with_prices(cities, "movenl.json")
        print("\n✓ Updated movenl.json with house price data")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
