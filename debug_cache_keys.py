#!/usr/bin/env python3
"""
Debug script to compare cache keys and identify why duplicates exist.

Run this script to analyze the cache database and find duplicate entries.
"""

import sqlite3
import json
import hashlib
from datetime import datetime

def analyze_cache_duplicates(db_path="omada_cache.db"):
    """Analyze cache for potential duplicate entries."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all cache entries
    cursor.execute("""
        SELECT cache_key, endpoint, query_params, created_at, hit_count
        FROM api_cache
        ORDER BY created_at DESC
    """)

    entries = cursor.fetchall()
    conn.close()

    print(f"\n{'='*80}")
    print(f"CACHE DUPLICATE ANALYSIS")
    print(f"{'='*80}\n")
    print(f"Total cache entries: {len(entries)}\n")

    # Group by parameters to find duplicates
    params_to_entries = {}

    for cache_key, endpoint, query_params, created_at, hit_count in entries:
        # Parse params
        try:
            params_dict = json.loads(query_params)

            # Create a normalized key (sorted JSON for comparison)
            normalized = json.dumps(params_dict, sort_keys=True)

            if normalized not in params_to_entries:
                params_to_entries[normalized] = []

            params_to_entries[normalized].append({
                'cache_key': cache_key,
                'endpoint': endpoint,
                'created_at': created_at,
                'hit_count': hit_count,
                'params': params_dict
            })
        except Exception as e:
            print(f"Error parsing params: {e}")
            continue

    # Find duplicates (same params, different cache keys)
    duplicates_found = False

    for normalized_params, entry_list in params_to_entries.items():
        if len(entry_list) > 1:
            duplicates_found = True
            print(f"\n{'='*80}")
            print(f"🔴 DUPLICATE FOUND: {len(entry_list)} entries with identical parameters")
            print(f"{'='*80}\n")

            for i, entry in enumerate(entry_list, 1):
                print(f"Entry {i}:")
                print(f"  Cache Key: {entry['cache_key']}")
                print(f"  Created: {entry['created_at']}")
                print(f"  Hit Count: {entry['hit_count']}")
                print(f"  Endpoint: {entry['endpoint']}")

                # Show if query string differs
                if 'query' in entry['params']:
                    query = entry['params']['query']
                    # Show first 100 chars and hash
                    query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
                    print(f"  Query (first 100 chars): {query[:100]}...")
                    print(f"  Query hash: {query_hash}")

                print(f"  User Identity: {entry['params'].get('user_identity', 'N/A')}")
                print(f"  Impersonate User: {entry['params'].get('impersonate_user', 'N/A')}")
                print(f"  Version: {entry['params'].get('version', 'N/A')}")
                print()

            # Compare the cache keys they SHOULD have
            print("Cache Key Analysis:")
            for i, entry in enumerate(entry_list, 1):
                # Regenerate what the cache key SHOULD be
                param_str = json.dumps(entry['params'], sort_keys=True)
                key_input = f"{entry['endpoint']}:{param_str}"
                expected_key = hashlib.sha256(key_input.encode()).hexdigest()

                matches = "✅ MATCH" if expected_key == entry['cache_key'] else "❌ MISMATCH"
                print(f"  Entry {i}: {matches}")
                print(f"    Actual:   {entry['cache_key'][:32]}...")
                print(f"    Expected: {expected_key[:32]}...")

                if expected_key != entry['cache_key']:
                    print(f"    ⚠️  Cache key doesn't match expected value!")
                print()

    if not duplicates_found:
        print("✅ No duplicates found - all cache entries have unique parameters\n")

    print(f"{'='*80}\n")

if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "omada_cache.db"
    analyze_cache_duplicates(db_path)
