"""Expande el catálogo de ciudades con ~150 localidades adicionales."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR

CITIES_FILE = DATA_DIR / "cities_mexico_32_states.json"

NEW_CITIES = {
    "Aguascalientes": [
        {"name": "Calvillo", "lat": 21.85, "lon": -102.72, "population": 55000},
        {"name": "Rincón de Romos", "lat": 22.23, "lon": -102.32, "population": 52000},
        {"name": "Pabellón de Arteaga", "lat": 22.15, "lon": -102.27, "population": 42000},
    ],
    "Baja California": [
        {"name": "San Quintín", "lat": 30.53, "lon": -115.93, "population": 25000},
        {"name": "San Felipe", "lat": 31.02, "lon": -114.84, "population": 18000},
    ],
    "Baja California Sur": [
        {"name": "Ciudad Constitución", "lat": 25.04, "lon": -111.67, "population": 45000},
        {"name": "Loreto", "lat": 26.01, "lon": -111.35, "population": 20000},
        {"name": "Santa Rosalía", "lat": 27.34, "lon": -112.27, "population": 15000},
        {"name": "Guerrero Negro", "lat": 27.97, "lon": -114.06, "population": 15000},
    ],
    "Campeche": [
        {"name": "Champotón", "lat": 19.35, "lon": -90.72, "population": 35000},
        {"name": "Escárcega", "lat": 18.61, "lon": -90.74, "population": 30000},
        {"name": "Calkiní", "lat": 20.37, "lon": -90.05, "population": 18000},
    ],
    "Chiapas": [
        {"name": "Palenque", "lat": 17.51, "lon": -91.98, "population": 50000},
        {"name": "Ocosingo", "lat": 16.91, "lon": -92.10, "population": 45000},
        {"name": "Tonalá", "lat": 16.09, "lon": -93.75, "population": 40000},
        {"name": "Villaflores", "lat": 16.23, "lon": -93.27, "population": 35000},
        {"name": "Huixtla", "lat": 15.14, "lon": -92.47, "population": 30000},
    ],
    "Chihuahua": [
        {"name": "Parral", "lat": 26.93, "lon": -105.67, "population": 115000},
        {"name": "Nuevo Casas Grandes", "lat": 30.42, "lon": -107.91, "population": 65000},
        {"name": "Camargo", "lat": 27.68, "lon": -105.17, "population": 50000},
        {"name": "Ojinaga", "lat": 29.57, "lon": -104.42, "population": 28000},
    ],
    "Ciudad de México": [
        {"name": "Xochimilco", "lat": 19.26, "lon": -99.10, "population": 420000},
        {"name": "Tlalpan", "lat": 19.17, "lon": -99.17, "population": 680000},
        {"name": "Iztapalapa", "lat": 19.36, "lon": -99.06, "population": 1800000},
        {"name": "Coyoacán", "lat": 19.35, "lon": -99.16, "population": 620000},
        {"name": "Cuajimalpa", "lat": 19.36, "lon": -99.30, "population": 200000},
    ],
    "Coahuila": [
        {"name": "Acuña", "lat": 29.32, "lon": -100.93, "population": 180000},
        {"name": "Sabinas", "lat": 27.85, "lon": -101.12, "population": 65000},
        {"name": "Múzquiz", "lat": 27.88, "lon": -101.52, "population": 70000},
        {"name": "Parras", "lat": 25.44, "lon": -102.19, "population": 45000},
        {"name": "San Pedro de las Colonias", "lat": 25.76, "lon": -102.98, "population": 55000},
    ],
    "Colima": [
        {"name": "Tecomán", "lat": 18.91, "lon": -103.88, "population": 75000},
        {"name": "Comala", "lat": 19.32, "lon": -103.76, "population": 22000},
    ],
    "Durango": [
        {"name": "Lerdo", "lat": 25.54, "lon": -103.52, "population": 150000},
        {"name": "Santiago Papasquiaro", "lat": 25.04, "lon": -105.42, "population": 45000},
        {"name": "Canatlán", "lat": 24.52, "lon": -104.78, "population": 20000},
    ],
    "Estado de México": [
        {"name": "Metepec", "lat": 19.25, "lon": -99.60, "population": 230000},
        {"name": "Valle de Bravo", "lat": 19.19, "lon": -100.13, "population": 65000},
        {"name": "Jilotepec", "lat": 19.95, "lon": -99.53, "population": 85000},
        {"name": "Ixtlahuaca", "lat": 19.57, "lon": -99.77, "population": 160000},
    ],
    "Guanajuato": [
        {"name": "Salamanca", "lat": 20.57, "lon": -101.20, "population": 260000},
        {"name": "Silao", "lat": 20.95, "lon": -101.43, "population": 180000},
        {"name": "Valle de Santiago", "lat": 20.39, "lon": -101.19, "population": 145000},
        {"name": "Dolores Hidalgo", "lat": 21.16, "lon": -100.93, "population": 155000},
    ],
    "Guerrero": [
        {"name": "Iguala", "lat": 18.34, "lon": -99.54, "population": 150000},
        {"name": "Taxco", "lat": 18.56, "lon": -99.60, "population": 105000},
        {"name": "Zihuatanejo", "lat": 17.64, "lon": -101.55, "population": 125000},
    ],
    "Hidalgo": [
        {"name": "Ixmiquilpan", "lat": 20.49, "lon": -99.22, "population": 90000},
        {"name": "Huejutla", "lat": 21.14, "lon": -98.42, "population": 50000},
        {"name": "Zimapán", "lat": 20.74, "lon": -99.39, "population": 35000},
    ],
    "Jalisco": [
        {"name": "Lagos de Moreno", "lat": 21.35, "lon": -101.93, "population": 165000},
        {"name": "Tepatitlán", "lat": 20.82, "lon": -102.77, "population": 140000},
        {"name": "Autlán", "lat": 19.77, "lon": -104.37, "population": 60000},
    ],
    "Michoacán": [
        {"name": "Lázaro Cárdenas", "lat": 17.96, "lon": -102.20, "population": 180000},
        {"name": "Apatzingán", "lat": 19.09, "lon": -102.35, "population": 130000},
        {"name": "Pátzcuaro", "lat": 19.52, "lon": -101.61, "population": 90000},
        {"name": "Zitácuaro", "lat": 19.44, "lon": -100.36, "population": 160000},
        {"name": "Sahuayo", "lat": 20.06, "lon": -102.72, "population": 75000},
    ],
    "Morelos": [
        {"name": "Jojutla", "lat": 18.62, "lon": -99.18, "population": 58000},
        {"name": "Yautepec", "lat": 18.88, "lon": -99.07, "population": 100000},
    ],
    "Nayarit": [
        {"name": "Compostela", "lat": 21.24, "lon": -104.90, "population": 55000},
        {"name": "Acaponeta", "lat": 22.49, "lon": -105.37, "population": 30000},
        {"name": "Santiago Ixcuintla", "lat": 21.81, "lon": -105.21, "population": 50000},
    ],
    "Nuevo León": [
        {"name": "Linares", "lat": 24.86, "lon": -99.57, "population": 85000},
        {"name": "Montemorelos", "lat": 25.19, "lon": -99.83, "population": 60000},
        {"name": "Sabinas Hidalgo", "lat": 26.51, "lon": -100.18, "population": 36000},
    ],
    "Oaxaca": [
        {"name": "Juchitán", "lat": 16.43, "lon": -95.02, "population": 100000},
        {"name": "Salina Cruz", "lat": 16.17, "lon": -95.20, "population": 90000},
        {"name": "Huatulco", "lat": 15.77, "lon": -96.13, "population": 50000},
        {"name": "Tuxtepec", "lat": 18.09, "lon": -96.12, "population": 100000},
        {"name": "Pinotepa Nacional", "lat": 16.34, "lon": -98.05, "population": 55000},
    ],
    "Puebla": [
        {"name": "Teziutlán", "lat": 19.82, "lon": -97.36, "population": 95000},
        {"name": "Huauchinango", "lat": 20.18, "lon": -98.05, "population": 55000},
        {"name": "Izúcar de Matamoros", "lat": 18.60, "lon": -98.47, "population": 75000},
    ],
    "Querétaro": [
        {"name": "Tequisquiapan", "lat": 20.52, "lon": -99.89, "population": 68000},
        {"name": "Cadereyta", "lat": 20.70, "lon": -99.82, "population": 70000},
        {"name": "Jalpan", "lat": 21.22, "lon": -99.47, "population": 25000},
    ],
    "Quintana Roo": [
        {"name": "Bacalar", "lat": 18.68, "lon": -88.39, "population": 15000},
        {"name": "Felipe Carrillo Puerto", "lat": 19.58, "lon": -88.05, "population": 30000},
    ],
    "San Luis Potosí": [
        {"name": "Rioverde", "lat": 21.93, "lon": -99.99, "population": 95000},
        {"name": "Tamazunchale", "lat": 21.26, "lon": -98.79, "population": 50000},
    ],
    "Sinaloa": [
        {"name": "Los Mochis", "lat": 25.79, "lon": -108.99, "population": 420000},
        {"name": "Navolato", "lat": 24.77, "lon": -107.70, "population": 135000},
        {"name": "Escuinapa", "lat": 22.85, "lon": -105.79, "population": 55000},
    ],
    "Sonora": [
        {"name": "Nogales", "lat": 31.31, "lon": -110.94, "population": 260000},
        {"name": "San Luis Río Colorado", "lat": 32.46, "lon": -114.77, "population": 195000},
        {"name": "Caborca", "lat": 30.72, "lon": -112.16, "population": 90000},
        {"name": "Agua Prieta", "lat": 31.33, "lon": -109.55, "population": 85000},
        {"name": "Empalme", "lat": 27.96, "lon": -110.81, "population": 55000},
    ],
    "Tabasco": [
        {"name": "Tenosique", "lat": 17.47, "lon": -91.42, "population": 60000},
        {"name": "Huimanguillo", "lat": 17.83, "lon": -93.39, "population": 55000},
        {"name": "Macuspana", "lat": 17.77, "lon": -92.59, "population": 65000},
        {"name": "Paraíso", "lat": 18.39, "lon": -93.21, "population": 90000},
    ],
    "Tamaulipas": [
        {"name": "Río Bravo", "lat": 25.99, "lon": -98.09, "population": 120000},
        {"name": "Mante", "lat": 22.74, "lon": -98.97, "population": 85000},
        {"name": "San Fernando", "lat": 24.85, "lon": -98.16, "population": 58000},
        {"name": "Valle Hermoso", "lat": 25.67, "lon": -97.81, "population": 62000},
    ],
    "Tlaxcala": [
        {"name": "Huamantla", "lat": 19.32, "lon": -97.92, "population": 95000},
        {"name": "Calpulalpan", "lat": 19.59, "lon": -98.56, "population": 50000},
        {"name": "Chiautempan", "lat": 19.32, "lon": -98.19, "population": 75000},
        {"name": "Zacatelco", "lat": 19.22, "lon": -98.24, "population": 42000},
    ],
    "Veracruz": [
        {"name": "Tuxpan", "lat": 20.96, "lon": -97.40, "population": 145000},
        {"name": "Pánuco", "lat": 22.06, "lon": -98.18, "population": 50000},
        {"name": "San Andrés Tuxtla", "lat": 18.45, "lon": -95.21, "population": 75000},
        {"name": "Tierra Blanca", "lat": 18.45, "lon": -96.35, "population": 45000},
        {"name": "Acayucan", "lat": 17.95, "lon": -94.91, "population": 50000},
        {"name": "Papantla", "lat": 20.45, "lon": -97.32, "population": 55000},
    ],
    "Yucatán": [
        {"name": "Tizimín", "lat": 21.14, "lon": -88.15, "population": 80000},
        {"name": "Tekax", "lat": 20.20, "lon": -89.29, "population": 42000},
        {"name": "Ticul", "lat": 20.40, "lon": -89.54, "population": 40000},
        {"name": "Motul", "lat": 21.10, "lon": -89.28, "population": 38000},
        {"name": "Izamal", "lat": 20.93, "lon": -89.02, "population": 26000},
    ],
    "Zacatecas": [
        {"name": "Jerez", "lat": 22.65, "lon": -103.00, "population": 60000},
        {"name": "Río Grande", "lat": 23.81, "lon": -103.03, "population": 55000},
        {"name": "Sombrerete", "lat": 23.63, "lon": -103.64, "population": 30000},
        {"name": "Jalpa", "lat": 21.63, "lon": -102.97, "population": 25000},
        {"name": "Nochistlán", "lat": 21.36, "lon": -102.85, "population": 20000},
    ],
}


def main():
    with open(CITIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing = set()
    state_idx = {}
    for i, s in enumerate(data["states"]):
        state_idx[s["name"]] = i
        for c in s["cities"]:
            existing.add(f"{c['name']}|{s['name']}")

    added = 0
    for state_name, cities in NEW_CITIES.items():
        idx = state_idx.get(state_name)
        if idx is None:
            print(f"WARNING: {state_name} not found")
            continue
        for city in cities:
            key = f"{city['name']}|{state_name}"
            if key not in existing:
                city["is_capital"] = False
                data["states"][idx]["cities"].append(city)
                existing.add(key)
                added += 1

    with open(CITIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total = sum(len(s["cities"]) for s in data["states"])
    print(f"Agregadas {added} ciudades nuevas")
    print(f"Total: {total} ciudades en 32 estados")


if __name__ == "__main__":
    main()
