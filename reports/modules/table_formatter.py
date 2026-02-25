"""
Table Formatter Module

Creates formatted tables in various formats (pandas DataFrame, dict, markdown, Excel).
"""

import pandas as pd
from typing import List, Dict, Optional


class TableFormatter:
    """
    Formats growth analysis results as tables in various output formats.

    Supports:
    - pandas DataFrame
    - Dictionary
    - Markdown
    - Excel (via pandas)
    """

    @staticmethod
    def format_number(value: float, decimals: int = 2) -> str:
        """
        Format number with thousands separator.

        Args:
            value: Number to format
            decimals: Number of decimal places

        Returns:
            Formatted string
        """
        return f"{value:,.{decimals}f}"

    @staticmethod
    def to_dataframe(growth_data: List[Dict]) -> pd.DataFrame:
        """
        Convert growth data to pandas DataFrame.

        Args:
            growth_data: List of growth calculation results

        Returns:
            pandas DataFrame
        """
        df = pd.DataFrame(growth_data)

        # Rename columns for better readability
        column_map = {
            'afore': 'Afore',
            'start_value': 'Start Value',
            'end_value': 'End Value',
            'growth_absolute': 'Growth ($)',
            'growth_percent': 'Growth (%)',
            'currency': 'Currency'
        }

        df = df.rename(columns=column_map)

        return df

    @staticmethod
    def to_dict(growth_data: List[Dict]) -> Dict:
        """
        Convert growth data to structured dictionary.

        Args:
            growth_data: List of growth calculation results

        Returns:
            Dictionary with data and metadata
        """
        return {
            'data': growth_data,
            'total': growth_data[-1] if growth_data else None,
            'afores': growth_data[:-1] if growth_data else []
        }

    @staticmethod
    def to_markdown(
        growth_data: List[Dict],
        title: str = "Growth Analysis",
        show_start: bool = True
    ) -> str:
        """
        Convert growth data to markdown table.

        Args:
            growth_data: List of growth calculation results
            title: Table title
            show_start: Whether to include start value column

        Returns:
            Markdown formatted table string
        """
        if not growth_data:
            return f"## {title}\n\nNo data available."

        currency = growth_data[0].get('currency', 'USD')
        prefix = "$" if currency == "USD" else ""

        lines = [f"## {title}", ""]

        # Headers
        if show_start:
            headers = ["Afore", "Start Value", "End Value", "Growth ($)", "Growth (%)"]
            alignment = [":---", "---:", "---:", "---:", "---:"]
        else:
            headers = ["Afore", "End Value", "Growth ($)", "Growth (%)"]
            alignment = [":---", "---:", "---:", "---:"]

        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(alignment) + " |")

        # Data rows
        for i, row in enumerate(growth_data):
            afore = row['afore']
            end_val = TableFormatter.format_number(row['end_value'])
            growth_abs = TableFormatter.format_number(row['growth_absolute'])
            growth_pct = TableFormatter.format_number(row['growth_percent'], 1)

            # Bold for total row
            if i == len(growth_data) - 1:
                afore = f"**{afore}**"
                end_val = f"**{prefix}{end_val}**"
                growth_abs = f"**{prefix}{growth_abs}**"
                growth_pct = f"**{growth_pct}%**"
            else:
                end_val = f"{prefix}{end_val}"
                growth_abs = f"{prefix}{growth_abs}"
                growth_pct = f"{growth_pct}%"

            if show_start:
                start_val = TableFormatter.format_number(row['start_value'])
                if i == len(growth_data) - 1:
                    start_val = f"**{prefix}{start_val}**"
                else:
                    start_val = f"{prefix}{start_val}"

                lines.append(f"| {afore} | {start_val} | {end_val} | {growth_abs} | {growth_pct} |")
            else:
                lines.append(f"| {afore} | {end_val} | {growth_abs} | {growth_pct} |")

        return "\n".join(lines)

    @staticmethod
    def create_comparison_table(
        ytd_data: List[Dict],
        one_year_data: List[Dict],
        three_year_data: Optional[List[Dict]] = None,
        five_year_data: Optional[List[Dict]] = None,
        title: str = "Multi-Period Growth Comparison"
    ) -> pd.DataFrame:
        """
        Create a comparison table showing multiple time periods side by side.

        Args:
            ytd_data: YTD growth data
            one_year_data: 1-year growth data
            three_year_data: 3-year growth data (optional)
            five_year_data: 5-year growth data (optional)
            title: Table title

        Returns:
            pandas DataFrame with multi-period comparison
        """
        # Extract afore names (excluding total)
        afores = [d['afore'] for d in ytd_data[:-1]]

        # Build comparison data
        comparison = []

        for i, afore in enumerate(afores):
            row = {'Afore': afore}

            # YTD
            row['YTD Value'] = ytd_data[i]['end_value']
            row['YTD Growth $'] = ytd_data[i]['growth_absolute']
            row['YTD Growth %'] = ytd_data[i]['growth_percent']

            # 1Y
            row['1Y Growth $'] = one_year_data[i]['growth_absolute']
            row['1Y Growth %'] = one_year_data[i]['growth_percent']

            # 3Y (if provided)
            if three_year_data:
                row['3Y Growth $'] = three_year_data[i]['growth_absolute']
                row['3Y Growth %'] = three_year_data[i]['growth_percent']

            # 5Y (if provided)
            if five_year_data:
                row['5Y Growth $'] = five_year_data[i]['growth_absolute']
                row['5Y Growth %'] = five_year_data[i]['growth_percent']

            comparison.append(row)

        # Add total row
        total_row = {'Afore': 'MARKET TOTAL'}
        total_row['YTD Value'] = ytd_data[-1]['end_value']
        total_row['YTD Growth $'] = ytd_data[-1]['growth_absolute']
        total_row['YTD Growth %'] = ytd_data[-1]['growth_percent']
        total_row['1Y Growth $'] = one_year_data[-1]['growth_absolute']
        total_row['1Y Growth %'] = one_year_data[-1]['growth_percent']

        if three_year_data:
            total_row['3Y Growth $'] = three_year_data[-1]['growth_absolute']
            total_row['3Y Growth %'] = three_year_data[-1]['growth_percent']

        if five_year_data:
            total_row['5Y Growth $'] = five_year_data[-1]['growth_absolute']
            total_row['5Y Growth %'] = five_year_data[-1]['growth_percent']

        comparison.append(total_row)

        return pd.DataFrame(comparison)

    @staticmethod
    def to_excel(
        dataframes: Dict[str, pd.DataFrame],
        output_path: str,
        format_numbers: bool = True
    ):
        """
        Export multiple DataFrames to Excel with formatting.

        Args:
            dataframes: Dict mapping sheet names to DataFrames
            output_path: Output Excel file path
            format_numbers: Whether to apply number formatting
        """
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                if format_numbers:
                    worksheet = writer.sheets[sheet_name]

                    # Format number columns
                    for col_idx, col in enumerate(df.columns, 1):
                        if 'Growth %' in col or '%' in col:
                            for row_idx in range(2, len(df) + 2):
                                cell = worksheet.cell(row=row_idx, column=col_idx)
                                if cell.value is not None:
                                    cell.number_format = '0.00%'
                                    cell.value = cell.value / 100

                        elif 'Value' in col or 'Growth $' in col or '$' in col:
                            for row_idx in range(2, len(df) + 2):
                                cell = worksheet.cell(row=row_idx, column=col_idx)
                                if cell.value is not None:
                                    cell.number_format = '#,##0.00'

    @staticmethod
    def create_summary_table(all_metrics: Dict) -> pd.DataFrame:
        """
        Create a high-level summary table from all metrics.

        Args:
            all_metrics: Dict from AUMCalculator.get_all_growth_metrics()

        Returns:
            Summary DataFrame
        """
        summary = []

        periods = ['ytd', '1_year', '3_year', '5_year']
        period_labels = ['YTD', '1 Year', '3 Year', '5 Year']

        for period, label in zip(periods, period_labels):
            if period in all_metrics:
                for currency in ['USD', 'MXN']:
                    if currency in all_metrics[period]:
                        # Get market total (last item)
                        market_data = all_metrics[period][currency][-1]

                        summary.append({
                            'Period': label,
                            'Currency': currency,
                            'End Value': market_data['end_value'],
                            'Growth ($)': market_data['growth_absolute'],
                            'Growth (%)': market_data['growth_percent']
                        })

        return pd.DataFrame(summary)
