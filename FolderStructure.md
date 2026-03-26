3. Folder Structure

Here’s a clean, production-style structure:

peytznotes/
│
├── frontend/                # Next.js app
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── styles/
│
├── backend/                # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── services/
│   │   ├── models/
│   │   └── utils/
│   │
│   └── requirements.txt
│
├── ingestion/              # data pipeline
│   ├── notion_parser.py
│   ├── chunker.py
│   ├── embedder.py
│   ├── uploader.py
│   └── run_pipeline.py
│
├── db/
│   ├── schema.sql
│   └── migrations/
│
├── scripts/
│   └── test_queries.py
│
├── .env
├── docker-compose.yml
└── README.md