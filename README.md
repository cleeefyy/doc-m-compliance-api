# doc_m_compliance_checker

A Python tool for evaluating architectural WC layouts against UK Approved Document M (2024) accessibility standards. This tool extracts spatial data from CAD floorplans and section views, semantically searches regulation content using OpenAI embeddings, and generates GPT-4 Turbo–powered compliance reports grounded in specific diagrams and clauses.

## Features

- Extracts geometry from DXF floorplans (toilets, grab rails, doors, turning circles)
- Extracts vertical heights from section views (basin, toilet seat, grab rails, shelf)
- Evaluates spatial data using a RAG (Retrieval-Augmented Generation) setup with GPT-4 Turbo
- Searches across Document M text and summarised diagrams (18 to 22)
- Produces structured compliance reports with citations and suggested fixes

## Project Structure

doc_m_compliance_checker/
├── floorplans/               # Input DXF files (plan and section)
├── outputs/                  # Auto-generated spatial data JSONs
├── embeddings/               # Vector embeddings of Document M text and diagrams
├── chunks/                   # Chunked Document M text and manual diagram summaries
├── doc_m_project/            # Main processing scripts
│   ├── embed_chunks.py
│   ├── embed_diagrams.py
│   ├── extract_dxf.py
│   ├── extract_section_heights.py
│   ├── rag_compliance.py
├── .env                      # OpenAI API key (not tracked)
├── .gitignore
├── requirements.txt
└── README.md

## Requirements

- Python 3.8+
- openai
- ezdxf
- numpy
- python-dotenv

Install all dependencies:

pip3 install -r requirements.txt

## API Key

Create a file called `.env` in the root of the project with the following content:

OPENAI_API_KEY=sk-proj-...

This file should not be committed to Git. It is excluded by the `.gitignore`.

## How to Use

1. Extract geometry from the floorplan DXF:

python3 extract_dxf.py

2. Extract vertical heights from the section view:

python3 extract_section_heights.py

3. Run the GPT-4 Turbo compliance checker:

python3 rag_compliance.py

The tool will output a compliance report referencing Document M guidance and diagrams.

## Notes

- Regulation and diagram content was embedded for semantic retrieval
- Diagrams 18–22 are manually summarised and embedded
- Embedding model: text-embedding-3-small
- Language model: gpt-4-turbo

## License

MIT License
