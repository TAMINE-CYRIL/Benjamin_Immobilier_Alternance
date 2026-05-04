import { useEffect } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import { formatMoney } from "../utils";


function hasValidCoords(annonce) {
  const rawLatitude = annonce.enrichment?.latitude;
  const rawLongitude = annonce.enrichment?.longitude;
  if (rawLatitude === null || rawLatitude === undefined || rawLatitude === "") return false;
  if (rawLongitude === null || rawLongitude === undefined || rawLongitude === "") return false;

  const latitude = Number(rawLatitude);
  const longitude = Number(rawLongitude);
  return Number.isFinite(latitude) && Number.isFinite(longitude);
}

function MapViewport({ annonces, selectedId }) {
  const map = useMap();

  useEffect(() => {
    const selected = annonces.find((annonce) => annonce.id === selectedId);
    if (selected) {
      map.flyTo([Number(selected.enrichment.latitude), Number(selected.enrichment.longitude)], 14, {
        duration: 1,
      });
      return;
    }

    if (annonces.length > 1) {
      const bounds = L.latLngBounds(
        annonces.map((annonce) => [
          Number(annonce.enrichment.latitude),
          Number(annonce.enrichment.longitude),
        ])
      );
      map.fitBounds(bounds, { padding: [34, 34], maxZoom: 13 });
    } else if (annonces.length === 1) {
      map.setView(
        [Number(annonces[0].enrichment.latitude), Number(annonces[0].enrichment.longitude)],
        13
      );
    }
  }, [annonces, selectedId, map]);

  return null;
}

export default function AnnoncesMap({ annonces, selectedId, onSelect }) {
  const annoncesAvecCoords = annonces.filter(hasValidCoords);

  return (
    <section className="map-panel">
      <div className="map-head">
        <div>
          <p className="eyebrow">Carte</p>
          <h2>Recherche geographique</h2>
        </div>
        <span className="map-count">
          {annoncesAvecCoords.length} localisee(s) / {annonces.length}
        </span>
      </div>

      <MapContainer center={[43.303, 5.512]} zoom={10} className="annonces-map">
        <MapViewport annonces={annoncesAvecCoords} selectedId={selectedId} />
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {annoncesAvecCoords.map((annonce) => (
          <Marker
            key={annonce.id}
            position={[Number(annonce.enrichment.latitude), Number(annonce.enrichment.longitude)]}
            eventHandlers={{ click: () => onSelect(annonce.id) }}
          >
            <Popup>
              <div className="map-popup">
                <strong>{annonce.title || "Annonce sans titre"}</strong>
                <span>{[annonce.city, annonce.zip_code].filter(Boolean).join(" ") || "Localisation inconnue"}</span>
                <span>{formatMoney(annonce.price)}</span>
                <button type="button" onClick={() => onSelect(annonce.id)}>
                  Voir le detail
                </button>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {!annoncesAvecCoords.length ? (
        <div className="map-empty">Aucune annonce de cette page ne dispose de coordonnees exploitables.</div>
      ) : null}
    </section>
  );
}
