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
  type_bien: "",
  score_min: "",
  source_site: "",
  enrichment_status: "",
  zonage: "",
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
  { value: "Leboncoin", label: "Leboncoin" },
  { value: "LogicImmo", label: "LogicImmo" },
  { value: "PAP", label: "PAP" },
  { value: "SeLoger", label: "SeLoger" },
];
