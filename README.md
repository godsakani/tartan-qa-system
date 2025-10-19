# RAG Academic Advisor API

A FastAPI-based Retrieval-Augmented Generation (RAG) system that serves as an academic advisor chatbot for Carnegie Mellon University Africa. The system uses Google's Gemini AI model and vector search to provide accurate answers about academic policies, course registration, and degree planning.

## Features

- 📚 **Document Upload & Processing**: Upload PDF, DOCX, and HTML documents
- 🔍 **Intelligent Search**: Vector-based document retrieval using HuggingFace embeddings
- 🤖 **AI-Powered Responses**: Google Gemini integration for natural language responses
- 💬 **Chat History**: Maintains conversation context for better responses
- 📊 **Document Management**: Track and manage uploaded documents
- 🔧 **Debug Tools**: Built-in endpoints for testing and debugging

## Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **AI Model**: Google Gemini (gemini-2.5-flash)
- **Vector Store**: ChromaDB with HuggingFace embeddings
- **Document Processing**: PyPDF, docx2txt
- **Database**: SQLite
- **Deployment**: Render.com ready

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Google AI API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd rag-fastapi-project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your Google API key
   GOOGLE_API_KEY=your_google_api_key_here
   ```

5. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Endpoints

### Core Endpoints

- `GET /` - Health check and API info
- `POST /chat` - Main chat endpoint for asking questions
- `POST /upload-doc` - Upload documents (PDF, DOCX, HTML)
- `GET /all-docs` - List all uploaded documents
- `POST /delete-doc` - Delete a document by ID

### Debug Endpoints

- `GET /debug-search` - Test document search functionality
- `POST /clear-vectorstore` - Clear all documents from vector store

### Example Usage

#### Upload a Document
```bash
curl -X POST "http://localhost:8000/upload-doc" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@handbook.pdf"
```

#### Ask a Question
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the tracks for MS IT students?",
    "session_id": "user123",
    "model": "gemini-1.5-pro"
  }'
```

## Project Structure

```
rag-fastapi-project/
├── main.py                 # FastAPI application and routes
├── langchain_utils.py      # RAG chain and AI model integration
├── chroma_utils.py         # Vector store and document processing
├── db_utils.py             # Database operations
├── pydantic_models.py      # Data models and schemas
├── requirements.txt        # Python dependencies
├── render.yaml            # Render deployment configuration
├── .env                   # Environment variables (not in git)
├── data/                  # Persistent data directory
│   ├── rag_app.db        # SQLite database
│   └── chroma_db/        # Vector store data
└── README.md             # This file
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI API key for Gemini model | Yes |
| `DATA_DIR` | Directory for persistent data storage | No (default: ./data) |

### Supported File Types

- **PDF**: Academic handbooks, policy documents
- **DOCX**: Word documents with course information
- **HTML**: Web-based documentation

## Deployment

### Deploy to Render

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create Render Service**
   - Go to [render.com](https://render.com)
   - Create new Web Service
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` configuration

3. **Set Environment Variables**
   - Add `GOOGLE_API_KEY` in Render dashboard
   - Set `DATA_DIR` to `/opt/render/project/src/data`

### Alternative Deployment Options

- **Railway**: `railway up`
- **Google Cloud Run**: Use provided Dockerfile
- **AWS Lambda**: Requires serverless framework setup
- **Heroku**: Use Procfile (included)

## Usage Examples

### Academic Advisor Queries

The system is designed to answer questions about CMU Africa academics:

- "What are the tracks for MS IT students?"
- "What are the graduation requirements for MSIT?"
- "How do I register for courses?"
- "What is the academic integrity policy?"

### Document Management

```python
# Upload academic handbook
POST /upload-doc
Content-Type: multipart/form-data
file: handbook.pdf

# Query the uploaded content
POST /chat
{
  "question": "What are the degree requirements?",
  "session_id": "student123"
}
```

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Adding New Features

1. **New Document Types**: Extend `chroma_utils.py`
2. **Custom AI Models**: Modify `langchain_utils.py`
3. **Additional Endpoints**: Add to `main.py`

### Debug Mode

Enable detailed logging by setting debug endpoints:

```bash
# Check vector store contents
GET /debug-search?query=your_search_term

# Clear all documents
POST /clear-vectorstore
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Google API Errors**: Verify your API key is valid
   ```bash
   # Test API key
   curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
     https://generativelanguage.googleapis.com/v1beta/models
   ```

3. **Memory Issues**: Use lighter requirements for deployment
   ```bash
   pip install -r requirements-light.txt
   ```

4. **Vector Store Issues**: Clear and rebuild
   ```bash
   POST /clear-vectorstore
   # Re-upload documents
   ```

### Performance Optimization

- Use smaller embedding models for faster responses
- Implement document chunking for large files
- Add caching for frequently asked questions
- Use async processing for document uploads

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the development team
- Check the troubleshooting section above

## Acknowledgments

- Carnegie Mellon University Africa for the use case
- Google AI for the Gemini model
- LangChain community for the RAG framework
- HuggingFace for embedding models