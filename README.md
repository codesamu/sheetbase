# 📊 Sheetbase  
### *Datasheet + Database, Combined.*

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-Web_App-000000?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" />
  <img src="https://img.shields.io/badge/TailwindCSS-UI-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" />
  <img src="https://img.shields.io/badge/OpenRouter-AI_API-8A2BE2?style=for-the-badge" />
  <img src="https://img.shields.io/badge/PyMuPDF-PDF_Processing-009688?style=for-the-badge" />
</p>

<p align="center">
  <b>Structured like a spreadsheet. Powered like a database. Enhanced with AI.</b>
</p>

---

## ✨ Overview

**Sheetbase** combines the familiarity of datasheets with the power of modern databases.

Think:

- 📄 Spreadsheet-like data management  
- 🗄 PostgreSQL-backed structured storage  
- 🤖 AI-assisted querying and automation  
- 📑 PDF ingestion and preprocessing  
- 🌐 Lightweight Flask web interface  
- 🎨 Modern Tailwind-powered UI  

Built for managing, exploring, and enriching structured data with AI.

---

## 🚀 Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python + Flask |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| AI Integration | OpenRouter (Free API) |
| Document Processing | PyMuPDF |
| Frontend | Tailwind CSS |

---

## 🏗 Architecture

```text
                ┌───────────────────┐
                │   Tailwind UI      │
                └────────┬──────────┘
                         │
                    Flask App
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    SQLAlchemy      OpenRouter AI      PyMuPDF
         │               │               │
         └────────── PostgreSQL ─────────┘
                        │
```

---

## 📂 Project Structure

```bash
sheetbase/
├── app/
│   ├── routes/
│   ├── models/
│   ├── services/
│   └── templates/
├── static/
├── pdf_processing/
├── database/
├── config.py
├── app.py
└── README.md
```

---

## ⚙️ Setup

### Clone

```bash
git clone https://github.com/yourname/sheetbase.git
cd sheetbase
```

### Install

```bash
pip install -r requirements.txt
```

### Run

```bash
flask run
```
---

## Documentation
https://www.notion.so/Sheetbase-34962c2b0df980a6aa36cc3a143a7f23?source=copy_link
