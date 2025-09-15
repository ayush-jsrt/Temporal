# Temporal Knowledge Cards

A personal knowledge management system powered by AI that transforms your thoughts and ideas into structured, searchable knowledge cards.

## 🚀 Quick Start

### 1. Database Setup
Start the PostgreSQL database with pgvector extension:

```bash
docker run --name temporal-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_DB=temporal_db \
  -p 5432:5432 \
  ankane/pgvector
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python3 api.py
```
Backend will run on `http://localhost:5000`

### 3. Frontend Setup
```bash
cd frontend
npm install

# For React version (port 3000)
npm run dev:react

# For Vue version (port 3001)  
npm run dev:vue
```

## 🎨 Frontend Features

### Dark Theme Design
- Elegant grayscale color scheme with white highlights
- Modern, clean interface optimized for readability
- Responsive design that works on desktop and mobile

### Horizontal Carousel
- Smooth scrolling cards with snap-to-center behavior
- Focused card is highlighted in the center
- Click or scroll to navigate between cards

### Interactive Knowledge Cards
- Add new knowledge by entering text
- AI processes your input into structured cards
- Delete unwanted cards with one click
- Rich HTML formatting for detailed content

### Real-time Updates
- Automatic focus detection based on carousel position
- Smooth transitions and animations
- Instant feedback on all user actions

## 🛠 Technology Stack

### Backend
- **Flask**: Web framework
- **PostgreSQL**: Database with pgvector for embeddings
- **AI Service**: Text processing and knowledge extraction
- **SQLAlchemy**: ORM for database operations

### Frontend
- **React 18**: Modern React with hooks
- **Vue 3**: Composition API implementation  
- **Vite**: Fast build tool for both frameworks
- **Axios**: HTTP client for API communication
- **Pure CSS**: Custom properties and modern CSS features

## 📱 Browser Support
- Chrome/Edge 88+
- Firefox 87+
- Safari 14+
- Mobile browsers with CSS scroll-snap support

## 🔧 Development

### Using VS Code Tasks
Run these tasks from VS Code Command Palette (`Ctrl+Shift+P`):
- `Tasks: Run Task` → `Start Backend API`
- `Tasks: Run Task` → `Start React Frontend`
- `Tasks: Run Task` → `Start Vue Frontend`

### Using the Development Script
```bash
./start-dev.sh
```
This starts the backend automatically and provides instructions for the frontend.

## 📁 Project Structure
```
Temporal/
├── backend/           # Flask API server
│   ├── api.py        # Main API endpoints
│   ├── crud.py       # Database operations
│   ├── ai_service.py # AI text processing
│   └── cards.py      # Data models
├── frontend/         # React & Vue implementations
│   ├── react/        # React version
│   ├── vue/          # Vue version
│   └── README.md     # Frontend documentation
└── README.md         # This file
```

## 🌟 Usage

1. **Start the system**: Database → Backend → Frontend
2. **Add knowledge**: Type your thoughts in the input area
3. **Browse cards**: Use the horizontal carousel to explore
4. **View details**: Click any card to see full content
5. **Manage cards**: Delete cards you no longer need

The AI will automatically process your input, find related existing knowledge, and create new structured cards with insights and connections.
