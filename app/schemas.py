from pydantic import BaseModel, ConfigDict


class Macronutrients(BaseModel):
    model_config = ConfigDict(extra="allow")

    protein_g: float
    fat_g: float
    carbs_g: float
    water_g: float


class Micronutrients(BaseModel):
    vitamins: dict[str, float] = {}
    minerals: dict[str, float] = {}


class Ingredient(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    weight_g: float
    calories_kcal: float
    allergens: list[str] = []
    macronutrients: Macronutrients
    micronutrients: Micronutrients


class Total(BaseModel):
    model_config = ConfigDict(extra="allow")

    calories_kcal: float
    allergens: list[str] = []
    macronutrients: Macronutrients
    micronutrients: Micronutrients


class DishAnalysis(BaseModel):
    dish_name: str
    ingredients: list[Ingredient]
    total: Total


class AnalyzeResponse(BaseModel):
    data: DishAnalysis | dict | None = None
    error: str | None = None
