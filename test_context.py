#!/usr/bin/env python3

from natural_language_processor_backup import IaLNaturalProcessor

def test_context_enrichment():
    processor = IaLNaturalProcessor()
    
    # Testar listagem
    result1 = processor._enrich_context_if_needed("liste as fases do ial")
    print("LISTAGEM:", "GitHub" in result1)
    
    # Testar criação  
    result2 = processor._enrich_context_if_needed("criar uma fase 15-backup")
    print("CRIAÇÃO:", "GitHub" in result2)

if __name__ == "__main__":
    test_context_enrichment()
