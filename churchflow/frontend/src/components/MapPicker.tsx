import { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents, useMap } from 'react-leaflet'
import L from 'leaflet'
import { getApiUrl } from '../config'
import 'leaflet/dist/leaflet.css'

// Fix for default marker icon in react-leaflet
// Reason: Webpack doesn't automatically include Leaflet's default marker images
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

interface MapPickerProps {
  latitude: number | null
  longitude: number | null
  onLocationSelect: (lat: number, lng: number) => void
  height?: string
}

/**
 * Geocoding result interface matching backend response.
 */
interface GeocodingResult {
  label: string
  x: number  // longitude
  y: number  // latitude
  bounds?: [[number, number], [number, number]]
  raw: any
}

/**
 * Custom search component for location search.
 * Uses backend geocoding proxy to bypass CORS restrictions.
 */
function SearchField({ onLocationSelect }: { onLocationSelect: (lat: number, lng: number) => void }) {
  const map = useMap()
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<GeocodingResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const searchTimeoutRef = useRef<NodeJS.Timeout>()

  // Search function using backend proxy
  const handleSearch = async (query: string) => {
    if (query.length < 3) {
      setSearchResults([])
      setShowResults(false)
      return
    }

    setIsSearching(true)
    try {
      // Call backend geocoding proxy instead of Nominatim directly
      const url = getApiUrl(`geocoding/search?q=${encodeURIComponent(query)}&countrycodes=gh&limit=5`)
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(`Geocoding failed: ${response.status}`)
      }

      const data = await response.json()
      setSearchResults(data.results || [])
      setShowResults(data.results && data.results.length > 0)
    } catch (error) {
      console.error('Search error:', error)
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  // Debounced search
  const onSearchChange = (value: string) => {
    setSearchQuery(value)

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    searchTimeoutRef.current = setTimeout(() => {
      handleSearch(value)
    }, 300)
  }

  // Handle result selection
  const selectResult = (result: GeocodingResult) => {
    onLocationSelect(result.y, result.x)
    map.setView([result.y, result.x], 15)
    setSearchQuery(result.label)
    setShowResults(false)
  }

  return (
    <div className="leaflet-top leaflet-left" style={{ marginTop: '10px', marginLeft: '10px', zIndex: 1000 }}>
      <div className="leaflet-control" style={{ position: 'relative' }}>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          onFocus={() => searchResults.length > 0 && setShowResults(true)}
          placeholder="Search for venue location..."
          className="px-4 py-2 border-2 border-purple-500 rounded-lg shadow-lg text-sm font-medium focus:ring-2 focus:ring-purple-500 focus:outline-none"
          style={{ width: '280px' }}
        />

        {isSearching && (
          <div className="absolute right-3 top-3 text-purple-600">
            <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        )}

        {showResults && searchResults.length > 0 && (
          <div
            className="absolute top-full left-0 right-0 mt-1 bg-white border-2 border-purple-200 rounded-lg shadow-xl max-h-64 overflow-y-auto z-[10001]"
            style={{ width: '280px' }}
          >
            {searchResults.map((result, index) => (
              <div
                key={index}
                onClick={() => selectResult(result)}
                className="px-4 py-2 text-sm text-gray-700 hover:bg-purple-50 cursor-pointer border-b border-gray-100 last:border-b-0"
              >
                {result.label}
              </div>
            ))}
          </div>
        )}

        {showResults && searchResults.length === 0 && searchQuery.length >= 3 && !isSearching && (
          <div
            className="absolute top-full left-0 right-0 mt-1 bg-white border-2 border-purple-200 rounded-lg shadow-xl px-4 py-3 text-sm text-gray-500 italic"
            style={{ width: '280px' }}
          >
            No results found. Try another search or click on the map.
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Interactive map component for selecting venue GPS coordinates.
 *
 * Features:
 * - Search for locations by name (OpenStreetMap)
 * - Click on map to set venue location
 * - Draggable marker for fine-tuning
 * - Default center on Accra, Ghana
 *
 * @param latitude - Current latitude value
 * @param longitude - Current longitude value
 * @param onLocationSelect - Callback when location is selected
 * @param height - Map container height (default: 300px)
 */
function LocationMarker({ position, onLocationSelect }: { position: [number, number] | null, onLocationSelect: (lat: number, lng: number) => void }) {
  const markerRef = useRef<L.Marker>(null)

  useMapEvents({
    click(e) {
      onLocationSelect(e.latlng.lat, e.latlng.lng)
    },
  })

  if (!position) return null

  return (
    <Marker
      position={position}
      draggable={true}
      eventHandlers={{
        dragend: () => {
          const marker = markerRef.current
          if (marker) {
            const newPos = marker.getLatLng()
            onLocationSelect(newPos.lat, newPos.lng)
          }
        },
      }}
      ref={markerRef}
    >
      <Popup>
        <div className="text-sm">
          <strong>Venue Location</strong><br />
          Lat: {position[0].toFixed(6)}<br />
          Lng: {position[1].toFixed(6)}<br />
          <span className="text-gray-600 text-xs">Drag to adjust</span>
        </div>
      </Popup>
    </Marker>
  )
}

export default function MapPicker({ latitude, longitude, onLocationSelect, height = '300px' }: MapPickerProps) {
  // Default to Accra, Ghana if no coordinates provided
  const defaultCenter: [number, number] = [5.6037, -0.1870]
  const center: [number, number] = (latitude && longitude) ? [latitude, longitude] : defaultCenter
  const markerPosition: [number, number] | null = (latitude && longitude) ? [latitude, longitude] : null

  return (
    <div className="relative" style={{ height }}>
      <MapContainer
        center={center}
        zoom={13}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%', borderRadius: '0.5rem' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <SearchField onLocationSelect={onLocationSelect} />
        <LocationMarker position={markerPosition} onLocationSelect={onLocationSelect} />
      </MapContainer>

      <div className="absolute top-2 right-2 bg-white rounded-lg shadow-md px-3 py-2 text-xs text-gray-600 z-[1000] pointer-events-none">
        {markerPosition ? (
          <div>
            <strong>Selected:</strong><br />
            {markerPosition[0].toFixed(6)}, {markerPosition[1].toFixed(6)}
          </div>
        ) : (
          <div>Search or click map</div>
        )}
      </div>
    </div>
  )
}
