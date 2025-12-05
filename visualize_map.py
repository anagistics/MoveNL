#!/usr/bin/env python3
"""
Interactive map visualization of Dutch cities with intercity stations,
universities, and swimming pools using Folium.
"""

import json
import folium
from folium import plugins


def load_data(filename="movenl.json"):
    """Load the JSON data."""
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def create_map(data):
    """
    Create an interactive Folium map with all cities and their facilities.

    Args:
        data: List of cities with their facilities

    Returns:
        Folium map object
    """
    # Center map on Netherlands
    m = folium.Map(
        location=[52.1326, 5.2913],  # Center of Netherlands
        zoom_start=7,
        tiles="OpenStreetMap"
    )

    # Create feature groups for different layers (can be toggled)
    cities_group = folium.FeatureGroup(name="Cities", show=True)
    stations_group = folium.FeatureGroup(name="Train Stations", show=True)
    universities_group = folium.FeatureGroup(name="Universities", show=True)
    pools_group = folium.FeatureGroup(name="Swimming Pools", show=True)
    connections_group = folium.FeatureGroup(name="Connections", show=False)

    # Color scheme
    colors = {
        "city": "red",
        "station": "blue",
        "university": "green",
        "pool": "lightblue"
    }

    # Process each city
    for city_data in data:
        city_name = city_data["city"]
        city_lat = city_data["lat"]
        city_lon = city_data["lon"]
        population = city_data["population"]

        # City marker (larger, distinct)
        city_popup = f"""
        <div style="font-family: Arial; min-width: 200px;">
            <h3 style="margin: 0 0 10px 0; color: #d63031;">{city_name}</h3>
            <p style="margin: 5px 0;"><b>Population:</b> {population:,}</p>
            <p style="margin: 5px 0;"><b>Stations:</b> {len(city_data.get('intercity_stations', []))}</p>
            <p style="margin: 5px 0;"><b>Universities:</b> {len(city_data.get('universities', []))}</p>
            <p style="margin: 5px 0;"><b>Swimming Pools:</b> {len(city_data.get('swimming_pools', []))}</p>
        </div>
        """

        folium.Marker(
            location=[city_lat, city_lon],
            popup=folium.Popup(city_popup, max_width=300),
            tooltip=f"{city_name} ({population:,} inhabitants)",
            icon=folium.Icon(color=colors["city"], icon="home", prefix="fa")
        ).add_to(cities_group)

        # Add train stations
        for station in city_data.get("intercity_stations", []):
            station_popup = f"""
            <div style="font-family: Arial; min-width: 180px;">
                <h4 style="margin: 0 0 8px 0; color: #0984e3;">{station['name']}</h4>
                <p style="margin: 3px 0;"><b>Distance from {city_name}:</b> {station['distance_km']} km</p>
                {f"<p style='margin: 3px 0;'><b>Operator:</b> {station['operator']}</p>" if station.get('operator') else ""}
                {f"<p style='margin: 3px 0;'><b>Network:</b> {station['network']}</p>" if station.get('network') else ""}
            </div>
            """

            folium.Marker(
                location=[station["lat"], station["lon"]],
                popup=folium.Popup(station_popup, max_width=300),
                tooltip=station["name"],
                icon=folium.Icon(color=colors["station"], icon="train", prefix="fa")
            ).add_to(stations_group)

            # Add connection line
            folium.PolyLine(
                locations=[[city_lat, city_lon], [station["lat"], station["lon"]]],
                color="blue",
                weight=1,
                opacity=0.4,
                dash_array="5"
            ).add_to(connections_group)

        # Add universities
        for uni in city_data.get("universities", []):
            uni_popup = f"""
            <div style="font-family: Arial; min-width: 180px;">
                <h4 style="margin: 0 0 8px 0; color: #00b894;">{uni['name']}</h4>
                <p style="margin: 3px 0;"><b>Distance from {city_name}:</b> {uni['distance_km']} km</p>
                {f"<p style='margin: 3px 0;'><b>Website:</b> <a href='{uni['website']}' target='_blank'>Link</a></p>" if uni.get('website') else ""}
                {f"<p style='margin: 3px 0;'><b>Wikidata:</b> <a href='https://www.wikidata.org/wiki/{uni['wikidata']}' target='_blank'>{uni['wikidata']}</a></p>" if uni.get('wikidata') else ""}
            </div>
            """

            folium.Marker(
                location=[uni["lat"], uni["lon"]],
                popup=folium.Popup(uni_popup, max_width=300),
                tooltip=uni["name"],
                icon=folium.Icon(color=colors["university"], icon="graduation-cap", prefix="fa")
            ).add_to(universities_group)

            # Add connection line
            folium.PolyLine(
                locations=[[city_lat, city_lon], [uni["lat"], uni["lon"]]],
                color="green",
                weight=1,
                opacity=0.4,
                dash_array="5"
            ).add_to(connections_group)

        # Add swimming pools
        for pool in city_data.get("swimming_pools", []):
            pool_type = " (Sports Centre)" if pool.get('leisure') == 'sports_centre' else ""
            pool_popup = f"""
            <div style="font-family: Arial; min-width: 180px;">
                <h4 style="margin: 0 0 8px 0; color: #74b9ff;">{pool['name']}{pool_type}</h4>
                <p style="margin: 3px 0;"><b>Distance from {city_name}:</b> {pool['distance_km']} km</p>
                {f"<p style='margin: 3px 0;'><b>Type:</b> {pool['leisure']}</p>" if pool.get('leisure') else ""}
                {f"<p style='margin: 3px 0;'><b>Operator:</b> {pool['operator']}</p>" if pool.get('operator') else ""}
                {f"<p style='margin: 3px 0;'><b>Website:</b> <a href='{pool['website']}' target='_blank'>Link</a></p>" if pool.get('website') else ""}
            </div>
            """

            folium.Marker(
                location=[pool["lat"], pool["lon"]],
                popup=folium.Popup(pool_popup, max_width=300),
                tooltip=pool["name"],
                icon=folium.Icon(color=colors["pool"], icon="swimmer", prefix="fa")
            ).add_to(pools_group)

            # Add connection line
            folium.PolyLine(
                locations=[[city_lat, city_lon], [pool["lat"], pool["lon"]]],
                color="lightblue",
                weight=1,
                opacity=0.4,
                dash_array="5"
            ).add_to(connections_group)

    # Add all feature groups to map
    cities_group.add_to(m)
    stations_group.add_to(m)
    universities_group.add_to(m)
    pools_group.add_to(m)
    connections_group.add_to(m)

    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)

    # Add fullscreen button
    plugins.Fullscreen(
        position="topright",
        title="Fullscreen",
        title_cancel="Exit fullscreen",
        force_separate_button=True
    ).add_to(m)

    # Add search functionality
    plugins.Search(
        layer=cities_group,
        search_label="tooltip",
        placeholder="Search cities...",
        collapsed=True
    ).add_to(m)

    # Add minimap
    plugins.MiniMap(toggle_display=True).add_to(m)

    # Add measurement tool
    plugins.MeasureControl(
        position="topleft",
        primary_length_unit="kilometers",
        secondary_length_unit="miles"
    ).add_to(m)

    # Add title/legend
    title_html = '''
    <div style="position: fixed;
                top: 10px; left: 60px; width: 400px; height: auto;
                background-color: white; border: 2px solid grey; z-index: 9999;
                font-size: 14px; padding: 10px; border-radius: 5px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <h4 style="margin: 0 0 10px 0;">Dutch Cities with University Access</h4>
        <p style="margin: 5px 0; font-size: 12px;">
            <i class="fa fa-home" style="color: red;"></i> Cities (< 300k pop.) |
            <i class="fa fa-train" style="color: blue;"></i> Train Stations |
            <i class="fa fa-graduation-cap" style="color: green;"></i> Universities |
            <i class="fa fa-swimmer" style="color: lightblue;"></i> Swimming Pools
        </p>
        <p style="margin: 5px 0; font-size: 11px; color: #666;">
            Click markers for details. Toggle layers using the control panel.
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    return m


def main():
    """Main function."""
    print("Loading data from movenl.json...")
    data = load_data("movenl.json")
    print(f"✓ Loaded {len(data)} cities")

    print("\nCreating interactive map...")
    map_obj = create_map(data)

    output_file = "movenl_map.html"
    print(f"Saving map to {output_file}...")
    map_obj.save(output_file)

    print(f"\n✓ Map created successfully!")
    print(f"  File: {output_file}")
    print(f"\nOpen '{output_file}' in your web browser to view the interactive map.")
    print("\nFeatures:")
    print("  - Toggle different layers (cities, stations, universities, pools)")
    print("  - Click markers for detailed information")
    print("  - Search for cities")
    print("  - Measure distances")
    print("  - Fullscreen mode")
    print("  - Show/hide connection lines between cities and facilities")


if __name__ == "__main__":
    main()
