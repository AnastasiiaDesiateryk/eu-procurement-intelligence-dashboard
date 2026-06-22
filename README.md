# EU Procurement Intelligence Dashboard

A full-stack data analytics platform that transforms public EU procurement data into supply-chain intelligence.

The project uses TED (Tenders Electronic Daily) data and turns large public procurement tables into readable dashboards, rankings, and indicators for procurement and supply-chain analysis.

## What is TED?

TED stands for **Tenders Electronic Daily**. It is the EU's public procurement portal where tender notices and contract award information are published.

In simple terms, TED contains open data about public tenders: who buys, who supplies, what is purchased, in which country, for what value, and when the tender was published or awarded.

## What this platform does

This prototype analyses approximately **1.5M+ EU TED procurement records** and provides:

- spend analysis by country and year;
- buyer-side and supplier-side views;
- CPV category rankings with readable category names;
- Top-10 suppliers and buyers;
- Tender Lead Time metrics;
- average and median contract value indicators;
- data quality and outlier-oriented SQL views;
- an interactive React dashboard;
- a FastAPI backend;
- PostgreSQL analytical views;
- Docker Compose setup for reproducible local execution.

## Why this matters

Public procurement data is large, fragmented, and difficult to interpret directly. This platform shows how raw open data can be cleaned, structured, and transformed into business-oriented insights.

It can help answer questions such as:

- Which countries spend the most in public procurement?
- Which procurement categories dominate in a selected country?
- Who are the top suppliers or buyers?
- Which countries have shorter or longer Tender Lead Time?
- Where are possible spending patterns or outliers visible?

## Tech stack

- React + Vite + TypeScript
- FastAPI + SQLAlchemy
- PostgreSQL
- Python ETL scripts
- SQL analytical views
- Docker Compose

## Project Structure

```text
SupplyChainMVP/
├── api.py
├── Dockerfile.api
├── docker-compose.yml
├── requirements.txt
├── README.md
├── .env
├── .env.example
├── .gitignore
│
├── app/                         # React + Vite frontend
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── styles.css
│       ├── components/
│       │   ├── KPI.tsx
│       │   ├── Nav.tsx
│       │   └── SupersetEmbed.tsx
│       └── pages/
│           ├── Overview.tsx
│           ├── Suppliers.tsx
│           └── Finance.tsx
│
├── etl/                         # Python ETL and data preparation scripts
│   ├── eu_ted.py
│   ├── inspect_ted_columns.py
│   ├── kpi.py
│   ├── load_cpv_dict.py
│   ├── peek_ted.py
│   └── test_db.py
│
├── sql/                         # DDL and analytical SQL views
│   ├── constraints.sql
│   ├── ddl.sql
│   ├── dq_views.sql
│   ├── lt_outliers.sql
│   ├── v_country_tlt.sql
│   ├── views.sql
│   ├── views_cpv.sql
│   ├── views_dio_dso.sql
│   ├── views_finance.sql
│   ├── views_finance_basic.sql
│   └── views_kpi.sql
│
├── data/                        # Local data storage
│   ├── cpv/
│   └── eu/
│
├── pgdata/                      # PostgreSQL volume data
├── superset_home/               # Apache Superset local config/data
│
├── dash/                        # Optional dashboard-related assets
├── __pycache__/
├── .venv/
│
```

## Running locally
This project uses large local data and database files that are not stored in this repository.

Before starting the app, place the following archives in the project root:

data.zip 

pgdata.zip


Then unzip them:

unzip data.zip
unzip pgdata.zip

After extraction, the project root should contain:

data/
pgdata/

The data/ folder contains the raw TED procurement files.
The pgdata/ folder contains the local PostgreSQL database volume used by Docker.

Create a local environment file:

cp .env.example .env

Start the full stack:

docker compose up -d --build

Open:

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs
- Adminer: http://localhost:8080
- Superset: http://localhost:8088

## Data note

Raw TED data, local database files, and secrets are not committed to this repository.

The repository contains the application code, ETL scripts, SQL views, Docker configuration, and environment template.

## Status

This is an MVP / exploratory prototype designed to demonstrate how open procurement data can be transformed into supply-chain and procurement intelligence.

## Disclaimer

This project is not affiliated with the European Union or TED. It uses public procurement data for educational, analytical, and prototyping purposes.
