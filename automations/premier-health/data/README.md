# Premier Health Insurance - Provider Data

**Generated**: October 16, 2025
**Source**: PHI SERVICE PROVIDER LIST - UPDATED_4.xlsx
**Total Providers**: 753
**Regions Covered**: 106

---

## 📁 Files Overview

| File | Description | Records | Size |
|------|-------------|---------|------|
| **premier_health_master_provider_list.csv** | All 753 providers in one file | 753 | 75.56 KB |
| **premier_health_specialties.csv** | All medical specialties offered | 98 | ~5 KB |
| **provider_analysis_report.md** | Comprehensive data analysis | - | ~30 KB |
| **by_region/*.csv** | 106 individual region files | 753 total | ~428 KB |

---

## 🗂️ File Descriptions

### 1. Master Provider List
**File**: `premier_health_master_provider_list.csv`

Complete list of all 753 healthcare providers across Ghana.

**Columns**:
- `Region` - Geographic region/area
- `Number` - Provider sequence number within region
- `Hospital/Clinic` - Facility name
- `Speciality` - Medical services offered (abbreviated)
- `Contact` - Phone number(s)
- `Location` - Specific address/landmark
- `Sub-Region` - Sub-area within main region

**Usage**:
```python
import pandas as pd
df = pd.read_csv('premier_health_master_provider_list.csv')
print(f"Total providers: {len(df)}")
```

---

### 2. Specialties List
**File**: `premier_health_specialties.csv`

Complete list of all medical specialties covered by Premier Health network.

**Columns**:
- `Abbreviation` - Specialty abbreviation (e.g., GP, OBS, GYN)
- `Full Name` - Full specialty name
- `Provider Count` - Number of providers offering this specialty
- `Percentage` - Percentage of total providers

**Top Specialties**:
1. General Practice (GP) - 410 providers (54.4%)
2. Gynecology (GYN) - 210 providers (27.9%)
3. Obstetrics (OBS) - 196 providers (26.0%)
4. Physiotherapy (PHY) - 184 providers (24.4%)
5. Pharmacy - 144 providers (19.1%)

**Usage**:
```python
import pandas as pd
df = pd.read_csv('premier_health_specialties.csv')
top_10 = df.head(10)
print(top_10)
```

---

### 3. Regional CSVs
**Directory**: `by_region/`
**Files**: 106 CSV files (one per region)

Each file contains providers for a specific geographic region.

**Naming Convention**: `{region_name}.csv` (lowercase, underscores)

**Examples**:
- `madina__adenta__dodowa.csv` - 22 providers
- `tamale.csv` - 44 providers
- `takoradi.csv` - 37 providers
- `east_legon__adjringanor.csv` - 20 providers

**Usage**:
```python
import pandas as pd
import glob

# Load all regional files
csv_files = glob.glob('by_region/*.csv')
for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    region = csv_file.split('/')[-1].replace('.csv', '')
    print(f"{region}: {len(df)} providers")
```

---

### 4. Analysis Report
**File**: `provider_analysis_report.md`

Comprehensive analysis including:
- Regional distribution statistics
- Specialty breakdown and categories
- Contact information quality assessment
- Data quality scores
- Recommendations for knowledge base integration

---

## 📊 Key Statistics

### Regional Distribution

| Region Type | Providers | Percentage |
|-------------|-----------|------------|
| Greater Accra | ~340 | 45% |
| Ashanti | ~96 | 13% |
| Northern | ~78 | 10% |
| Western | ~70 | 9% |
| Eastern | ~71 | 9% |
| Brong-Ahafo | ~71 | 9% |
| Central | ~29 | 4% |
| Volta | ~15 | 2% |

### Specialty Categories

| Category | Provider Entries |
|----------|------------------|
| Primary Care (GP) | 410 |
| Women's Health (OBS/GYN) | 450+ |
| Children's Health (PED) | 176 |
| Surgery | 177 |
| Rehabilitation (PHY) | 194 |
| Pharmacy | 144 |
| Eye Care | 129 |
| Dental | 40 |

### Data Quality

- **Contact Information**: 89.9% complete (677/753 providers)
- **Location Data**: 99.3% complete (748/753 providers)
- **Multiple Contacts**: 62.8% have backup phone numbers
- **Average Phones per Provider**: 2.10

---

## 🔧 How to Use This Data

### For Knowledge Base Import

**Method 1: Bulk Import (Recommended)**
Use the master CSV file to import all providers at once:

```python
import pandas as pd
import httpx

df = pd.read_csv('premier_health_master_provider_list.csv')

for region in df['Region'].unique():
    region_data = df[df['Region'] == region]

    # Create document content
    content = f"# Healthcare Providers in {region}\n\n"
    for _, row in region_data.iterrows():
        content += f"## {row['Hospital/Clinic']}\n"
        content += f"**Specialties**: {row['Speciality']}\n"
        content += f"**Phone**: {row['Contact']}\n"
        content += f"**Location**: {row['Location']}\n\n"

    # Send to knowledge base API
    response = httpx.post(
        "https://api.ailabsafrica.com/knowledge-base/documents",
        params={"company_name": "premier_health_production"},
        json={
            "title": f"Healthcare Providers in {region}",
            "content": content,
            "category": "provider_directory",
            "tags": ["provider_list", "healthcare", region.lower()]
        }
    )
```

**Method 2: Frontend Upload**
1. Navigate to Knowledge Base page in B2C Portal
2. Select "Upload" tab
3. Upload regional CSV files one by one
4. System will automatically parse and index

**Method 3: Manual Entry**
Use the "Manual Entry" tab in the Knowledge Base page to add providers individually.

---

### For Data Analysis

**Provider Search**:
```python
import pandas as pd

df = pd.read_csv('premier_health_master_provider_list.csv')

# Find providers in specific region
madina_providers = df[df['Region'].str.contains('Madina', case=False)]

# Find providers by specialty
pediatricians = df[df['Speciality'].str.contains('PED|PAED', case=False, na=False)]

# Find providers with multiple contacts
multi_contact = df[df['Contact'].str.contains('/', na=False)]
```

**Specialty Analysis**:
```python
import pandas as pd

df = pd.read_csv('premier_health_specialties.csv')

# Top 10 specialties
top_10 = df.head(10)

# Specialties with >100 providers
common_specialties = df[df['Provider Count'] > 100]
```

---

### For VAPI/Voice Assistant Integration

Create region-specific queries:

```python
# Example: Query for doctors in Madina
query = "Find me doctors in Madina"

# RAG system will search regional documents
# Returns: Providers from madina__adenta__dodowa.csv
```

---

## ⚠️ Known Issues

### API Import Issue
**Status**: ❌ Not Working
**Error**: `'dict' object has no attribute 'id'`
**Impact**: Cannot bulk import via API currently

**Workaround Solutions**:
1. Use frontend upload feature in B2C Portal
2. Use direct database insertion script
3. Fix API endpoint (requires backend debugging)

**To Fix**:
- Check `/opt/kasaai/apps/core_backend/backend/routes/knowledge_base.py:280`
- Verify `DocumentManagementService.create_document()` return type
- Ensure response.document is not None before accessing .id

---

## 🚀 Next Steps

### Immediate Actions
1. ✅ CSV files created and organized
2. ✅ Master CSV generated
3. ✅ Specialties CSV generated
4. ✅ Analysis report completed
5. ⏳ Import data into knowledge base (via frontend or fix API)
6. ⏳ Test RAG queries with regional data

### Future Enhancements
1. Add GPS coordinates for mapping
2. Implement contact verification system
3. Add provider availability scheduling
4. Include facility photos and ratings
5. Add insurance tier details
6. Implement real-time status updates
7. Create mobile app integration
8. Add patient review system

---

## 📞 Support

For questions or issues with this data:
- Contact: AI Labs Africa Team
- Email: ailabsafrica@gmail.com
- Documentation: See `provider_analysis_report.md`

---

## 📝 Change Log

### October 16, 2025
- ✅ Initial extraction from Excel file
- ✅ Created 106 regional CSV files
- ✅ Generated master provider list
- ✅ Created specialties breakdown
- ✅ Completed data analysis report
- ❌ API import blocked (pending fix)

---

**Last Updated**: October 16, 2025
**Data Version**: 1.0
**Source File**: PHI SERVICE PROVIDER LIST - UPDATED_4.xlsx
**Status**: ✅ READY FOR USE
