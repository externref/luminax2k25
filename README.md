# Surge - Real-Time Environmental Monitoring System

A comprehensive environmental monitoring platform for Bangalore that tracks air quality index (AQI) and water quality index (WQI) with real-time data visualization, interactive maps, and AI-powered predictions.

## Overview

Surge provides real-time monitoring and predictive analytics for environmental health metrics across 20 localities in Bangalore. The system features interactive heatmaps, historical trend analysis, and Prophet-based forecasting with uncertainty quantification.

## Technology Stack

### Frontend
- **SvelteKit 2.48.5** - Full-stack framework with SSR/SPA capabilities
- **Svelte 5** - Reactive UI framework with runes-based state management
- **TypeScript** - Type-safe development
- **Tailwind CSS 4.1.17** - Utility-first CSS framework
- **Leaflet 1.9.4** - Interactive mapping library
- **leaflet.heat 0.2.0** - Heatmap visualization plugin

### Backend
- **Supabase PostgreSQL** - Real-time database with JSONB support
- **Server-Sent Events (SSE)** - Real-time data streaming
- **SvelteKit API Routes** - Serverless API endpoints

### Data & Analytics
- **Prophet-like Algorithm** - Time-series forecasting with trend analysis and seasonality
- **WAQI API** - World Air Quality Index data source
- **Python 3.x** - Data generation and processing scripts
- **httpx** - HTTP client for API requests

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Browser                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Home Page   │  │  Air Quality │  │ Water Quality│     │
│  │   (/)        │  │   (/air)     │  │   (/water)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│               SvelteKit Application Server                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 API Routes                            │  │
│  │  /api/historical      - Historical data fetch        │  │
│  │  /api/predict-aqi     - AQI predictions              │  │
│  │  /api/predict-water   - WQI predictions              │  │
│  │  /api/live-updates    - SSE for AQI updates          │  │
│  │  /api/water-updates   - SSE for WQI updates          │  │
│  │  /api/report          - Data ingestion endpoint      │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Database Functions (database.ts)          │  │
│  │  - addAQIRecord()                                    │  │
│  │  - addWaterRecord()                                  │  │
│  │  - getHistoricalDataByLocality()                     │  │
│  │  - subscribeToUpdates()                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          │                                          │
          ▼                                          ▼
┌──────────────────────┐              ┌──────────────────────┐
│  Supabase PostgreSQL │              │   External APIs      │
│                      │              │                      │
│  Tables:             │              │  - WAQI API          │
│  - aqi_records       │              │  (demo token)        │
│  - water_records     │              │                      │
└──────────────────────┘              └──────────────────────┘
          ▲
          │
┌─────────┴────────────────────────────────────────────────────┐
│              Data Generation Scripts (Python)                │
│  - generate_aqi_historical.py                                │
│  - generate_water_historical.py                              │
└──────────────────────────────────────────────────────────────┘
```

### Component Architecture

**Frontend Components:**
- Interactive Leaflet maps with zoom-based layer switching (heatmap/markers)
- SVG-based chart visualization with historical and predicted data
- Real-time SSE event listeners for live updates
- Modal dialogs for detailed locality analysis
- Responsive sidebar for unhealthy/poor quality areas

**State Management:**
- Svelte 5 runes ($state, $derived, $effect, $props)
- Reactive data binding for real-time updates
- Derived computations for filtered datasets

## Database Schema

### aqi_records Table

```sql
CREATE TABLE aqi_records (
    id SERIAL PRIMARY KEY,
    locality VARCHAR(255) NOT NULL,
    value INTEGER NOT NULL,
    coords JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    extra JSONB
);

CREATE INDEX idx_aqi_locality ON aqi_records(locality);
CREATE INDEX idx_aqi_timestamp ON aqi_records(timestamp);
CREATE INDEX idx_aqi_created_at ON aqi_records(created_at);
```

**JSONB Fields:**
- `coords`: `{ latitude: number, longitude: number }`
- `extra`: `{ pm25: number, pm10: number, no2: number, so2: number, co: number, o3: number }`

### water_records Table

```sql
CREATE TABLE water_records (
    id SERIAL PRIMARY KEY,
    locality VARCHAR(255) NOT NULL,
    value INTEGER NOT NULL,
    coords JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    extra JSONB
);

CREATE INDEX idx_water_locality ON water_records(locality);
CREATE INDEX idx_water_timestamp ON water_records(timestamp);
CREATE INDEX idx_water_created_at ON water_records(created_at);
```

**JSONB Fields:**
- `coords`: `{ latitude: number, longitude: number }`
- `extra`: `{ pH: number, tds: number, turbidity: number, status: string }`

## Algorithms

### Prophet-like Time-Series Forecasting

The prediction system implements a simplified Prophet algorithm for forecasting environmental metrics.

**Algorithm Components:**

1. **Trend Analysis**
```typescript
const trend = (lastValue - firstValue) / dataLength
const recentMean = mean(last10Values)
const trendComponent = trend * 0.6 + recentMean * 0.4
```

2. **Seasonal Factor**
```typescript
const hourOfDay = timestamp.getHours()
const seasonalFactor = 1 + amplitude * Math.sin((hourOfDay / 24) * 2 * Math.PI)
// AQI: amplitude = 0.1
// WQI: amplitude = 0.05
```

3. **Prediction Calculation**
```typescript
predictedValue = baseValue * trendComponent * seasonalFactor + noise
lowerBound = predictedValue * (1 - uncertainty)
upperBound = predictedValue * (1 + uncertainty)
```

4. **Confidence Scoring**
```typescript
confidence = Math.max(0.5, 1 - (hoursAhead / 168))
// Decreases with prediction horizon, minimum 50%
```

**Prediction Intervals:** 24 hours, 48 hours

**Output Format:**
```typescript
{
  timestamp: string,
  hours_ahead: number,
  predicted_value: number,
  lower_bound: number,
  upper_bound: number,
  confidence: number
}
```

### AQI Color Mapping (12-Level Granularity)

Enhanced color scale for high-pollution differentiation:

```typescript
const aqiColorScale = {
  0-50:    '#00e400',  // Good
  51-75:   '#7acc16',  // Satisfactory
  76-100:  '#ffff00',  // Moderate
  101-125: '#ffcc00',  // Moderate to Poor
  126-150: '#ff9900',  // Poor
  151-175: '#ff6600',  // Poor to Very Poor
  176-200: '#ff3300',  // Very Poor
  201-225: '#ff0000',  // Very Poor to Severe
  226-250: '#cc0000',  // Severe
  251-275: '#990033',  // Severe+
  276-300: '#660066',  // Severe++
  300+:    '#4d004d'   // Hazardous
}
```

### WQI Color Mapping (6-Level Scale)

Inverted scale where higher values indicate better quality:

```typescript
const wqiColorScale = {
  0-10:   '#7f1d1d',  // Very Poor
  11-30:  '#dc2626',  // Poor
  31-50:  '#f59e0b',  // Fair
  51-70:  '#fbbf24',  // Moderate
  71-90:  '#a3e635',  // Good
  90-100: '#22c55e'   // Excellent
}
```

### Heatmap Normalization

```typescript
const normalized = (value - minValue) / (maxValue - minValue)
// Maps values to 0-1 range for gradient application
```

## Data Generation

### AQI Historical Data Generator

**Features:**
- Fetches real-time baseline from WAQI API
- Generates 48 hours of hourly data (49 time points)
- Applies traffic pattern variations (6-10 AM, 5-9 PM: 1.15x multiplier)
- Includes all pollutant parameters (PM2.5, PM10, NO2, SO2, CO, O3)
- Covers 20 Bangalore localities

**Traffic Patterns:**
```python
if 6 <= hour <= 10 or 17 <= hour <= 21:
    traffic_factor = 1.15
else:
    traffic_factor = 1.0
```

### Water Quality Data Generator

**Features:**
- Baseline WQI: 55-85 range
- pH: 6.8-8.2
- TDS: 180-350 ppm
- Turbidity: 0.5-4.0 NTU
- Usage-based variations (morning/evening peaks)
- Status categorization (Excellent/Good/Fair/Poor/Very Poor)

## Monitoring Localities

System covers 20 locations across Bangalore:

- Koramangala
- Indiranagar
- Whitefield
- Electronic City
- Jayanagar
- Malleshwaram
- HSR Layout
- BTM Layout
- Marathahalli
- Bellandur
- Sarjapur Road
- Hebbal
- Yeshwanthpur
- JP Nagar
- Banashankari
- Rajajinagar
- Yelahanka
- Bannerghatta Road
- MG Road
- Brigade Road

## Features

### Real-Time Monitoring
- Live data updates via Server-Sent Events
- Interactive Leaflet maps with heatmap overlay
- Zoom-based layer switching (heatmap < 14, markers >= 14)
- 18px markers with permanent locality labels

### Historical Analysis
- 48-hour historical trend charts
- SVG-based visualization (800x320px)
- Separate historical and prediction sections in charts
- Color-coded data points matching quality levels

### Predictive Analytics
- AI-powered 24h and 48h forecasts
- Uncertainty bands visualization
- Confidence intervals display
- "Now" separator line in charts

### Interactive Features
- Click markers to view detailed locality data
- Unhealthy/Poor quality areas sidebar
- Modal dialogs with comprehensive trend analysis
- Responsive design for mobile and desktop

### Chart Visualization
- Historical data: Blue solid line
- Predictions: Orange dashed line
- Uncertainty bands: Yellow shaded area
- Legend and axis labels
- Max values: AQI=200, WQI=100

## API Endpoints

### GET /api/historical
Fetch historical data for a locality.

**Query Parameters:**
- `locality`: string (required)
- `limit`: number (default: 20)

**Response:**
```json
{
  "data": [
    {
      "value": number,
      "created_at": string,
      "extra": object
    }
  ]
}
```

### GET /api/predict-aqi
Generate AQI predictions for a locality.

**Query Parameters:**
- `locality`: string (required)

**Response:**
```json
{
  "predictions": [
    {
      "timestamp": string,
      "hours_ahead": number,
      "predicted_value": number,
      "lower_bound": number,
      "upper_bound": number,
      "confidence": number
    }
  ]
}
```

### GET /api/predict-water
Generate WQI predictions for a locality.

**Query Parameters:**
- `locality`: string (required)

**Response:** Same structure as predict-aqi

### GET /api/live-updates
Server-Sent Events stream for real-time AQI updates.

**Event Format:**
```json
{
  "locality": string,
  "value": number,
  "coords": { "latitude": number, "longitude": number },
  "timestamp": string,
  "extra": object
}
```

### POST /api/report
Ingest new environmental data records.

**Request Body:**
```json
{
  "type": "aqi" | "water",
  "locality": string,
  "value": number,
  "coords": { "latitude": number, "longitude": number },
  "extra": object
}
```

## Environment Variables

Required environment variables (prefix: `SURGE_`):

```env
SURGE_SUPABASE_URL=your_supabase_project_url
SURGE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Installation & Setup

### Prerequisites
- Node.js 18+ 
- Python 3.8+
- Supabase account

### Installation Steps

1. Clone the repository
```bash
git clone https://github.com/externref/luminax2k25.git
cd luminax2k25
```

2. Install dependencies
```bash
npm install
```

3. Configure environment variables
Create `.env` file with Supabase credentials

4. Set up database
Execute SQL schemas for `aqi_records` and `water_records` tables

5. Generate historical data
```bash
python server_replicators/generate_aqi_historical.py
python server_replicators/generate_water_historical.py
```

6. Start development server
```bash
npm run dev
```

## Project Structure

```
luminax2k25/
├── src/
│   ├── lib/
│   │   ├── server/
│   │   │   └── database.ts          # Supabase client & DB functions
│   │   ├── $types.d.ts               # TypeScript type definitions
│   │   ├── localitites.ts            # Locality coordinates data
│   │   └── assets/                   # Static assets
│   ├── routes/
│   │   ├── +layout.svelte            # Global layout with header
│   │   ├── +page.svelte              # Home page
│   │   ├── air/
│   │   │   ├── +page.svelte          # Air quality monitoring
│   │   │   └── +page.server.ts       # SSR data loading
│   │   ├── water/
│   │   │   ├── +page.svelte          # Water quality monitoring
│   │   │   └── +page.server.ts       # SSR data loading
│   │   └── api/
│   │       ├── historical/+server.ts      # Historical data endpoint
│   │       ├── predict-aqi/+server.ts     # AQI prediction endpoint
│   │       ├── predict-water/+server.ts   # WQI prediction endpoint
│   │       ├── live-updates/+server.ts    # AQI SSE stream
│   │       ├── water-updates/+server.ts   # WQI SSE stream
│   │       └── report/+server.ts          # Data ingestion endpoint
│   ├── app.d.ts                      # App type definitions
│   └── app.html                      # HTML template
├── server_replicators/
│   ├── generate_aqi_historical.py    # AQI data generator
│   └── generate_water_historical.py  # WQI data generator
├── static/                           # Static assets
├── package.json                      # Dependencies
├── svelte.config.js                  # SvelteKit configuration
├── tailwind.config.js                # Tailwind CSS configuration
├── tsconfig.json                     # TypeScript configuration
└── vite.config.ts                    # Vite configuration
```

## Performance Optimizations

- Server-side rendering for initial page load
- Lazy loading of Leaflet libraries
- Debounced real-time updates
- Efficient JSONB queries with indexes
- Derived state computations
- SVG-based charts for lightweight rendering

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

Copyright 2025 Surge. All rights reserved.

## Contributors

Built for environmental monitoring and smart city initiatives.
