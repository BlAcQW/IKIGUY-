"""
Fixed branch list for ChurchFlow.

This module contains the predefined list of church branches.
Branches cannot be created, edited, or deleted through the admin interface.
"""

from typing import List, Dict, Any

# Fixed list of church branches
FIXED_BRANCHES: List[Dict[str, Any]] = [
    # Greater Accra Region - Adenta Area
    {"name": "Adenta", "location": "Adenta, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Ashaiman", "location": "Ashaiman, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Madina", "location": "Madina, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Nmai Dzorn", "location": "Nmai Dzorn, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Oyibi", "location": "Oyibi, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Sun City, West Adenta", "location": "Sun City, West Adenta, Ghana", "region": "Greater Accra"},
    {"name": "Haatso", "location": "Haatso, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Westlands", "location": "Westlands, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Ashaley Botwe", "location": "Ashaley Botwe, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Dodowa", "location": "Dodowa, Greater Accra, Ghana", "region": "Greater Accra"},

    # Greater Accra Region - Accra Central
    {"name": "Ablekuma", "location": "Ablekuma, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Pantang", "location": "Pantang, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Dome", "location": "Dome, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Ayikumah", "location": "Ayikumah, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Amasaman-Fise", "location": "Amasaman-Fise, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Agbogba", "location": "Agbogba, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Kwabenya", "location": "Kwabenya, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Kofi Kwei", "location": "Kofi Kwei, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Dansoman", "location": "Dansoman, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Abeka Lapaz", "location": "Abeka Lapaz, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Weija", "location": "Weija, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Alpha Beta, Dansoman", "location": "Alpha Beta, Dansoman, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Tesano", "location": "Tesano, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Bubuashi", "location": "Bubuashi, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Baatsona", "location": "Baatsona, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Teshie Nungua", "location": "Teshie Nungua, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Osu", "location": "Osu, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Kokomlemle", "location": "Kokomlemle, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Achimota", "location": "Achimota, Accra, Ghana", "region": "Greater Accra"},
    {"name": "East Airport", "location": "East Airport, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Mallam Gbawe", "location": "Mallam Gbawe, Accra, Ghana", "region": "Greater Accra"},

    # Eastern Region
    {"name": "New Abirim", "location": "New Abirim, Eastern Region, Ghana", "region": "Eastern"},
    {"name": "Akwatia", "location": "Akwatia, Eastern Region, Ghana", "region": "Eastern"},
    {"name": "Nsawam", "location": "Nsawam, Eastern Region, Ghana", "region": "Eastern"},
    {"name": "Koforidua", "location": "Koforidua, Eastern Region, Ghana", "region": "Eastern"},
    {"name": "Akim Asene/Akim Oda", "location": "Akim Asene/Akim Oda, Eastern Region, Ghana", "region": "Eastern"},
    {"name": "Suhum", "location": "Suhum, Eastern Region, Ghana", "region": "Eastern"},

    # Tema Area
    {"name": "Tema Com #9", "location": "Tema Community 9, Ghana", "region": "Greater Accra"},
    {"name": "ACI Nhyira (Akan Church)", "location": "Tema, Ghana", "region": "Greater Accra"},
    {"name": "Michel Camp", "location": "Michel Camp, Tema, Ghana", "region": "Greater Accra"},
    {"name": "Tema Manhean", "location": "Tema Manhean, Ghana", "region": "Greater Accra"},
    {"name": "Love Hill Chapel", "location": "Tema, Ghana", "region": "Greater Accra"},
    {"name": "Lashibi Branch", "location": "Lashibi, Tema, Ghana", "region": "Greater Accra"},
    {"name": "Tema Com #2", "location": "Tema Community 2, Ghana", "region": "Greater Accra"},
    {"name": "Trasacco", "location": "Trasacco, Accra, Ghana", "region": "Greater Accra"},
    {"name": "Tema Comm 25", "location": "Tema Community 25, Ghana", "region": "Greater Accra"},

    # Greater Accra - Outlying Areas
    {"name": "Afienya Mataheko", "location": "Afienya Mataheko, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Adjei-Kojo", "location": "Adjei-Kojo, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Akuse Junction", "location": "Akuse Junction, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Jerusalem-Afienya", "location": "Jerusalem-Afienya, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Kakasunanka", "location": "Kakasunanka, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Kasoa", "location": "Kasoa, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Pokuase", "location": "Pokuase, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Buduburam", "location": "Buduburam, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Aplaku", "location": "Aplaku, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Kokrobite", "location": "Kokrobite, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Medie", "location": "Medie, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Agblezaa", "location": "Agblezaa, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "Dawhenya", "location": "Dawhenya, Greater Accra, Ghana", "region": "Greater Accra"},
    {"name": "John Teye, Ofankor", "location": "John Teye, Ofankor, Ghana", "region": "Greater Accra"},
    {"name": "Shalom Estates", "location": "Shalom Estates, Ghana", "region": "Greater Accra"},

    # Volta Region
    {"name": "Ho", "location": "Ho, Volta Region, Ghana", "region": "Volta"},
    {"name": "Sogakope", "location": "Sogakope, Volta Region, Ghana", "region": "Volta"},
    {"name": "Tafi Agome", "location": "Tafi Agome, Volta Region, Ghana", "region": "Volta"},
    {"name": "Aflao", "location": "Aflao, Volta Region, Ghana", "region": "Volta"},
    {"name": "Hohoe", "location": "Hohoe, Volta Region, Ghana", "region": "Volta"},
    {"name": "Agortime", "location": "Agortime, Volta Region, Ghana", "region": "Volta"},

    # Ashanti Region
    {"name": "Bantama", "location": "Bantama, Kumasi, Ghana", "region": "Ashanti"},
    {"name": "Kwamo", "location": "Kwamo, Kumasi, Ghana", "region": "Ashanti"},
    {"name": "Ridge Community", "location": "Ridge Community, Kumasi, Ghana", "region": "Ashanti"},
    {"name": "Santasi", "location": "Santasi, Kumasi, Ghana", "region": "Ashanti"},
    {"name": "Obuasi", "location": "Obuasi, Ashanti Region, Ghana", "region": "Ashanti"},
    {"name": "Twedie", "location": "Twedie, Kumasi, Ghana", "region": "Ashanti"},
    {"name": "Apitiso", "location": "Apitiso, Kumasi, Ghana", "region": "Ashanti"},
    {"name": "Apitikooko", "location": "Apitikooko, Kumasi, Ghana", "region": "Ashanti"},
    {"name": "Kwapia", "location": "Kwapia, Kumasi, Ghana", "region": "Ashanti"},
    {"name": "Abrepo", "location": "Abrepo, Kumasi, Ghana", "region": "Ashanti"},

    # Brong-Ahafo Region
    {"name": "Sunyani", "location": "Sunyani, Brong-Ahafo Region, Ghana", "region": "Brong-Ahafo"},
    {"name": "Techiman", "location": "Techiman, Brong-Ahafo Region, Ghana", "region": "Brong-Ahafo"},

    # Northern Region
    {"name": "Tamale", "location": "Tamale, Northern Region, Ghana", "region": "Northern"},

    # Central Region
    {"name": "Winneba", "location": "Winneba, Central Region, Ghana", "region": "Central"},
    {"name": "Agona Swedru", "location": "Agona Swedru, Central Region, Ghana", "region": "Central"},
    {"name": "Cape Coast", "location": "Cape Coast, Central Region, Ghana", "region": "Central"},
    {"name": "ACC Ogbojo", "location": "Ogbojo, Central Region, Ghana", "region": "Central"},

    # Western Region
    {"name": "Takoradi", "location": "Takoradi, Western Region, Ghana", "region": "Western"},
    {"name": "Nzema", "location": "Nzema, Western Region, Ghana", "region": "Western"},

    # Special Locations
    {"name": "Prayer Mountain, Berekusu", "location": "Prayer Mountain, Berekusu, Ghana", "region": "Greater Accra"},

    # Training Programs & Special Groups
    {"name": "SUCCESSFUL MINISTERS ACADEMY", "location": "Action Chapel International, Accra, Ghana", "region": "Training Programs"},
    {"name": "DTS Alumni", "location": "Action Chapel International, Accra, Ghana", "region": "Training Programs"},
    {"name": "DTS Students", "location": "Action Chapel International, Accra, Ghana", "region": "Training Programs"},

    # Benin
    {"name": "Sodjeatinmey", "location": "Sodjeatinmey, Benin", "region": "Benin"},
    {"name": "Hinkoude", "location": "Hinkoude, Benin", "region": "Benin"},
    {"name": "Tankpe", "location": "Tankpe, Benin", "region": "Benin"},
    {"name": "Parakou", "location": "Parakou, Benin", "region": "Benin"},
    {"name": "Ganhi", "location": "Ganhi, Benin", "region": "Benin"},
    {"name": "Calavi-Gbodjo", "location": "Calavi-Gbodjo, Benin", "region": "Benin"},
    {"name": "Calavi Zoca", "location": "Calavi Zoca, Benin", "region": "Benin"},
    {"name": "Godomey", "location": "Godomey, Benin", "region": "Benin"},
    {"name": "Segbeya", "location": "Segbeya, Benin", "region": "Benin"},
    {"name": "Kohounou", "location": "Kohounou, Benin", "region": "Benin"},

    # Ivory Coast (Côte d'Ivoire)
    {"name": "Angre, Cocodey", "location": "Angre, Cocodey, Abidjan, Ivory Coast", "region": "Ivory Coast"},
    {"name": "Youpougon", "location": "Youpougon, Abidjan, Ivory Coast", "region": "Ivory Coast"},
    {"name": "Rivera-Palmeraie", "location": "Rivera-Palmeraie, Abidjan, Ivory Coast", "region": "Ivory Coast"},
    {"name": "Gonzagueville", "location": "Gonzagueville, Ivory Coast", "region": "Ivory Coast"},

    # Togo
    {"name": "Lome, Togo", "location": "Lome, Togo", "region": "Togo"},
    {"name": "Kpalime", "location": "Kpalime, Togo", "region": "Togo"},

    # Liberia
    {"name": "Liberia", "location": "Liberia", "region": "Liberia"},

    # Sierra Leone
    {"name": "Sierra Leone", "location": "Sierra Leone", "region": "Sierra Leone"},

    # United Kingdom
    {"name": "Brixton, South London", "location": "Brixton, South London, UK", "region": "United Kingdom"},
    {"name": "East London", "location": "East London, UK", "region": "United Kingdom"},
    {"name": "Wembley", "location": "Wembley, London, UK", "region": "United Kingdom"},
    {"name": "Southend-on-Sea", "location": "Southend-on-Sea, UK", "region": "United Kingdom"},
    {"name": "CC1 Thornton Heath", "location": "Thornton Heath, London, UK", "region": "United Kingdom"},
    {"name": "CC2 Milton Keynes", "location": "Milton Keynes, UK", "region": "United Kingdom"},
    {"name": "CC3 Kilburn Park", "location": "Kilburn Park, London, UK", "region": "United Kingdom"},
    {"name": "CC4 Palmers Green", "location": "Palmers Green, London, UK", "region": "United Kingdom"},
    {"name": "CC6 Chiswick", "location": "Chiswick, London, UK", "region": "United Kingdom"},
    {"name": "Milton Keynes", "location": "Milton Keynes, UK", "region": "United Kingdom"},
    {"name": "Northampton", "location": "Northampton, UK", "region": "United Kingdom"},

    # Italy
    {"name": "Brescia", "location": "Brescia, Italy", "region": "Italy"},
    {"name": "Vicenza", "location": "Vicenza, Italy", "region": "Italy"},

    # Germany
    {"name": "Hamburg", "location": "Hamburg, Germany", "region": "Germany"},
    {"name": "Westerland, Germany", "location": "Westerland, Germany", "region": "Germany"},

    # France
    {"name": "Paris, France", "location": "Paris, France", "region": "France"},

    # United States
    {"name": "New York", "location": "New York, NY, USA", "region": "United States"},
    {"name": "Perry Hall", "location": "Perry Hall, MD, USA", "region": "United States"},
    {"name": "Baltimore, Maryland", "location": "Baltimore, Maryland, USA", "region": "United States"},
    {"name": "Silver Spring, Maryland", "location": "Silver Spring, Maryland, USA", "region": "United States"},
    {"name": "North Carolina", "location": "North Carolina, USA", "region": "United States"},
    {"name": "Reading, Pennsylvania", "location": "Reading, Pennsylvania, USA", "region": "United States"},
    {"name": "Tulsa, Oklahoma", "location": "Tulsa, Oklahoma, USA", "region": "United States"},
    {"name": "Alexandria, Virginia", "location": "Alexandria, Virginia, USA", "region": "United States"},
    {"name": "Dallas, Texas", "location": "Dallas, Texas, USA", "region": "United States"},
    {"name": "Nashville, Tennessee", "location": "Nashville, Tennessee, USA", "region": "United States"},

    # United Arab Emirates
    {"name": "Abu Dhabi", "location": "Abu Dhabi, UAE", "region": "UAE"},

    # Canada
    {"name": "Canada", "location": "Canada", "region": "Canada"},
]


def get_all_branches() -> List[Dict[str, Any]]:
    """
    Get the complete list of fixed branches.

    Returns:
        List[Dict[str, Any]]: List of all branch dictionaries.
    """
    return FIXED_BRANCHES


def get_branch_by_name(name: str) -> Dict[str, Any] | None:
    """
    Get a branch by its name.

    Args:
        name (str): The branch name to search for.

    Returns:
        Dict[str, Any] | None: The branch dictionary if found, None otherwise.
    """
    for branch in FIXED_BRANCHES:
        if branch["name"].lower() == name.lower():
            return branch
    return None


def get_branches_by_region(region: str) -> List[Dict[str, Any]]:
    """
    Get all branches in a specific region.

    Args:
        region (str): The region name to filter by.

    Returns:
        List[Dict[str, Any]]: List of branches in the specified region.
    """
    return [branch for branch in FIXED_BRANCHES if branch["region"] == region]


def get_all_regions() -> List[str]:
    """
    Get a list of all unique regions.

    Returns:
        List[str]: List of unique region names.
    """
    return list(set(branch["region"] for branch in FIXED_BRANCHES))
