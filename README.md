# MommyShops MVP - Ingredient Analysis API

A FastAPI-based application that analyzes cosmetic and food ingredients for safety and eco-friendliness, with WhatsApp integration and AI-powered enrichment via Nanobot.

## Features

- **OCR Processing**: Extract ingredients from product labels using Tesseract
- **Multi-Source Analysis**: Integrates data from FDA, PubChem, EWG, IARC, INVIMA, and COSING
- **WhatsApp Integration**: Receive images via WhatsApp and send analysis results
- **MCP Integration**: Model Context Protocol for AI-powered ingredient enrichment
- **Database Caching**: SQLAlchemy-based caching of ingredient data
- **Parallel API Calls**: Optimized performance with concurrent API requests

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WhatsApp      │───▶│   FastAPI App    │───▶│   Database      │
│   Webhook       │    │   (main.py)      │    │   (PostgreSQL)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   External APIs  │
                       │  (FDA, EWG, etc) │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Nanobot/MCP    │
                       │   (AI Analysis)  │
                       └──────────────────┘
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL
- Tesseract OCR
- Docker (for Nanobot, optional)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR

**macOS (using Homebrew):**
```bash
brew install tesseract
brew install tesseract-lang  # For Spanish support
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

**Windows:**
Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)

### 3. Database Setup

Create a PostgreSQL database:
```sql
CREATE DATABASE mommyshops_db;
CREATE USER postgres WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE mommyshops_db TO postgres;
```

### 4. Environment Configuration

Copy and configure the `.env` file:
```bash
cp .env.example .env
```

Update the following variables:
- `DATABASE_URL`: Your PostgreSQL connection string
- `TESSERACT_PATH`: Path to tesseract executable
- `META_ACCESS_TOKEN`: WhatsApp Business API token
- `META_PHONE_NUMBER_ID`: Your WhatsApp phone number ID
- `EWG_API_KEY`: EWG Skin Deep API key (optional)
- `ENTREZ_EMAIL`: Email for PubChem Power User Gateway queries
- `MCP_ACCESS_TOKEN`: Token for MCP authentication

### 5. Initialize Database

```bash
python init_db.py
```

### 6. Run the Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 7. Setup Nanobot (Optional)

If you want to use AI-powered ingredient enrichment:

```bash
cd nanobot
docker build -t nanobot .
docker run -p 8080:8080 nanobot
```

## API Endpoints

### Core Endpoints

- `GET /`: Health check
- `POST /whatsapp/webhook`: WhatsApp webhook handler

### MCP Endpoints (for Nanobot integration)

- `POST /mcp/fda_search`: Search FDA database
- `POST /mcp/pubchem_query`: Query PubChem
- `POST /mcp/ewg_score`: Get EWG score
- `POST /mcp/iarc_check`: Check IARC carcinogenicity
- `POST /mcp/invima_scrape`: Scrape INVIMA
- `POST /mcp/cosing_lookup`: Lookup COSING
- `POST /mcp/enrich_ingredient`: Save ingredient data
- `POST /mcp/analyze_ingredients`: Analyze ingredient list

## Usage

### WhatsApp Integration

1. Send a text message to your WhatsApp Business number
2. Send an image of a product label
3. Receive ingredient analysis with safety scores and recommendations

### Direct API Usage

```python
import httpx

# Analyze ingredients directly
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/mcp/analyze_ingredients",
        json={
            "ingredients": ["parabenos", "glicerina"],
            "user_need": "sensitive skin"
        }
    )
    result = response.json()
```

## Data Sources

- **FDA**: Food and cosmetic enforcement actions
- **PubChem**: Chemical properties and descriptions
- **EWG Skin Deep**: Eco-friendliness scores and concerns
- **IARC**: Carcinogenicity data via PubMed
- **INVIMA**: Colombian regulatory approval status
- **COSING**: EU cosmetic ingredient functions

## Development

### Running Tests

```bash
pytest test.py
```

### Code Formatting

```bash
black .
flake8 .
```

### Database Migrations

```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Configuration Files

- `config.yaml`: Nanobot agent configuration
- `.env`: Environment variables
- `requirements.txt`: Python dependencies
- `database.py`: Database models and utilities
- `api_utils.py`: External API integrations

## Troubleshooting

### Common Issues

1. **Tesseract not found**: Ensure Tesseract is installed and path is correct in `.env`
2. **Database connection**: Check PostgreSQL is running and credentials are correct
3. **API timeouts**: Some external APIs may be slow; check network connectivity
4. **WhatsApp webhook**: Ensure webhook URL is accessible and tokens are valid

### Logs

The application uses structured logging. Check logs for detailed error information:

```bash
tail -f logs/app.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue on GitHub or contact the development team.# Force Railway rebuild - Thu Oct  9 09:21:19 -03 2025
