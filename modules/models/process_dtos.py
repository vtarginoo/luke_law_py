import re
from datetime import datetime
from typing import Optional, List

from pydantic import field_validator, BaseModel, Field

from modules.models.exception.validations_exceptions import InvalidProcessNumberException


class ProcessNumberValidator:
    FORMAT_WITH_DASHES = r"^\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}$"
    FORMAT_WITHOUT_DASHES = r"^\d{20}$"

    @staticmethod
    def is_valid(value: str) -> bool:
        """
        Verifica se o número do processo está em um dos formatos válidos.
        """
        if not value:
            return False
        return bool(re.match(ProcessNumberValidator.FORMAT_WITH_DASHES, value) or \
                    re.match(ProcessNumberValidator.FORMAT_WITHOUT_DASHES, value))

    @staticmethod
    def format_process_number(num_processo: str) -> str:
        """
        Formata o número do processo para o padrão com traços e pontos,
        se estiver no formato de 20 dígitos. Retorna como está caso contrário.
        """
        if re.match(ProcessNumberValidator.FORMAT_WITHOUT_DASHES, num_processo):
            return re.sub(
                r"^(\d{7})(\d{2})(\d{4})(\d{1})(\d{2})(\d{4})$",
                r"\1-\2.\3.\4.\5.\6",
                num_processo
            )
        return num_processo # Retorna como está se já estiver no formato correto


class WSRequest(BaseModel):
    numProcesso: str = Field(..., description="Número do processo a ser raspado.")

    @field_validator('numProcesso', mode='before')  # `mode=before` para formatar antes da validação
    def validate_and_format_process_number(cls, v):
        # Primeiro, formata o número do processo, replicando seu `getNumProcesso` Java
        formatted_v = ProcessNumberValidator.format_process_number(v)

        # Depois, valida o número formatado
        if not ProcessNumberValidator.is_valid(formatted_v):
            raise InvalidProcessNumberException(num_processo=v)
        return formatted_v

class WppRequest(BaseModel):
    adv_wpp: str = Field(..., description="Número de WhatsApp do advogado (incluindo código do país, sem 'whatsapp:')")
    system_identifier: str = Field(..., description="Identificador numérico do sistema (ex: '1' para Eproc-RJ, '2' para PJE-RJ)")
    num_processo: str = Field(..., description="Número do processo a ser consultado.")

    # # Opcional: Adicionar validação para adv_wpp para garantir formato.
    # @field_validator('adv_wpp')
    # def validate_adv_wpp(cls, v):
    #     # Exemplo básico de validação de número de telefone. Ajuste conforme necessário.
    #     if not re.match(r"^\+\d{10,15}$", v):  # + seguido de 10 a 15 dígitos
    #         raise ValueError("adv_wpp deve ser um número de telefone válido, começando com '+' e código do país.")
    #     return v


    @field_validator('num_processo', mode='before')
    def validate_and_format_process_number(cls, v):
        formatted_v = ProcessNumberValidator.format_process_number(v)
        if not ProcessNumberValidator.is_valid(formatted_v):
            raise InvalidProcessNumberException(num_processo=v)
        return formatted_v




# --- DTOs e Modelos de Requisição ---

# DTOs para partes aninhadas (Movimento, Parte, etc.)
class MovimentoDTO(BaseModel): # Renomeado de Movimento para MovimentoDTO
    ordem: Optional[int] = None
    nome: str
    dataHora: datetime

class ParteDTO(BaseModel): # Adicionado, se você tiver uma estrutura de partes mais detalhada
    nome: str
    tipo: str # Ex: "Advogado", "Autor", "Réu"

# DTO Principal para dados raspados
class ProcessoScrapedDTO(BaseModel):
    partesEnvolvidas: str # Considerar usar List[ParteDTO] no futuro
    numeroProcesso: str
    tribunal: str
    sistema: str
    grau: str
    movimentos: List[MovimentoDTO] = Field(default_factory=list)
    dataHoraUltimaAtualizacao: datetime

