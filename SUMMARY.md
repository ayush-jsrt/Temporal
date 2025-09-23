# Project: Temporal

This is a **microservices-based platform** for AI-powered card and note management, featuring containerized deployment and Kubernetes orchestration. Temporal is a modular, containerized platform for managing cards/notes with AI features. It uses React for the frontend, Flask-based Python services for the backend, and Kubernetes for orchestration. Each service is independently deployable and scalable, supporting modern development and operational best practices.

1. **Frontend** → User interface for card/note management
2. **Backend** → Main API server with database operations and AI integration to create cards
3. **Langgraph Backend** → Dedicated service for AI chat features

## 1. **Frontend**

**Tech Stack:**
- **Language:** JavaScript - UI logic and interactivity
- **Framework:** React - SPA structure and state management
- **Build Tool:** Vite (hot reload, fast builds, ES modules) - development and bundling
- **HTTP Client:** Axios, fetch API - API requests
- **Styling:** CSS - UI design

**Use Case:**
- Single Page Application (SPA) for card/note management
- User interface for creating, editing, and managing cards/notes
- Integrates with backend API for data operations

## 2. **Backend**

**Tech Stack:**
- **Language:** Python 3 - backend logic
- **Framework:** Flask (Blueprints, RESTful APIs, error handling) - web server
- **Database:** SQLAlchemy ORM - data storage to Postgresql+Vector
- **AI Integration:** Custom AI service (aws bedrock using boto3, titan v2 embedding, cluade 3 haiku)- card/note analysis
- **Cross-Origin:** Flask-CORS - enable frontend API access
- **Environment:** python-dotenv - config management
- **HTTP:** requests - external API calls

**Use Case:**
- RESTful API server for card/note management
- Provides CRUD operations for cards/notes
- Integrates with AI model for advanced features
- Acts as the primary data layer for the application

## 3. **Langgraph Backend**

**Tech Stack:**
- **Language:** Python 3.10+ (async, type hints) - service logic
- **Framework:** flask - API server
- **Database:** redis, SQLAlchemy ORM - persistent storage
- **AI Integration:** Langgraph, AWS Bedrock for claude 3 haiku
- **Validation:** Pydantic - data validation

**Use Case:**
- Dedicated backend for advanced AI-powered features
- Handles AI operations and database management
- Exposes API endpoints for frontend or other services