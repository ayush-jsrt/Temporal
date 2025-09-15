# Temporal Knowledge Cards - Frontend

This project contains both React and Vue implementations of the Temporal Knowledge Cards frontend.

## Features

- **Dark Theme**: Elegant grayscale design with white highlights
- **Horizontal Carousel**: Snappable card carousel with focus-based navigation
- **Focused Detail View**: Selected card shows detailed content below the carousel
- **Add New Cards**: Process text input through AI to create knowledge cards
- **Delete Cards**: Remove unwanted cards with confirmation
- **Responsive Design**: Mobile-friendly layout

## UI Design

- Cards are displayed in a horizontal carousel with scroll-snap behavior
- The focused card (center-most) is highlighted and shows detailed content below
- Cards can be focused by scrolling or clicking
- The focused card's content is rendered with HTML formatting
- Dark theme with gray scales and white highlights for better readability

## Technology Stack

- **React Version**: React 18 with hooks
- **Vue Version**: Vue 3 with Composition API
- **Build Tool**: Vite for both versions
- **HTTP Client**: Axios for API communication
- **Styling**: Pure CSS with CSS custom properties

## Backend Dependencies

Make sure the backend API is running on `http://localhost:5000` with the following endpoints:
- `GET /cards` - Fetch all cards
- `POST /add-text` - Create new knowledge card
- `DELETE /cards/{id}` - Delete a specific card

## Running the Applications

### React Version
```bash
npm run dev:react
```
This will start the React app on `http://localhost:3000`

### Vue Version
```bash
npm run dev:vue
```
This will start the Vue app on `http://localhost:3001`

### General Development
```bash
# Install dependencies
npm install

# Start React development server
npm run dev:react

# Start Vue development server (in another terminal)
npm run dev:vue

# Build for production (React)
npm run build

# Preview production build
npm run preview
```

## API Configuration

The frontend is configured to connect to the backend at `http://localhost:5000`. If your backend is running on a different port, update the `API_BASE_URL` constant in:
- React: `/react/src/App.jsx`
- Vue: `/vue/src/App.vue`

## Browser Support

- Chrome/Edge 88+
- Firefox 87+
- Safari 14+
- Mobile browsers with scroll-snap support

## Development Notes

- Both implementations share the same CSS design system
- React uses functional components with hooks
- Vue uses Composition API for better TypeScript support
- Carousel focus is automatically updated based on scroll position
- HTML content from cards is safely rendered (ensure backend sanitizes input)
