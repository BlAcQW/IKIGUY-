#!/usr/bin/env python3
"""Simple data loader for Ghana Tourism PostgreSQL RAG."""
import asyncio
import json
import os
import asyncpg
import openai

# Config
DB_URL = f"postgresql://postgres:aawwER444444@localhost:5432/kasaai_core"
openai.api_key = os.getenv("OPENAI_API_KEY", "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")

async def embed(text):
    """Generate embedding in pgvector format."""
    try:
        resp = openai.embeddings.create(model="text-embedding-3-small", input=text[:8000])
        # Convert to pgvector string format
        vec = resp.data[0].embedding
        return f"[{','.join(map(str, vec))}]"
    except:
        return f"[{','.join(['0.0'] * 1536)}]"

async def main():
    conn = await asyncpg.connect(DB_URL)
    data_dir = os.path.join(os.path.dirname(__file__), 'data')

    print("Loading destinations...")
    with open(f"{data_dir}/destinations.json") as f:
        dests = json.load(f)['destinations']

    for d in dests:
        text = f"{d['name']} in {d['region']}. {d['description']} Activities: {', '.join(d['activities'])}"
        emb = await embed(text)
        await conn.execute("""
            INSERT INTO tourism_destinations (id, name, region, category, description, highlights,
            best_time_to_visit, entry_fee, activities, difficulty, duration_hours, district, coordinates,
            distance_from_accra_km, contact, facilities, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            ON CONFLICT (id) DO UPDATE SET name = $2, embedding = $17
        """, d['id'], d['name'], d['region'], d['category'], d['description'], d['highlights'],
        d.get('best_time_to_visit'), d.get('entry_fee'), d['activities'], d.get('difficulty'),
        d.get('duration_hours'), d['location'].get('district'), json.dumps(d['location'].get('coordinates')),
        d['location'].get('distance_from_accra_km'), json.dumps(d.get('contact')), d.get('facilities', []), emb)
        print(f"✓ {d['name']}")

    print(f"\nLoading accommodations...")
    with open(f"{data_dir}/accommodations.json") as f:
        accs = json.load(f)['accommodations']

    for a in accs:
        text = f"{a['name']}, {a['star_rating']}-star {a['type']} in {a['city']}. {a['description']}"
        emb = await embed(text)
        await conn.execute("""
            INSERT INTO tourism_accommodations (id, name, region, city, type, star_rating, description,
            amenities, room_types, location, contact, booking_platforms, special_notes, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            ON CONFLICT (id) DO UPDATE SET name = $2, embedding = $14
        """, a['id'], a['name'], a['region'], a['city'], a['type'], a.get('star_rating'),
        a['description'], a['amenities'], json.dumps(a['room_types']), json.dumps(a['location']),
        json.dumps(a['contact']), a['booking_platforms'], a.get('special_notes'), emb)
        print(f"✓ {a['name']}")

    print(f"\nLoading practical info...")
    with open(f"{data_dir}/practical_info.json") as f:
        pinfo = json.load(f)

    categories = [
        ('visa', 'visa_requirements', 'Visa Requirements'),
        ('mobile_sim', 'mobile_sim_cards', 'Mobile SIM Cards'),
        ('currency', 'currency_exchange', 'Currency Exchange'),
        ('safety', 'safety_security', 'Safety & Security'),
        ('weather', 'weather_climate', 'Weather & Climate'),
        ('culture', 'cultural_etiquette', 'Cultural Etiquette')
    ]

    for cat_id, key, title in categories:
        if key not in pinfo:
            continue
        content = pinfo[key]
        text = json.dumps(content)[:4000]
        emb = await embed(text)
        await conn.execute("""
            INSERT INTO tourism_practical_info (id, category, title, content, keywords, embedding)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE SET content = $4, embedding = $6
        """, f"{cat_id}_001", cat_id, title, json.dumps(content), [cat_id, key], emb)
        print(f"✓ {title}")

    await conn.close()
    print("\n✅ All data loaded with embeddings!")

if __name__ == "__main__":
    asyncio.run(main())
