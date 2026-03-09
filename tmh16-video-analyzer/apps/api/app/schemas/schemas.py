from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class ProjectCreate(BaseModel):
    name: str
    site_name: str
    site_type: str
    location: str
    survey_date: str
    survey_period: str
    notes: str | None = None


class ProjectOut(ProjectCreate):
    id: int

    class Config:
        from_attributes = True


class SceneDefinitionInput(BaseModel):
    config: dict


class ManualCorrectionInput(BaseModel):
    edit_type: str
    payload: dict


class AnalysisRunRequest(BaseModel):
    frame_skip: int = 3
    confidence_threshold: float = 0.4
