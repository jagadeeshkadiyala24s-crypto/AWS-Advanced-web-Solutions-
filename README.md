# Graphene Trace Django Project

A Django implementation of the Graphene Trace case study, built using the structure of your original role-based healthcare project as inspiration.

## What is included

- Custom user model with three roles: admin, clinician, patient
- Patient dashboard with:
  - 32x32 pressure heatmap viewer
  - key metrics (Peak Pressure Index and Contact Area %)
  - selectable time windows (1h, 6h, 24h, all)
  - alerts and plain-English summaries
  - timestamp-linked patient comments
- Clinician dashboard with:
  - alerts queue
  - patient list
  - threaded replies to patient comments
  - review view for a single patient
- Admin dashboard with user / session / alert counts and quick links
- CSV importer for the GTLB dataset
- Demo database seeded from the provided files

## Demo accounts

After setup, or using the included `db.sqlite3`:

- Admin: `admin` / `admin123`
- Clinician: `clinician1` / `clinician123`
- Patients: usernames are generated from the CSV user ids, each with password `patient123`

## Quick start

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py import_pressure_data sample_data/GTLB-Data
python manage.py runserver
```

## URLs

- Login: `/`
- Admin dashboard: `/dashboard/admin/`
- Clinician dashboard: `/dashboard/clinician/`
- Patient dashboard: `/dashboard/patient/`

## Notes

- The importer creates missing patients automatically from the CSV filenames.
- Each 32 rows in a CSV file are treated as one frame.
- Recorded timestamps are inferred at 1-second intervals within each file.
- High-pressure regions are detected using connected components and configurable thresholds in `dashboard/utils.py`.
