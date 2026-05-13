from pydantic import BaseModel, ConfigDict

class Annonce(BaseModel):
    """
    Modèle de données pour une annonce immobilière,
    avec validation et typage strict.
    """
    id: int
    title: str
    url: str
    city: str
    zip_code: str
    surface: float
    price: float
    price_square_meter: float
    score: int

