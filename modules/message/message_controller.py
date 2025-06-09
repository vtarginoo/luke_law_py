import logging
import os

from flask import Blueprint, jsonify
from flask_pydantic import validate


from modules.core.process_consultant import ProcessConsultant
from modules.message.whatsapp.templates.message_formatter import format_passive_generic_message
from modules.message.whatsapp.whatsapp_service import WhatsappService
from modules.models.process_dtos import WppRequest

logger = logging.getLogger(__name__)

# Criação de um Blueprint para organizar as rotas
# O prefixo base será /api/v1/scrape
message_bp = Blueprint('message_api', __name__, url_prefix='/api/v1/whatsapp')

process_consultant = ProcessConsultant()
whatsapp_service = WhatsappService()

@message_bp.route('/', strict_slashes=False, methods=['POST'])
@validate()
def consulta_passiva_handle(body:WppRequest):
    """
    Endpoint para realizar o scraping de um processo no PJE-RJ.
    Recebe apenas o número do processo no corpo da requisição.
    """
    # 1. Realizar o scraping
    logger.info("Iniciar busca pelo processo")
    processo = process_consultant.get_process_details(body.num_processo,body.system_identifier)
    logger.info("Processo encontrado, iniciar a formatação da mensagem")

    # 2. Formatar a mensagem usando o MessageFormatter
    mensagem_formatada = format_passive_generic_message(processo)
    logger.info("Mensagem formatada!")

    # # 3. Enviar a mensagem formatada via WhatsappService
    logger.info(f"Enviando mensagem para o WhatsApp do destinatário: {body.adv_wpp}")
    whatsapp_service.send_whatsapp_message(
        recipient_wpp=body.adv_wpp,
        message_body=mensagem_formatada
    )
    logger.info("Mensagem enviada com sucesso para o WhatsApp.")

    twilio_response_data = whatsapp_service.send_whatsapp_message(
        recipient_wpp=body.adv_wpp,
        message_body=mensagem_formatada
    )
    logger.info("Mensagem enviada com sucesso para o WhatsApp.")

    return jsonify({
        "status": "success",
        "message": "Processo raspado e mensagem enviada com sucesso para o WhatsApp.",
        "process_number": body.num_processo,
        "recipient": body.adv_wpp,
        "whatsapp_preview_message": mensagem_formatada,
        "twilio_message_sid": twilio_response_data.get("message_sid"),
        "twilio_message_status": twilio_response_data.get("message_status")
    }), 200

@message_bp.route('/active', strict_slashes=False, methods=['POST'])
@validate()
def consulta_ativa_handle(body:WppRequest):
    """
    Endpoint para realizar o scraping de um processo no PJE-RJ.
    Recebe apenas o número do processo no corpo da requisição.
    """
    # 1. Realizar o scraping
    logger.info("Iniciar busca pelo processo")
    processo = process_consultant.get_process_details(body.num_processo,body.system_identifier)
    logger.info("Processo encontrado, iniciar a formatação da mensagem")

    # 2. Formatar a mensagem usando o MessageFormatter
    mensagem_formatada = format_passive_generic_message(processo)
    logger.info("Mensagem formatada!")

    # # 3. Enviar a mensagem formatada via WhatsappService
    logger.info(f"Enviando mensagem para o WhatsApp do destinatário: {body.adv_wpp}")
    whatsapp_service.send_whatsapp_message(
        recipient_wpp=body.adv_wpp,
        message_body=mensagem_formatada
    )
    logger.info("Mensagem enviada com sucesso para o WhatsApp.")

    twilio_response_data = whatsapp_service.send_whatsapp_message(
        recipient_wpp=body.adv_wpp,
        message_body=mensagem_formatada
    )
    logger.info("Mensagem enviada com sucesso para o WhatsApp.")

    return jsonify({
        "status": "success",
        "message": "Processo raspado e mensagem enviada com sucesso para o WhatsApp.",
        "process_number": body.num_processo,
        "recipient": body.adv_wpp,
        "whatsapp_preview_message": mensagem_formatada,
        "twilio_message_sid": twilio_response_data.get("message_sid"),
        "twilio_message_status": twilio_response_data.get("message_status")
    }), 200
