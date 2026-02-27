"""
Data Loader Module

Handles loading and filtering of Afore AUM data from JSON database.
"""

import json
from typing import List, Dict, Optional
from pathlib import Path


class AforeDataLoader:
    """
    Loads and filters Afore AUM data from CONSAR database.

    Attributes:
        data_path: Path to the JSON database file
        data: Loaded data records
    """

    # Concept mappings to handle variations in data
    CONCEPT_MAPPINGS = {
        'total_assets': ['Total de Activo'],
        'mandatos': ['Inversiones Tercerizadas'],
        'mutual_funds': [
            'Inversion en Fondos Mutuos',
            'Inversión en Fondos Mutuos'
        ],
        'fiduciary': [
            'Inversion en Titulos Fiduciarios',
            'Inversión en títulos Fiduciarios'
        ]
    }

    def __init__(self, data_path: str = "consar_siefores_with_usd.json"):
        """
        Initialize the data loader.

        Args:
            data_path: Path to the JSON database file
        """
        self.data_path = Path(data_path)
        self.data: List[Dict] = []

    def load(self) -> 'AforeDataLoader':
        """
        Load data from JSON file.

        Returns:
            Self for method chaining
        """
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        return self

    def get_records(
        self,
        year: Optional[str] = None,
        month: Optional[str] = None,
        afore: Optional[str] = None,
        concept_key: Optional[str] = None,
        concept: Optional[str] = None
    ) -> List[Dict]:
        """
        Filter records by specified criteria.

        Args:
            year: Filter by year (e.g., "2025")
            month: Filter by month (e.g., "10" for October)
            afore: Filter by Afore name
            concept_key: Filter by concept key (e.g., 'total_assets', 'mandates')
            concept: Filter by exact concept name

        Returns:
            List of matching records
        """
        results = self.data

        if year:
            results = [r for r in results if r['PeriodYear'] == year]

        if month:
            results = [r for r in results if r['PeriodMonth'] == month]

        if afore:
            results = [r for r in results if r['Afore'] == afore]

        if concept_key:
            concepts = self.CONCEPT_MAPPINGS.get(concept_key, [])
            results = [r for r in results if r['Concept'] in concepts]

        if concept:
            results = [r for r in results if r['Concept'] == concept]

        return results

    def get_afores(self) -> List[str]:
        """
        Get list of all unique Afores in the database.

        Returns:
            Sorted list of Afore names (excludes Citibanamex as it's merged into Banamex)
        """
        afores = set(r['Afore'] for r in self.data)
        # Exclude Citibanamex since it's merged into Banamex
        afores.discard('Citibanamex')
        return sorted(afores)

    def get_concepts(self) -> List[str]:
        """
        Get list of all unique concepts in the database.

        Returns:
            Sorted list of concept names
        """
        return sorted(set(r['Concept'] for r in self.data))

    def get_available_periods(self) -> List[tuple]:
        """
        Get list of all available year-month combinations.

        Returns:
            Sorted list of (year, month) tuples
        """
        periods = set((r['PeriodYear'], r['PeriodMonth']) for r in self.data)
        return sorted(periods)

    def get_latest_period(self) -> tuple:
        """
        Get the most recent period available in the data.

        Returns:
            Tuple of (year, month)
        """
        periods = self.get_available_periods()
        return periods[-1] if periods else (None, None)
