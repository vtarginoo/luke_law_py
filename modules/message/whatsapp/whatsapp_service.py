import logging
import os

from twilio.rest import Client


logger = logging.getLogger(__name__)


class WhatsappService:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_WHATSAPP_FROM")

        if not self.account_sid or not self.auth_token or not self.twilio_phone_number:
            logger.error("Credenciais Twilio (SID, Token, Phone) não configuradas nas variáveis de ambiente.")
            raise ValueError("Credenciais Twilio ausentes.")

        self.client = Client(self.account_sid, self.auth_token)
        logger.info("Cliente Twilio inicializado.")

    def send_whatsapp_message(self, recipient_wpp: str, message_body: str)-> dict:
        """
        Envia uma mensagem de WhatsApp para um destinatário usando a API da Twilio.
        """
        try:

            if not recipient_wpp.startswith("whatsapp:"):
                recipient_wpp = "whatsapp:" + recipient_wpp

            message = self.client.messages.create(
                from_=self.twilio_phone_number,  # Seu número Twilio
                to=recipient_wpp,  # Número do destinatário
                body=message_body
            )
            logger.info(f"Mensagem enviada para {recipient_wpp}. SID: {message.sid}. Status: {message.status}")

            return {
                "message_sid": message.sid,
                "message_status": message.status
            }

        except Exception as e:
            logger.error(f"Falha ao enviar mensagem WhatsApp para {recipient_wpp}: {e}", exc_info=True)
            raise  # Re-lança a exceção para ser tratada pelo controller


