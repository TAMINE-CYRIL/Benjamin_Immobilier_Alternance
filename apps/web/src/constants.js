// Valeurs initiales pour les filtres de recherche d'annonces immobilières.
export const emptyFilters = {
  query: "",
  city: "",
  zip_code: "",
  department: "",
  price_min: "",
  price_max: "",
  surface_min: "",
  surface_max: "",
  rooms_min: "",
  rooms_max: "",
  price_m2_min: "",
  price_m2_max: "",
  type_bien: "",
  score_min: "",
  score_max: "",
  energy_class: "",
  source_site: "",
  enrichment_status: "",
  zonage: "",
  parcel_surface_min: "",
  parcel_surface_max: "",
  has_parcel: "",
  recent_days: "",
  center_lat: "",
  center_lon: "",
  radius_km: "",
  sort: "score",
  direction: "desc",
};

// Options pour les types de biens immobiliers.
export const propertyTypeOptions = [
  { value: "", label: "Tous types" },
  { value: "Appartement", label: "Appartement" },
  { value: "Maison", label: "Maison" },
  { value: "Villa", label: "Villa" },
  { value: "Terrain", label: "Terrain" },
  { value: "Local", label: "Local / commerce" },
  { value: "Immeuble", label: "Immeuble" },
  { value: "Duplex", label: "Duplex" },
  { value: "Studio", label: "Studio" },
  { value: "Autres", label: "Autres" },
];

// Options pour les sources des annonces immobilières.
export const sourceOptions = [
  { value: "", label: "Toutes sources" },
  { value: "AvoVentes", label: "AvoVentes" },
  { value: "BienIci", label: "BienIci" },
  { value: "Espaces Atypiques", label: "Espaces Atypiques" },
  { value: "LogicImmo", label: "LogicImmo" },
  { value: "PAP", label: "PAP" },
  { value: "SeLoger", label: "SeLoger" },
];

export const enrichmentStatusOptions = [
  { value: "", label: "Tous enrichissements" },
  { value: "success", label: "Enrichi" },
  { value: "partial_success", label: "Partiellement enrichi" },
  { value: "not_found", label: "Introuvable" },
  { value: "failed", label: "Erreur" },
  { value: "pending", label: "En attente" },
];

export const enrichmentStatusLabels = Object.fromEntries(
  enrichmentStatusOptions
    .filter((option) => option.value)
    .map((option) => [option.value, option.label]),
);
