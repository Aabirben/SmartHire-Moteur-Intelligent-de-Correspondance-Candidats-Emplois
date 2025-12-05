# Corrected test_config.py
# Added sys.path to parent.parent to access 'recherche_booleenne' from root.
import sys
from pathlib import Path

# Add project root to PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*80)
print("🔍 TEST CONFIGURATION")
print("="*80)

# Test 1: Import config
print("\n1. Test import recherche_booleenne...")
try:
    from recherche_booleenne.config import (
        CV_INDEX_PATH,
        JOB_INDEX_PATH,
        CV_MAPPING,
        JOB_MAPPING,
        MAPPING_FILE
    )
    print("✅ Import réussi")
except Exception as e:
    print(f"❌ Erreur import: {e}")
    sys.exit(1)

# Test 2: Chemins
print("\n2. Vérification des chemins...")
print(f"   📂 Index CV: {CV_INDEX_PATH}")
print(f"   📂 Index Jobs: {JOB_INDEX_PATH}")
print(f"   📄 Mapping: {MAPPING_FILE}")

import os
if os.path.exists(CV_INDEX_PATH):
    print("   ✅ Index CV existe")
else:
    print("   ❌ Index CV MANQUANT")

if os.path.exists(JOB_INDEX_PATH):
    print("   ✅ Index Jobs existe")
else:
    print("   ❌ Index Jobs MANQUANT")

# Test 3: Mapping
print("\n3. Vérification mapping...")
print(f"   📊 {len(CV_MAPPING)} CVs mappés")
print(f"   📊 {len(JOB_MAPPING)} offres mappées")

if len(CV_MAPPING) > 0:
    print("   ✅ Mapping CV OK")
    # Affiche un exemple
    first_cv = list(CV_MAPPING.items())[0]
    print(f"   Exemple: {first_cv[0]} → ID {first_cv[1]}")
else:
    print("   ❌ Mapping CV vide")

if len(JOB_MAPPING) > 0:
    print("   ✅ Mapping Jobs OK")
    first_job = list(JOB_MAPPING.items())[0]
    print(f"   Exemple: {first_job[0]} → ID {first_job[1]}")
else:
    print("   ❌ Mapping Jobs vide")

# Test 4: Validation complète
print("\n4. Validation complète...")
from recherche_booleenne.config import verify_setup

if verify_setup():
    print("\n✅ CONFIGURATION OK - PRÊT POUR LES TESTS")
else:
    print("\n❌ CONFIGURATION INVALIDE")
    sys.exit(1)

print("="*80)