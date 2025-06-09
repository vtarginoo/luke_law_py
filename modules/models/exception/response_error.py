from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class ResponseError(BaseModel):
    """
    DTO para padronizar as respostas de erro da API.
    A mensagem é obrigatória, enquanto o código, detalhes e timestamp são opcionais
    ou preenchidos automaticamente.
    """
    message: str = Field(...,
                         description="Mensagem descritiva do erro.")
    code: Optional[str] = Field(None,
                                description="Código de erro específico da aplicação (ex: 'VALIDATION_ERROR', 'INTERNAL_SERVER_ERROR').")
    details: Optional[Any] = Field(None,
                                   description="Detalhes adicionais sobre o erro para depuração. Não deve ser exposto em produção para erros internos.")
    timestamp: datetime = Field(default_factory=datetime.now,
                                description="Data e hora em que o erro ocorreu no formato ISO 8601.")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
