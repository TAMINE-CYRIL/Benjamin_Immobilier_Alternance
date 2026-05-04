import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import { DetailPanel } from "./DetailPanel";

export default function AnnoncesMap({ annonces }) {
  const annoncesAvecCoords = annonces.filter(
    (a) => a.enrichment?.latitude && a.enrichment?.longitude
  );

  return (
    <>
    <h1>Annonces sur la carte</h1>
    {annoncesAvecCoords.length === 0 ? (
        <div className="no-data">
          <p>Aucune annonce avec coordonnées disponibles pour l'affichage sur la carte.</p>
        </div>
      ):    
      <section>
      <h2>{annoncesAvecCoords.length} annonce(s) géolocalisées</h2>
      <MapContainer
        center={[43.2965, 5.3698]}
        zoom={10}
        style={{ height: "420px", width: "100%" }}

    >
      
      {annoncesAvecCoords.map((annonce, key) => (
        <Marker position={[annonce.enrichment.latitude, annonce.enrichment.longitude]} key={key}>
          <Popup>
            <div>
              <DetailPanel annonce={annonce} loading={false} onClose={() => {}} />
            </div>
          </Popup>
        </Marker>
      ))}
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
    </MapContainer>
    </section>
    }

    </>
  );
}
