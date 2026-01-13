from fastapi import APIRouter

from .schemas import Country, CountryListResponse

router = APIRouter()

# Targeting West Africa Countries for MVP
SUPPORTED_COUNTRIES = [
    Country(code="LR", name="Liberia"),
    Country(code="SL", name="Sierra Leone"),
    Country(code="GN", name="Guinea"),
    Country(code="GH", name="Ghana"),
    Country(code="CI", name="Côte d'Ivoire"),
    Country(code="NG", name="Nigeria"),
    Country(code="SN", name="Senegal"),
    Country(code="GM", name="Gambia"),
]


@router.get("/countries", response_model=CountryListResponse)
async def list_countries() -> CountryListResponse:
    "Get list of supported countries for registration"
    return CountryListResponse(countries=SUPPORTED_COUNTRIES)
