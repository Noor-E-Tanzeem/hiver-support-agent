import pandas as pd
from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles import Font, Alignment
from pathlib import Path

INPUT_FILE = "data/processed/golden_set.csv"
OUTPUT_FILE = "data/processed/golden_set_annotation.xlsx"

print("Loading golden set...")

df = pd.read_csv(INPUT_FILE)

# Create the Excel file.
df.to_excel(
    OUTPUT_FILE,
    index=False,
    sheet_name="Golden Set"
)

# Open the workbook so we can add annotation controls.
wb = load_workbook(OUTPUT_FILE)
ws = wb["Golden Set"]

# ---------------------------------------------------------------
# Intent dropdown
# ---------------------------------------------------------------

intent_values = (
    "device_malfunction,"
    "battery_charging,"
    "connectivity_communication,"
    "apps_services,"
    "settings_how_to,"
    "software_update,"
    "orders_account_billing,"
    "hardware_accessories,"
    "other_unclear"
)

intent_validation = DataValidation(
    type="list",
    formula1=f'"{intent_values}"',
    allow_blank=True
)

intent_validation.error = "Please select a valid intent."
intent_validation.errorTitle = "Invalid intent"
intent_validation.prompt = "Choose the customer's primary support intent."
intent_validation.promptTitle = "Intent"

ws.add_data_validation(intent_validation)

# Column E = intent
intent_validation.add(f"E2:E{len(df) + 1}")

# ---------------------------------------------------------------
# Escalation dropdown
# ---------------------------------------------------------------

escalation_validation = DataValidation(
    type="list",
    formula1='"yes,no"',
    allow_blank=True
)

escalation_validation.error = "Choose yes or no."
escalation_validation.errorTitle = "Invalid escalation value"
escalation_validation.prompt = "Should this case be escalated?"
escalation_validation.promptTitle = "Escalation"

ws.add_data_validation(escalation_validation)

# Column F = should_escalate
escalation_validation.add(f"F2:F{len(df) + 1}")

# ---------------------------------------------------------------
# Escalation reason dropdown
# ---------------------------------------------------------------

reason_values = (
    "private_account_or_security,"
    "case_specific_diagnosis,"
    "transaction_or_billing,"
    "insufficient_information,"
    "sensitive_or_risky,"
    "historical_dm_routing,"
    "other"
)

reason_validation = DataValidation(
    type="list",
    formula1=f'"{reason_values}"',
    allow_blank=True
)

reason_validation.error = "Please select a valid escalation reason."
reason_validation.errorTitle = "Invalid reason"
reason_validation.prompt = "Select the main reason for escalation."
reason_validation.promptTitle = "Escalation reason"

ws.add_data_validation(reason_validation)

# Column G = escalation_reason
reason_validation.add(f"G2:G{len(df) + 1}")

# ---------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------

# Freeze the header row.
ws.freeze_panes = "A2"

# Enable filters.
ws.auto_filter.ref = ws.dimensions

# Make headers bold.
for cell in ws[1]:
    cell.font = Font(bold=True)
    cell.alignment = Alignment(
        horizontal="center",
        vertical="center"
    )

# Set useful column widths.
widths = {
    "A": 18,
    "B": 65,
    "C": 18,
    "D": 65,
    "E": 30,
    "F": 18,
    "G": 30,
    "H": 50,
}

for column, width in widths.items():
    ws.column_dimensions[column].width = width

# Wrap long text.
for row in ws.iter_rows():
    for cell in row:
        cell.alignment = Alignment(
            vertical="top",
            wrap_text=True
        )

# Make annotation columns visually obvious.
for row in range(2, len(df) + 2):
    ws[f"E{row}"].alignment = Alignment(
        vertical="top",
        wrap_text=True
    )
    ws[f"F{row}"].alignment = Alignment(
        vertical="top",
        wrap_text=True
    )
    ws[f"G{row}"].alignment = Alignment(
        vertical="top",
        wrap_text=True
    )
    ws[f"H{row}"].alignment = Alignment(
        vertical="top",
        wrap_text=True
    )

# Save.
Path(OUTPUT_FILE).parent.mkdir(
    parents=True,
    exist_ok=True
)

wb.save(OUTPUT_FILE)

print(f"Rows: {len(df)}")
print(f"Saved to: {OUTPUT_FILE}")
print()
print("Annotation columns:")
print("E = intent")
print("F = should_escalate")
print("G = escalation_reason")
print("H = annotation_notes")
