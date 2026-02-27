"""
Chart Generator Module

Creates bar charts and visualizations for AUM growth analysis.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from typing import List, Dict, Optional
import numpy as np


class ChartGenerator:
    """
    Generates bar charts and visualizations for AUM analysis.

    Supports:
    - Growth comparison charts
    - Multi-period comparison
    - Market overview charts
    - Individual Afore analysis
    """

    @staticmethod
    def set_chart_style():
        """Set consistent chart styling."""
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12

    @staticmethod
    def create_growth_bar_chart(
        growth_data: List[Dict],
        title: str = "AUM Growth Analysis",
        show_percentage: bool = False,
        output_path: Optional[str] = None,
        figsize: tuple = (14, 8)
    ) -> plt.Figure:
        """
        Create a bar chart showing growth for all Afores.
        Displays both absolute amount (Millions) and Percentage.
        """
        # Exclude market total for individual Afore chart
        afore_data = growth_data[:-1]

        afores = [d['afore'] for d in afore_data]
        abs_values = [d['growth_absolute'] for d in afore_data]
        pct_values = [d['growth_percent'] for d in afore_data]
        currency = afore_data[0]['currency']

        values = abs_values
        ylabel = f"Growth ({currency} millions)"

        # Create figure
        fig, ax = plt.subplots(figsize=figsize)

        # Create bars with color coding (green for positive, red for negative)
        colors = ['#2ecc71' if v >= 0 else '#e74c3c' for v in values]
        bars = ax.bar(afores, values, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)

        # Customize chart
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
        ax.set_xlabel('Afore', fontsize=12, fontweight='bold')

        # Rotate x-axis labels for readability
        plt.xticks(rotation=45, ha='right')

        # Add value labels on bars
        for bar, val, pct in zip(bars, abs_values, pct_values):
            height = bar.get_height()

            # Format: $123M\n(5.4%)
            abs_str = f'${val:,.1f}M' if currency == 'USD' else f'${val:,.0f}M'
            label = f"{abs_str}\n({pct:.1f}%)"

            # Position label
            offset = (max(values) - min(values)) * 0.02
            if height >= 0:
                label_y = height + offset
                va = 'bottom'
            else:
                label_y = height - offset
                va = 'top'

            ax.text(bar.get_x() + bar.get_width()/2., label_y,
                   label,
                   ha='center', va=va,
                   fontsize=9, fontweight='bold',
                   linespacing=1.2)

        # Add horizontal line at zero
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1)

        # Format y-axis
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))

        # Add grid
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)

        # Adjust y-limit to fit labels
        ymin, ymax = ax.get_ylim()
        range_y = ymax - ymin
        ax.set_ylim(ymin - range_y * 0.1, ymax + range_y * 0.1)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    @staticmethod
    def create_comparison_bar_chart(
        afore_name: str,
        ytd_growth: float,
        one_year_growth: float,
        three_year_growth: Optional[float] = None,
        five_year_growth: Optional[float] = None,
        show_percentage: bool = False,
        currency: str = 'USD',
        output_path: Optional[str] = None,
        figsize: tuple = (10, 6)
    ) -> plt.Figure:
        """
        Create a bar chart comparing multiple time periods for a single Afore.
        """
        periods = ['YTD']
        values = [ytd_growth]

        periods.append('1 Year')
        values.append(one_year_growth)

        if three_year_growth is not None:
            periods.append('3 Year')
            values.append(three_year_growth)

        if five_year_growth is not None:
            periods.append('5 Year')
            values.append(five_year_growth)

        # Create figure
        fig, ax = plt.subplots(figsize=figsize)

        # Create bars
        colors = ['#3498db', '#2ecc71', '#f39c12', '#9b59b6'][:len(periods)]
        bars = ax.bar(periods, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1)

        # Customize chart
        title = f"{afore_name} - Multi-Period Growth Comparison"
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        if show_percentage:
            ylabel = "Growth (%)"
            value_format = '{:.1f}%'
        else:
            ylabel = f"Growth ({currency} millions)"
            value_format = '${:,.1f}M' if currency == 'USD' else '{:,.0f}M'

        ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')

        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   value_format.format(value),
                   ha='center', va='bottom',
                   fontsize=10, fontweight='bold')

        # Format y-axis
        if show_percentage:
            ax.yaxis.set_major_formatter(ticker.PercentFormatter())
        else:
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))

        # Add grid
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    @staticmethod
    def create_market_overview_chart(
        all_metrics: Dict,
        currency: str = 'USD',
        output_path: Optional[str] = None,
        figsize: tuple = (14, 8)
    ) -> plt.Figure:
        """
        Create a grouped bar chart showing market totals across all periods.
        """
        periods = ['YTD', '1 Year', '3 Year', '5 Year']
        period_keys = ['ytd', '1_year', '3_year', '5_year']

        # Extract market totals
        values = []
        percentages = []

        for key in period_keys:
            if key in all_metrics and currency in all_metrics[key]:
                market_total = all_metrics[key][currency][-1]
                values.append(market_total['end_value'])
                percentages.append(market_total['growth_percent'])
            else:
                values.append(0)
                percentages.append(0)

        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        # Chart 1: Absolute Values
        colors1 = ['#3498db', '#2ecc71', '#f39c12', '#9b59b6']
        bars1 = ax1.bar(periods, values, color=colors1, alpha=0.8, edgecolor='black', linewidth=1)

        ax1.set_title(f'Market Total AUM ({currency})', fontsize=14, fontweight='bold')
        ax1.set_ylabel(f'{currency} (millions)', fontsize=12, fontweight='bold')
        ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))

        # Add value labels
        for bar, value in zip(bars1, values):
            height = bar.get_height()
            label = f'${value:,.0f}M' if currency == 'USD' else f'{value:,.0f}M'
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    label, ha='center', va='bottom',
                    fontsize=9, fontweight='bold')

        ax1.grid(True, alpha=0.3, axis='y')
        ax1.set_axisbelow(True)

        # Chart 2: Growth Percentages
        colors2 = ['#2ecc71' if p >= 0 else '#e74c3c' for p in percentages]
        bars2 = ax2.bar(periods, percentages, color=colors2, alpha=0.8, edgecolor='black', linewidth=1)

        ax2.set_title('Market Growth (%)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Growth (%)', fontsize=12, fontweight='bold')
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)

        # Add value labels
        for bar, pct in zip(bars2, percentages):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{pct:.1f}%', ha='center',
                    va='bottom' if height >= 0 else 'top',
                    fontsize=9, fontweight='bold')

        ax2.grid(True, alpha=0.3, axis='y')
        ax2.set_axisbelow(True)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    @staticmethod
    def create_stacked_comparison(
        growth_data_dict: Dict[str, List[Dict]],
        title: str = "Multi-Concept Comparison",
        output_path: Optional[str] = None,
        figsize: tuple = (14, 8)
    ) -> plt.Figure:
        """
        Create a grouped bar chart comparing multiple concepts side by side.
        """
        # Get Afore names (excluding total)
        first_concept = list(growth_data_dict.values())[0]
        afores = [d['afore'] for d in first_concept[:-1]]

        # Number of concepts and afores
        n_concepts = len(growth_data_dict)
        n_afores = len(afores)

        # Set up the bar positions
        x = np.arange(n_afores)
        width = 0.8 / n_concepts

        fig, ax = plt.subplots(figsize=figsize)

        # Colors for different concepts
        colors = ['#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#e74c3c']

        # Create bars for each concept
        for i, (concept_name, growth_data) in enumerate(growth_data_dict.items()):
            values = [d['growth_percent'] for d in growth_data[:-1]]
            offset = width * i - (width * n_concepts / 2 - width / 2)
            ax.bar(x + offset, values, width, label=concept_name,
                  color=colors[i % len(colors)], alpha=0.8,
                  edgecolor='black', linewidth=0.5)

        # Customize chart
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_ylabel('Growth (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Afore', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(afores, rotation=45, ha='right')
        ax.legend(loc='best', framealpha=0.9)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    @staticmethod
    def close_all():
        """Close all matplotlib figures to free memory."""
        plt.close('all')
