# CONSAR Database Units Documentation

## Critical Information

The CONSAR Siefore database has a specific units format that MUST be followed for consistency.

## Units Format in Historical Database

### valueMXN (MXN Values)
- **Stored as**: Thousands of pesos (miles de pesos)
- **Example**: `31,319,202,025` represents 31.3 billion thousands = 31.3 trillion pesos
- **To display in billions**: Divide by `1,000,000,000`
- **To display in millions**: Divide by `1,000,000`

### valueUSD (USD Values)
- **Stored as**: Actual USD amount
- **Example**: `287,138,864` represents 287 million USD
- **To display in millions**: Divide by `1,000,000`

## Extraction Process

### What the XLSX files contain
CONSAR XLSX files show values that represent "miles de pesos" (thousands of MXN).

Example from Reporte.xlsx:
```
XXI Banorte Pensiones: 31,319,202.02504
```

This value `31,319,202` means:
- 31,319,202 thousands of pesos
- = 31,319,202,000 pesos
- = 31.32 billions of pesos

### What extract_latest_month.py outputs
The extraction reads the XLSX value as-is: `31,319,202.03`

This is stored in `consar_latest_month.json` as `valueMXN: 31319202.03`

### What enrich_latest_month.py outputs
The enrichment calculates USD by dividing valueMXN by the FX rate:

```python
valueUSD = valueMXN / FX_rate
```

For the example:
```
valueMXN: 31,319,202.03
FX_rate: 18.5725
valueUSD: 31,319,202.03 / 18.5725 = 1,686,321.28
```

This represents 1.69 million USD (not thousands).

### What fix_units_and_integrate.py does
**CRITICAL STEP**: This script multiplies BOTH values by 1000:

```python
record['valueMXN'] = record['valueMXN'] * 1000
record['valueUSD'] = record['valueUSD'] * 1000
```

After multiplication:
```
valueMXN: 31,319,202,025.04 (now in historical format)
valueUSD: 1,686,321,280 (now in historical format)
```

## Display Conversions

### For MXN (showing in billions)
```python
mxn_billions = valueMXN / 1_000_000_000
```

Example: `31,319,202,025 / 1,000,000,000 = 31.32 billions MXN`

### For USD (showing in millions)
```python
usd_millions = valueUSD / 1_000_000
```

Example: `1,686,321,280 / 1,000,000 = 1,686.32 millions USD`

## Verification Example

October 2025 Azteca Total de Activo across all 10 Siefores:

```
Database valueMXN sum: 366,562,569,358 (thousands)
Display: 366,562,569,358 / 1,000,000,000 = 366.56 billions MXN

Database valueUSD sum: 19,736,854,792
Display: 19,736,854,792 / 1,000,000 = 19,736.85 millions USD
```

## Common Mistakes to Avoid

1. ❌ **DO NOT** use valueMXN as-is from extraction - it must be multiplied by 1000
2. ❌ **DO NOT** forget to multiply valueUSD by 1000 as well
3. ❌ **DO NOT** display MXN values as "millions" - they should be "billions"
4. ❌ **DO NOT** display USD values as "billions" - they should be "millions"

## Correct Workflow for Monthly Updates

1. Run `extract_latest_month.py` - outputs values as-is from XLSX
2. Run `enrich_latest_month.py` - calculates USD from MXN
3. Run `fix_units_and_integrate.py` - **multiplies both by 1000** before adding to database
4. Verify totals match expected ranges:
   - Total Industry AUM: ~6,000-8,000 billions MXN
   - Total Industry AUM: ~300-400 millions USD

## Historical Context

- **Pre-September 2025**: Database maintained correctly with GitHub releases
- **September-October 2025**: Initial extraction didn't multiply by 1000, causing 1000x discrepancy
- **Fix applied**: November 25, 2025 - corrected Sept/Oct data and documented process
