# Environment Variables Setup

This project requires environment variables to be set for database credentials and API keys. For security reasons, these should not be committed to version control.

## Required Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Database credentials
POSTGRES_DB=ragdb
POSTGRES_USER=raguser
POSTGRES_PASSWORD=your_secure_password_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
```

## Security Notes

1. **Never commit the `.env` file** to version control
2. **Use strong passwords** for database credentials
3. **Keep API keys secure** and rotate them regularly
4. **The `.env` file is already in `.gitignore`** to prevent accidental commits

## Getting Started

1. Copy the example above and create your `.env` file
2. Replace the placeholder values with your actual credentials
3. Run `docker-compose up --build` to start the services

## Environment Variables Explained

- `POSTGRES_DB`: Database name (default: ragdb)
- `POSTGRES_USER`: Database username (default: raguser)
- `POSTGRES_PASSWORD`: Database password (use a strong password)
- `OPENAI_API_KEY`: Your OpenAI API key for LLM integration 


## Quick getting started:

After run the docker services (API and DB). We need to apply the Scrapping/Chunking/Insertion of both sites. 

For this use the API docs interface in localhost:8000/docs.

Use the endpoint /ingest 2 times:
- First time with JSON input: {
  "site": "think_python"
}


Wait for the process that should ingest 301 chunks and then, use it a second time with JSON input: {
  "site": "pep8"
}

that should ingest 28 chunks more.

After this, the DB should have 329 rows. You can check this using the another endpoint /count

Finally, you are ready to test the endpoint /query.
Please give instructions in English because documents are in English and the embeddings model transformer I used apply only with english too.

Best! :)
