"""
AUM Calculator Module

Calculates AUM growth metrics for different time periods and currencies.
"""

from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime
from .data_loader import AforeDataLoader


class AUMCalculator:
    """
    Calculates AUM (Assets Under Management) growth metrics.

    Supports:
    - Multiple time periods (1Y, 3Y, 5Y, YTD, calendar year)
    - Both USD and MXN currencies
    - Absolute and percentage growth
    - Market-wide and individual Afore analysis
    """

    def __init__(self, data_loader: AforeDataLoader):
        """
        Initialize calculator with a data loader.

        Args:
            data_loader: AforeDataLoader instance with loaded data
        """
        self.loader = data_loader

    def aggregate_by_afore(
        self,
        year: str,
        month: str,
        concept_key: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Aggregate AUM values by Afore for a specific period and concept.

        Args:
            year: Year string (e.g., "2025")
            month: Month string (e.g., "10")
            concept_key: Concept key ('total_assets', 'mandates', 'mutual_funds', 'fiduciary')

        Returns:
            Dict mapping Afore name to {'MXN': value, 'USD': value, 'FX': rate}
        """
        result = defaultdict(lambda: {'MXN': 0, 'USD': 0, 'FX': 0})

        records = self.loader.get_records(
            year=year,
            month=month,
            concept_key=concept_key
        )

        for record in records:
            afore = record['Afore']

            # Merge Citibanamex into Banamex (they are the same entity, renamed in 2024)
            if afore == 'Citibanamex':
                afore = 'Banamex'

            result[afore]['MXN'] += record['valueMXN']
            result[afore]['USD'] += record['valueUSD']
            result[afore]['FX'] = record['FX_EOM']

        return dict(result)

    def aggregate_active_management(
        self,
        year: str,
        month: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Aggregate combined "Total Active Management" (Mandatos + Mutual Funds).

        Total Active Management = External/outsourced management
        - Mandatos (Inversiones Tercerizadas / Third Party Mandates)
        - Fondos Mutuos (Mutual Funds)

        Note: Does NOT include Fiduciary Securities (Títulos Fiduciarios)

        Args:
            year: Year string
            month: Month string

        Returns:
            Dict mapping Afore name to combined values
        """
        mandatos = self.aggregate_by_afore(year, month, 'mandatos')
        mutual = self.aggregate_by_afore(year, month, 'mutual_funds')

        result = defaultdict(lambda: {'MXN': 0, 'USD': 0, 'FX': 0})

        all_afores = set(list(mandatos.keys()) + list(mutual.keys()))

        for afore in all_afores:
            result[afore]['MXN'] = (
                mandatos.get(afore, {}).get('MXN', 0) +
                mutual.get(afore, {}).get('MXN', 0)
            )
            result[afore]['USD'] = (
                mandatos.get(afore, {}).get('USD', 0) +
                mutual.get(afore, {}).get('USD', 0)
            )
            # Use most recent FX rate available
            result[afore]['FX'] = (
                mutual.get(afore, {}).get('FX', 0) or
                mandatos.get(afore, {}).get('FX', 0)
            )

        return dict(result)

    def calculate_growth(
        self,
        start_data: Dict[str, Dict[str, float]],
        end_data: Dict[str, Dict[str, float]],
        currency: str = 'USD',
        as_millions: bool = True
    ) -> List[Dict]:
        """
        Calculate growth between two periods for all Afores.

        Args:
            start_data: Starting period data from aggregate_by_afore()
            end_data: Ending period data from aggregate_by_afore()
            currency: 'USD' or 'MXN'
            as_millions: If True, convert to millions

        Returns:
            List of dicts with growth calculations for each Afore plus market total

        Note: Citibanamex is automatically merged into Banamex at the aggregation level
        """
        all_afores = sorted(set(list(start_data.keys()) + list(end_data.keys())))

        results = []
        total_start = 0
        total_end = 0

        # Divisor for converting to millions
        # DB stores miles de pesos (MXN/1000) and thousands of USD
        divisor = 1_000 if currency == 'USD' else 1_000

        for afore in all_afores:
            if currency == 'MXN':
                start_val = start_data.get(afore, {}).get('MXN', 0)
                end_val = end_data.get(afore, {}).get('MXN', 0)
            else:
                start_val = start_data.get(afore, {}).get('USD', 0)
                end_val = end_data.get(afore, {}).get('USD', 0)

            if as_millions:
                start_val = start_val / divisor
                end_val = end_val / divisor

            growth_abs = end_val - start_val
            growth_pct = (growth_abs / start_val * 100) if start_val > 0 else 0

            total_start += start_val
            total_end += end_val

            results.append({
                'afore': afore,
                'start_value': start_val,
                'end_value': end_val,
                'growth_absolute': growth_abs,
                'growth_percent': growth_pct,
                'currency': currency
            })

        # Add market total
        total_growth_abs = total_end - total_start
        total_growth_pct = (total_growth_abs / total_start * 100) if total_start > 0 else 0

        results.append({
            'afore': 'MARKET TOTAL',
            'start_value': total_start,
            'end_value': total_end,
            'growth_absolute': total_growth_abs,
            'growth_percent': total_growth_pct,
            'currency': currency
        })

        return results

    def calculate_period_offset(self, year: str, month: str, months_back: int) -> tuple:
        """
        Calculate year and month for a period N months before the given date.

        Args:
            year: Starting year
            month: Starting month
            months_back: Number of months to go back

        Returns:
            Tuple of (year_str, month_str)
        """
        date = datetime(int(year), int(month), 1)

        # Calculate target month
        total_months = date.year * 12 + date.month - 1 - months_back
        target_year = total_months // 12
        target_month = (total_months % 12) + 1

        return str(target_year), f"{target_month:02d}"

    def get_calendar_year_start(self, year: str) -> tuple:
        """
        Get January of the specified year.

        Args:
            year: Year string

        Returns:
            Tuple of (year, "01")
        """
        return year, "01"

    def get_ytd_growth(
        self,
        current_year: str,
        current_month: str,
        concept_key: str,
        currency: str = 'USD'
    ) -> List[Dict]:
        """
        Calculate year-to-date growth (from January to current month).

        Args:
            current_year: Current year
            current_month: Current month
            concept_key: Concept to analyze
            currency: 'USD' or 'MXN'

        Returns:
            List of growth results
        """
        start_data = self.aggregate_by_afore(current_year, "01", concept_key)
        end_data = self.aggregate_by_afore(current_year, current_month, concept_key)

        return self.calculate_growth(start_data, end_data, currency)

    def get_multi_year_growth(
        self,
        end_year: str,
        end_month: str,
        concept_key: str,
        years: int,
        currency: str = 'USD'
    ) -> List[Dict]:
        """
        Calculate N-year growth (1Y, 3Y, 5Y).

        Args:
            end_year: Ending year
            end_month: Ending month
            concept_key: Concept to analyze
            years: Number of years (1, 3, or 5)
            currency: 'USD' or 'MXN'

        Returns:
            List of growth results
        """
        start_year, start_month = self.calculate_period_offset(
            end_year, end_month, years * 12
        )

        start_data = self.aggregate_by_afore(start_year, start_month, concept_key)
        end_data = self.aggregate_by_afore(end_year, end_month, concept_key)

        return self.calculate_growth(start_data, end_data, currency)

    def get_all_growth_metrics(
        self,
        year: str,
        month: str,
        concept_key: str,
        include_active_management: bool = False
    ) -> Dict:
        """
        Get comprehensive growth metrics for all periods and currencies.

        Args:
            year: Analysis year
            month: Analysis month
            concept_key: Concept to analyze ('total_assets', 'mandatos', etc.)
            include_active_management: If True, use active management instead of concept_key

        Returns:
            Dict with all growth metrics organized by period and currency
        """
        results = {
            'period': f"{year}-{month}",
            'concept': 'active_management' if include_active_management else concept_key,
            'ytd': {},
            '1_month': {},
            '3_month': {},
            '1_year': {},
            '3_year': {},
            '5_year': {}
        }

        # Determine which aggregation method to use
        if include_active_management:
            end_data_func = lambda y, m: self.aggregate_active_management(y, m)
        else:
            end_data_func = lambda y, m: self.aggregate_by_afore(y, m, concept_key)

        for currency in ['USD', 'MXN']:
            # YTD
            start_data = end_data_func(year, "01")
            end_data = end_data_func(year, month)
            results['ytd'][currency] = self.calculate_growth(start_data, end_data, currency)

            # 1-month (MoM)
            start_year_mom, start_month_mom = self.calculate_period_offset(year, month, 1)
            start_data_mom = end_data_func(start_year_mom, start_month_mom)
            results['1_month'][currency] = self.calculate_growth(start_data_mom, end_data, currency)

            # 3-month
            start_year_3m, start_month_3m = self.calculate_period_offset(year, month, 3)
            start_data_3m = end_data_func(start_year_3m, start_month_3m)
            results['3_month'][currency] = self.calculate_growth(start_data_3m, end_data, currency)

            # 1-year
            start_year, start_month = self.calculate_period_offset(year, month, 12)
            start_data = end_data_func(start_year, start_month)
            results['1_year'][currency] = self.calculate_growth(start_data, end_data, currency)

            # 3-year
            start_year, start_month = self.calculate_period_offset(year, month, 36)
            start_data = end_data_func(start_year, start_month)
            results['3_year'][currency] = self.calculate_growth(start_data, end_data, currency)

            # 5-year
            start_year, start_month = self.calculate_period_offset(year, month, 60)
            start_data = end_data_func(start_year, start_month)
            results['5_year'][currency] = self.calculate_growth(start_data, end_data, currency)

        return results
