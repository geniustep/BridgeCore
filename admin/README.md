# BridgeCore Admin Dashboard

React-based admin dashboard for managing BridgeCore multi-tenant system.

## Features

- ✅ Admin authentication with JWT
- ✅ Tenant management (CRUD operations)
- ✅ Real-time analytics and statistics
- ✅ Usage and error logs viewer
- ✅ Responsive design with Ant Design
- ✅ TypeScript for type safety
- ✅ State management with Zustand

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Ant Design 5** - UI components
- **Zustand** - State management
- **React Router 6** - Routing
- **Axios** - HTTP client
- **Recharts** - Charts and graphs

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- BridgeCore API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

The dashboard will be available at: http://localhost:3000

### Default Credentials

```
Email: admin@bridgecore.local
Password: admin123
```

⚠️ **Change these credentials in production!**

## Development

```bash
# Development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Project Structure

```
admin/
├── src/
│   ├── components/      # Reusable components
│   │   ├── Layout/      # Layout components (Sidebar, Header, MainLayout)
│   │   ├── Charts/      # Chart components
│   │   ├── Common/      # Common components
│   │   ├── Tenants/     # Tenant-specific components
│   │   ├── Analytics/   # Analytics components
│   │   └── Logs/        # Log components
│   ├── pages/           # Page components
│   │   ├── Auth/        # Login page
│   │   ├── Dashboard/   # Dashboard page
│   │   ├── Tenants/     # Tenant pages
│   │   ├── Analytics/   # Analytics pages
│   │   └── Logs/        # Log pages
│   ├── services/        # API services
│   │   ├── api.ts       # Axios client
│   │   ├── auth.service.ts
│   │   ├── tenant.service.ts
│   │   ├── analytics.service.ts
│   │   └── logs.service.ts
│   ├── store/           # Zustand stores
│   │   ├── auth.store.ts
│   │   └── tenant.store.ts
│   ├── types/           # TypeScript types
│   ├── utils/           # Utility functions
│   ├── config/          # Configuration
│   ├── App.tsx          # Main app component
│   └── main.tsx         # Entry point
├── public/              # Static assets
├── index.html           # HTML template
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
├── vite.config.ts       # Vite config
└── README.md            # This file
```

## Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=BridgeCore Admin
```

## Available Pages

- **Dashboard** (`/`) - System overview with statistics
- **Tenants** (`/tenants`) - Manage tenants (list, create, edit, delete)
- **Analytics** (`/analytics`) - System-wide and tenant analytics
- **Logs** (`/logs`) - Usage and error logs viewer

## API Integration

The dashboard connects to the BridgeCore API:

- **Auth Endpoints:** `/admin/auth/*`
- **Tenant Endpoints:** `/admin/tenants/*`
- **Analytics Endpoints:** `/admin/analytics/*`
- **Logs Endpoints:** `/admin/logs/*`

All requests include JWT token in `Authorization` header.

## Building for Production

```bash
# Build optimized production bundle
npm run build

# Output will be in dist/ directory
```

Deploy the `dist/` directory to your web server or CDN.

## Docker Deployment

The admin dashboard is included in the Docker Compose setup:

```bash
# Start all services including admin dashboard
docker-compose up -d
```

Dashboard will be available at: http://localhost:3000

## Troubleshooting

### API Connection Issues

- Ensure BridgeCore API is running on http://localhost:8000
- Check CORS settings in API configuration
- Verify network connectivity

### Build Issues

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### TypeScript Errors

```bash
# Run type check
npx tsc --noEmit
```

## Contributing

1. Follow the existing code structure
2. Use TypeScript for all new files
3. Follow Ant Design patterns
4. Test all features before committing

## License

This project is part of BridgeCore and follows the same license.
