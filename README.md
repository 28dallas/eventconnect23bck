# EventConnect Backend

Flask API backend for the EventConnect platform.

## Features

- User authentication (JWT)
- Professional profiles
- Service management
- Booking system
- Professional directory

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export DATABASE_URL="sqlite:///eventconnect.db"
export JWT_SECRET_KEY="your-secret-key"
export FLASK_ENV="development"
```

3. Run the application:
```bash
python run.py
```

## Deployment to Render

1. Create a new repository with these files
2. Connect to Render and create a new Web Service
3. Set the following environment variables in Render:
   - `DATABASE_URL`: PostgreSQL connection string (provided by Render)
   - `JWT_SECRET_KEY`: A strong secret key for JWT tokens
   - `FLASK_ENV`: production

## API Endpoints

- `POST /api/register` - User registration
- `POST /api/login` - User login
- `GET/POST /api/services` - Service management
- `GET /api/professionals` - Professional directory
- `POST/PUT /api/professional-profile` - Professional profile management
- `GET/POST /api/bookings` - Booking management

## Database

The application uses SQLAlchemy with PostgreSQL in production and SQLite for development.
# eventcbacknd
