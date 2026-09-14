"""
Phase 4 - Step 2: vendors.csv
-------------------------------
Builds the Vendor dimension table.

Design decision: vendors are NOT random. Each is assigned a
Vendor_Category that maps to real workstreams in our task framework
(e.g. "MEP Contractor" vendors will later be linked to Engineering's
"MEP Systems" workstream tasks). This keeps Step 3 (assigning
Vendor_ID to each task) logical instead of arbitrary.

All names below are fully fictional (no real companies).
"""

import pandas as pd

vendors_raw = [
    # (Vendor_ID, Vendor_Name, Vendor_Category)
    ("VEN-IT-01", "Falcon Networks Systems", "IT Systems Integration"),
    ("VEN-IT-02", "Horizon PMS Solutions", "IT Systems Integration"),
    ("VEN-IT-03", "BlueWave Telecom", "IT Systems Integration"),
    ("VEN-IT-04", "NexaPoint IT Integrators", "IT Systems Integration"),

    ("VEN-SEC-01", "Sentinel Vision Security", "Security Systems"),
    ("VEN-SEC-02", "Gulf Shield Access Systems", "Security Systems"),
    ("VEN-SEC-03", "Argus Screening Technologies", "Security Systems"),

    ("VEN-MEP-01", "Coastal MEP Contractors", "MEP Contractor"),
    ("VEN-MEP-02", "Al-Marsa Electrical Works", "MEP Contractor"),
    ("VEN-MEP-03", "Desert Breeze HVAC Co.", "MEP Contractor"),

    ("VEN-FLS-01", "Redline Fire Safety", "Fire & Life Safety"),
    ("VEN-FLS-02", "SafeGuard Life Systems", "Fire & Life Safety"),

    ("VEN-ELE-01", "Ascendia Elevators", "Vertical Transportation"),

    ("VEN-FFE-01", "Coral Bay Furnishings", "FF&E Supplier"),
    ("VEN-FFE-02", "Lumina Lighting Design", "FF&E Supplier"),
    ("VEN-FFE-03", "Artisan Gallery Decor", "FF&E Supplier"),
    ("VEN-FFE-04", "Regency Guestroom Furniture", "FF&E Supplier"),

    ("VEN-OSE-01", "Amenity Source Co.", "OS&E Supplier"),
    ("VEN-OSE-02", "Prime Smallwares Supply", "OS&E Supplier"),
    ("VEN-OSE-03", "CleanPro Supplies", "OS&E Supplier"),

    ("VEN-KIT-01", "SteelChef Kitchen Equipment", "Kitchen Equipment"),
    ("VEN-KIT-02", "Nordic Cold Storage Systems", "Kitchen Equipment"),

    ("VEN-FB-01", "Harbor Fresh Foods", "F&B Supplier"),
    ("VEN-FB-02", "Vintage Cellars Beverage Co.", "F&B Supplier"),
    ("VEN-FB-03", "Coastal Produce Distributors", "F&B Supplier"),
    ("VEN-FB-04", "Golden Grain Bakery Supply", "F&B Supplier"),

    ("VEN-LND-01", "Pearl Linen Services", "Laundry & Linen"),
    ("VEN-LND-02", "CrystalWash Laundry Solutions", "Laundry & Linen"),

    ("VEN-UNI-01", "Prestige Uniform Co.", "Uniform Supplier"),

    ("VEN-TRN-01", "Apex Hospitality Recruitment", "Training & Recruitment Agency"),
    ("VEN-TRN-02", "ServiceFirst Training Institute", "Training & Recruitment Agency"),

    ("VEN-MKT-01", "Skyline Digital Agency", "Marketing & Digital Agency"),
    ("VEN-MKT-02", "BrightPath Marketing Group", "Marketing & Digital Agency"),

    ("VEN-PR-01", "Meridian PR & Communications", "PR Agency"),

    ("VEN-AV-01", "ClearView AV Solutions", "Audio-Visual & IPTV"),

    ("VEN-PRO-01", "Sterling Audit & Advisory", "Professional Services"),
]

vendors_df = pd.DataFrame(vendors_raw, columns=["Vendor_ID", "Vendor_Name", "Vendor_Category"])

# --- Sanity checks ---
assert vendors_df["Vendor_ID"].is_unique, "Duplicate Vendor_ID found!"
assert len(vendors_df) == 36, f"Expected 36 vendors, got {len(vendors_df)}"

vendors_df.to_csv("vendors.csv", index=False)

print(f"Total vendors: {len(vendors_df)}")
print(f"Total categories: {vendors_df['Vendor_Category'].nunique()}")
print()
print("Vendors per category:")
print(vendors_df["Vendor_Category"].value_counts())
