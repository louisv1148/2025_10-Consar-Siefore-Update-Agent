from typing import Dict, List, Tuple

class SummaryGenerator:
    """
    Generates natural language executive summaries based on calculated metrics.
    Uses rule-based logic to highlight key insights, trends, and top performers.
    """
    
    @staticmethod
    def generate_executive_dashboard_text(
        metrics_by_concept: Dict[str, Dict], 
        currency: str
    ) -> str:
        """
        User requested to remove all text from executive summary.
        """
        return ""
    
    @staticmethod
    def generate_active_fund_summary_table(
        metrics_by_concept: Dict[str, Dict],
        monthly_stats: List[Tuple[str, List[Dict]]],  # List of (MonthName, GrowthData)
        currency: str
    ) -> Tuple[List[str], List[List[str]]]:
        """
        Generate table showing Fund AUM and the change for each of the last 3 individual months.
        """
        # Dynamic headers: Afore, Fund AUM, [Month 1], [Month 2], [Month 3]
        headers = ["Afore", "Fund AUM"] + [f"{m} Change" for m, _ in monthly_stats]
        
        funds = metrics_by_concept.get('mutual_funds', {})
        funds_ytd = funds.get('ytd', {}).get(currency, [])
        
        rows = []
        
        # Get all afores from ytd data
        afores = sorted([d['afore'] for d in funds_ytd if d['afore'] != 'MARKET TOTAL'])
        
        def get_item_stat(data_list, afore_name):
            item = next((d for d in data_list if d['afore'] == afore_name), {})
            return item.get('growth_absolute', 0), item.get('growth_percent', 0)

        for afore in afores:
            fund_data = next((d for d in funds_ytd if d['afore'] == afore), {})
            fund_aum = fund_data.get('end_value', 0)
            
            row = [afore, f"${fund_aum:,.0f}M"]
            
            # Add stats for each month
            for _, stat_list in monthly_stats:
                m_abs, m_pct = get_item_stat(stat_list, afore)
                row.append(f"${m_abs:,.0f}M ({m_pct:+.1f}%)")
            
            rows.append(row)
        
        # Add market total
        fund_total_data = next((d for d in funds_ytd if d['afore'] == 'MARKET TOTAL'), {})
        total_row = ["MARKET TOTAL", f"${fund_total_data.get('end_value', 0):,.0f}M"]
        
        for _, stat_list in monthly_stats:
            m_abs_t, m_pct_t = get_item_stat(stat_list, "MARKET TOTAL")
            total_row.append(f"${m_abs_t:,.0f}M ({m_pct_t:+.1f}%)")
            
        rows.append(total_row)
        
        return headers, rows
    
    @staticmethod
    def generate_total_aum_table(
        total_assets_metrics: Dict,
        currency: str
    ) -> Tuple[List[str], List[List[str]]]:
        """
        Generate table showing Total AUM for each Afore and market.
        
        Returns:
            Tuple of (headers, data_rows)
        """
        headers = ["Afore", "Total AUM", "Market Share %"]
        
        ytd_data = total_assets_metrics.get('ytd', {}).get(currency, [])
        
        # Get market total
        market_total = next((d for d in ytd_data if d['afore'] == 'MARKET TOTAL'), {})
        market_aum = market_total.get('end_value', 1)  # Avoid division by zero
        
        # Get afores sorted by AUM
        afores_data = sorted(
            [d for d in ytd_data if d['afore'] != 'MARKET TOTAL'],
            key=lambda x: x['end_value'],
            reverse=True
        )
        
        rows = []
        for data in afores_data:
            aum = data['end_value']
            share = (aum / market_aum * 100) if market_aum > 0 else 0
            
            rows.append([
                data['afore'],
                f"${aum:,.0f}M",
                f"{share:.1f}%"
            ])
        
        # Add market total
        rows.append([
            "MARKET TOTAL",
            f"${market_aum:,.0f}M",
            "100.0%"
        ])
        
        return headers, rows
