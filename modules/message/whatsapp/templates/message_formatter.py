import logging
from datetime import datetime

from modules.models.process_dtos import ProcessoScrapedDTO


logger = logging.getLogger(__name__)

def format_passive_generic_message(processo_dto: ProcessoScrapedDTO) -> str:
    """
    Formata os detalhes do processo raspado em uma string para envio via WhatsApp.

    Args:
        processo_dto (ProcessoScrapedDTO): O objeto DTO contendo os dados do processo.

    Returns:
        str: A mensagem formatada pronta para o WhatsApp.
    """

    # Verifica se há movimentos no processo. Se não houver, retorna uma mensagem alternativa.
    if not processo_dto.movimentos:
        return (
            f"*ℹ️ Informações do Processo:*\n\n"
            f"👥 *Partes:* {processo_dto.partesEnvolvidas}\n"
            f"📄 *Processo:* {processo_dto.numeroProcesso}\n"
            f"🏛️ *Tribunal:* {processo_dto.tribunal}\n"
            f"🖥️ *Sistema:* {processo_dto.sistema}\n\n"
            f"❌ Não há movimentos registrados para este processo até o momento."
        )

    logger.info("Scrapping iniciado a procura dos movimentos!")

    # Pega o último movimento da lista.
    latest_movimento = processo_dto.movimentos[0]

    logger.info(f"DEBUG: Tipo de latest_movimento.dataHora é: {type(latest_movimento.dataHora)}")
    logger.info(f"DEBUG: Valor de latest_movimento.dataHora é: {latest_movimento.dataHora}")

    # *** ESSA É A ÚNICA MUDANÇA NECESSÁRIA AQUI: ***
    # data_hora_movimento_obj JÁ É o objeto datetime!
    data_hora_movimento_obj = latest_movimento.dataHora  # REMOVA o datetime.fromisoformat() daqui!

    logger.info("A data já é um objeto datetime, sem necessidade de fromisoformat.")

    # Obtém a data e hora atual no momento da formatação da mensagem.
    data_hora_agora = datetime.now()

    # Formata o objeto datetime do movimento para a string no formato "dd/MM/yyyy HH:mm:ss".
    data_hora_formatada = data_hora_movimento_obj.strftime("%d/%m/%Y %H:%M:%S")

    # Calcula a diferença de tempo entre agora e a última movimentação.
    horas_desde_ultimo_movimento = int((data_hora_agora - data_hora_movimento_obj).total_seconds() / 3600)

    return (
        f"*ℹ️ Segue a última movimentação de seu processo:*\n\n"
        f"👥 *Partes:* {processo_dto.partesEnvolvidas}\n"
        f"📄 *Processo:* {processo_dto.numeroProcesso}\n"
        f"🏛️ *Tribunal:* {processo_dto.tribunal}\n"
        f"🖥️️ *Sistema:* {processo_dto.sistema}\n\n"
        f"*Última Movimentação:*\n"
        f"🔍 *Tipo:* {latest_movimento.nome}\n"
        f"🕒 *Data e Hora:* {data_hora_formatada}\n"
        f"⏳ *Horas desde a Última Movimentação:* {horas_desde_ultimo_movimento} horas\n\n"
        f"⚖️ Por favor, verifique os detalhes no sistema."
    )



