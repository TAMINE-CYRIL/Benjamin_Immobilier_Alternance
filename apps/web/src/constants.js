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
  sort: "score",
  direction: "desc",
};

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
