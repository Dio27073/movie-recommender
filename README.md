# Movie Recommendation System

A personalized movie recommendation platform that suggests films based on user preferences, viewing history, and behavior patterns. The system provides accurate, relevant recommendations while maintaining high performance and scalability.

## Features

- **Personalized Recommendations**: Uses a hybrid recommendation system combining content-based and collaborative filtering
- **Comprehensive Movie Database**: Detailed movie metadata including cast, crew, genres, and technical details
- **Rating and Review System**: User ratings, written reviews, and community feedback
- **High Performance**: Fast API response times and support for large-scale concurrent usage
- **Mobile Responsive**: Seamless experience across desktop and mobile devices

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- PostgreSQL 15+ with PostGIS
- Redis for caching
- JWT for authentication

### Frontend
- React 18+
- Redux Toolkit
- Material-UI/Tailwind CSS

### Key Libraries
- scikit-learn
- pandas
- surprise
- psycopg2

## Getting Started

### Prerequisites

```bash
# Install Python 3.11+
python --version

# Install PostgreSQL 15+
psql --version

# Install Redis
redis-cli --version

# Install Node.js and npm
node --version
npm --version
```

### Installation

1. Clone the repository
```bash
git clone https://github.com/your-username/movie-recommendation-system.git
cd movie-recommendation-system
```

2. Set up the backend
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head
```

3. Set up the frontend
```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with your configuration
```

### Running the Application

1. Start the backend server
```bash
# From the root directory
uvicorn app.main:app --reload
```

2. Start the frontend development server
```bash
# From the frontend directory
npm run dev
```

The application will be available at `http://localhost:3000`

## Development

### Project Structure
```
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   └── services/
│   ├── tests/
│   └── alembic/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── store/
│   └── public/
└── docs/
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

- IMDB for movie dataset
- MovieLens for recommendation training data
- TMDB for supplementary movie information
