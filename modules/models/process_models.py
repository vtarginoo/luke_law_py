from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel



# Modelo para o Movimento
class Movimento(BaseModel):
    ordem: Optional[int] = None
    nome: str
    dataHora: datetime

# Modelo para o Processo capturado
class Processo(BaseModel):
    partesEnvolvidas: str
    numeroProcesso: str
    tribunal: str
    sistema: str
    grau: str  # Grau em vez de instancia, para seguir o Java
    movimentos: List[Movimento] = []  # Inicializa como lista vazia
    dataHoraUltimaAtualizacao: datetime  # Usamos datetime