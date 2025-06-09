from modules.models.process_dtos import ProcessoScrapedDTO, MovimentoDTO
from modules.models.process_models import Movimento, Processo


class ProcessMapper:
    """
    Classe utilitária para mapear objetos entre DTOs de scraping e entidades de domínio.
    """

    @staticmethod
    def from_dto_to_entity(dto: ProcessoScrapedDTO) -> Processo:
        """
        Converte um ProcessoScrapedDTO em uma entidade Processo.
        """
        movimentos_entity = [
            Movimento(ordem=m.ordem, nome=m.nome, dataHora=m.dataHora)
            for m in dto.movimentos
        ]

        return Processo(
            partesEnvolvidas=dto.partesEnvolvidas,
            numeroProcesso=dto.numeroProcesso,
            tribunal=dto.tribunal,
            sistema=dto.sistema,
            grau=dto.grau,
            movimentos=movimentos_entity,
            dataHoraUltimaAtualizacao=dto.dataHoraUltimaAtualizacao
        )

    @staticmethod
    def from_entity_to_dto(entity: Processo) -> ProcessoScrapedDTO:
        """
        Converte uma entidade Processo em um ProcessoScrapedDTO.
        (Útil se você precisar enviar o Processo do Core para um DTO de saída)
        """
        movimentos_dto = [
            MovimentoDTO(ordem=m.ordem, nome=m.nome, dataHora=m.dataHora)
            for m in entity.movimentos
        ]

        return ProcessoScrapedDTO(
            partesEnvolvidas=entity.partesEnvolvidas,
            numeroProcesso=entity.numeroProcesso,
            tribunal=entity.tribunal,
            sistema=entity.sistema,
            grau=entity.grau,
            movimentos=movimentos_dto,
            dataHoraUltimaAtualizacao=entity.dataHoraUltimaAtualizacao
        )