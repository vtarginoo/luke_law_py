import logging
import time # Para manter o script rodando
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# --- A Função da Tarefa Agendada (o "core" do seu serviço de agendamento) ---
def check_and_process_modifications():
    """
    Função principal agendada que verifica modificações nos processos da lista
    PROCESSES_TO_MONITOR e dispara ações (como notificação) se necessário.
    """
    global previous_process_states # Indica que estamos usando a variável global

    current_hour = datetime.now().hour

    # O horário atual é Terça-feira, 10 de Junho de 2025, 18:39:40 -03
    # Lembre-se que o scheduler vai rodar às 19:00:00 e depois só às 09:00:00 de amanhã.
    if 9 <= current_hour <= 19: # Roda das 9h às 19h (inclusive)
        logger.info \
            (f"--- Iniciando tarefa de verificação de processos agendada às {datetime.now().strftime('%H:%M:%S')} ---")

        if not PROCESSES_TO_MONITOR:
            logger.warning("Nenhum processo configurado na lista PROCESSES_TO_MONITOR. Pulando esta execução.")
            return

        for process_data in PROCESSES_TO_MONITOR:
            adv_wpp = process_data.get('adv_wpp')
            system_identifier = process_data.get('system_identifier')
            num_processo = process_data.get('num_processo')

            if not all([adv_wpp, system_identifier, num_processo]):
                logger.warning(f"Dados incompletos na lista para o processo: {process_data}. Pulando verificação.")
                continue

            process_key = f"{system_identifier}-{num_processo}"

            try:
                # 1. Scraping: Obtém os detalhes ATUAIS do processo
                current_process_details = passive_consultant_service.process_passive_consultation(
                    adv_wpp, system_identifier, num_processo
                )
                logger.debug(f"Processo '{num_processo}' consultado com sucesso.")

                # Converte o DTO para um formato comparável. Adapte se necessário.
                current_state_for_comparison = current_process_details.__dict__

                # 2. Comparação: Verifica se este processo já foi raspado antes
                if process_key in previous_process_states:
                    if previous_process_states[process_key] != current_state_for_comparison:
                        logger.info(f"*** MODIFICAÇÃO DETECTADA NO PROCESSO: {num_processo}! ***")
                        # --- AÇÃO QUANDO UMA MODIFICAÇÃO É ENCONTRADA ---
                        # Aqui você chamaria o serviço de WhatsApp para enviar a notificação.
                        # formatted_message = format_passive_generic_message(current_process_details)
                        # whatsapp_service.send_whatsapp_message(adv_wpp, formatted_message)

                        print(f"NOTIFICAÇÃO: Modificação detectada para {num_processo}. Notificando {adv_wpp}.")
                    else:
                        logger.info \
                            (f"Processo '{num_processo}': Nenhuma modificação detectada desde a última verificação.")
                else:
                    logger.info(f"Processo '{num_processo}': Primeira consulta. Armazenando estado inicial.")

                # 3. Atualizar Estado: Guarda o estado ATUAL do processo para a próxima comparação
                previous_process_states[process_key] = current_state_for_comparison

            except Exception as e:
                logger.error(f"Erro ao processar/verificar o processo '{num_processo}': {e}", exc_info=True)

        logger.info("--- Verificação de processos agendada concluída. ---")

    else:
        logger.info \
            (f"Fora do horário de operação (9h-19h). Hora atual: {datetime.now().strftime('%H:%M:%S')}. Aguardando próximo ciclo.")

# --- Configuração e Início do Scheduler ---
def start_active_consultant_scheduler():
    """
    Cria e inicia o APScheduler para executar a tarefa de verificação de processos.
    Esta função será chamada para iniciar o serviço.
    """
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        id='hourly_process_modification_check',
        func=check_and_process_modifications,
        trigger=CronTrigger(hour='9-19', minute='0'), # Roda no minuto 0 de cada hora, das 9h às 19h
        name='Verificação Horária de Modificações de Processo',
        replace_existing=True
    )

    logger.info("Serviço de consulta ativa iniciado. Agendador configurado.")
    scheduler.start()

    try:
        while True:
            time.sleep(2) # Dorme por 2 segundos para não consumir CPU desnecessariamente
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Serviço de consulta ativa encerrado.")


PROCESSES_TO_MONITOR = [
    {
        "adv_wpp": "+5521996800927",
        "system_identifier": "2",
        "num_processo": "0809129-51.2024.8.19.0001"
    },
    {
        "adv_wpp": "+5521888888888",
        "system_identifier": "1",
        "num_processo": "0000000-00.2024.8.26.0000"
    }
    # Adicione mais processos aqui conforme necessário
]




# --- Ponto de Entrada Principal para Rodar este Serviço ---
if __name__ == '__main__':
    # Quando você executa 'python modules/core/consults/active_consultant_service.py',
    # esta parte do código será executada e iniciará o agendador.
    start_active_consultant_scheduler()




