import json
from pathlib import Path

cities_file = Path(__file__).parent / 'data' / 'cities_mexico_32_states.json'
with open(cities_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

total_ciudades = sum(len(e['ciudades']) for e in data['estados'])
print(f"Total ciudades: {total_ciudades}")
print(f"Total estados: {len(data['estados'])}")
print(f"Esperado: {total_ciudades * 50} propiedades")

