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

    # Add terrain/elevation tile layers
    folium.TileLayer(
        tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attr='Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap',
        name='Topographic (Elevation)',
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg',
        attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.',
        name='Terrain',
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)

    # Add flood risk overlay from PDOK
    flood_risk_wms = folium.WmsTileLayer(
        url='https://service.pdok.nl/rws/overstromingen-risicogebied/wms/v1_0',
        layers='NZ.RiskZone',
        name='Flood Risk Areas (PDOK)',
        fmt='image/png',
        transparent=True,
        overlay=True,
        control=True,
        attr='Rijkswaterstaat via PDOK',
        show=True
    )
    flood_risk_wms.add_to(m)

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

    # Determine color scale for house prices
    house_prices = [c.get("avg_house_price") for c in data if c.get("avg_house_price")]
    if house_prices:
        min_price = min(house_prices)
        max_price = max(house_prices)

        def get_price_color(price):
            """Get color based on house price."""
            if price is None:
                return "gray"
            # Green (cheap) to red (expensive)
            if price < 300000:
                return "green"
            elif price < 400000:
                return "lightgreen"
            elif price < 500000:
                return "orange"
            else:
                return "red"
    else:
        def get_price_color(price):
            return "red"

    # Process each city
    for city_data in data:
        city_name = city_data["city"]
        city_lat = city_data["lat"]
        city_lon = city_data["lon"]
        population = city_data["population"]
        elevation = city_data.get("elevation")
        house_price = city_data.get("avg_house_price")
        temp_increase = city_data.get("temp_increase_2050")
        summer_temp_2050 = city_data.get("summer_avg_2050")

        # Build elevation display
        elevation_html = ""
        elevation_tooltip = ""
        if elevation is not None:
            elevation_html = f"<p style='margin: 5px 0;'><b>Elevation:</b> {elevation:.1f} m</p>"
            elevation_tooltip = f", {elevation:.1f}m"

        # Build house price display
        house_price_html = ""
        if house_price:
            house_price_html = f"<p style='margin: 5px 0;'><b>Avg House Price:</b> €{house_price:,.0f}</p>"

        # Build temperature projection display
        temp_html = ""
        if temp_increase and summer_temp_2050:
            temp_html = f"""
            <p style='margin: 5px 0;'><b>Climate 2050:</b></p>
            <p style='margin: 3px 0 3px 20px;'>• Temperature increase: +{temp_increase}°C</p>
            <p style='margin: 3px 0 3px 20px;'>• Summer avg: {summer_temp_2050}°C</p>
            """

        # City marker (color-coded by house price)
        marker_color = get_price_color(house_price)

        city_popup = f"""
        <div style="font-family: Arial; min-width: 220px;">
            <h3 style="margin: 0 0 10px 0; color: #d63031;">{city_name}</h3>
            <p style="margin: 5px 0;"><b>Population:</b> {population:,}</p>
            {elevation_html}
            {house_price_html}
            {temp_html}
            <hr style="margin: 10px 0; border: none; border-top: 1px solid #ddd;">
            <p style="margin: 5px 0;"><b>Facilities:</b></p>
            <p style="margin: 3px 0 3px 15px;">• Stations: {len(city_data.get('intercity_stations', []))}</p>
            <p style="margin: 3px 0 3px 15px;">• Universities: {len(city_data.get('universities', []))}</p>
            <p style="margin: 3px 0 3px 15px;">• Swimming Pools: {len(city_data.get('swimming_pools', []))}</p>
        </div>
        """

        folium.Marker(
            location=[city_lat, city_lon],
            popup=folium.Popup(city_popup, max_width=350),
            tooltip=f"{city_name} ({population:,} inhabitants{elevation_tooltip})",
            icon=folium.Icon(color=marker_color, icon="home", prefix="fa")
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
                top: 10px; left: 60px; width: 450px; height: auto;
                background-color: white; border: 2px solid grey; z-index: 9999;
                font-size: 14px; padding: 10px; border-radius: 5px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <h4 style="margin: 0 0 10px 0;">Dutch Cities - Climate & Housing Analysis</h4>

        <p style="margin: 8px 0 4px 0; font-weight: bold; font-size: 12px;">Facilities:</p>
        <p style="margin: 2px 0; font-size: 11px;">
            <i class="fa fa-train" style="color: blue;"></i> Train Stations |
            <i class="fa fa-graduation-cap" style="color: green;"></i> Universities |
            <i class="fa fa-swimmer" style="color: lightblue;"></i> Swimming Pools
        </p>

        <p style="margin: 8px 0 4px 0; font-weight: bold; font-size: 12px;">City Markers (by House Price):</p>
        <p style="margin: 2px 0; font-size: 11px;">
            <i class="fa fa-home" style="color: green;"></i> < €300k |
            <i class="fa fa-home" style="color: lightgreen;"></i> €300-400k |
            <i class="fa fa-home" style="color: orange;"></i> €400-500k |
            <i class="fa fa-home" style="color: red;"></i> > €500k
        </p>

        <p style="margin: 8px 0 0 0; font-size: 10px; color: #666; font-style: italic;">
            Includes: flood risk zones, house prices, 2050 climate projections<br/>
            Click markers for detailed info. Toggle layers in control panel.
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
