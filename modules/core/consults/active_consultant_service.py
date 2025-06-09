import logging
import time # Para manter o script rodando
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from modules.core.consults.passive_consultant_service import PassiveConsultantService
from modules.models.process_dtos import ProcessoScrapedDTO

logger = logging.getLogger(__name__)

passive_consultant_service = PassiveConsultantService()


# --- A Função da Tarefa Agendada ---
def perform_scheduled_scraping():
    """
    Função principal agendada que itera sobre a lista de processos
    e realiza o scraping para cada um, printando o resultado.
    """
    current_hour = datetime.now().hour

    # O cron do APScheduler garantirá que isso rode no minuto 0 das horas 9 a 19.
    # Mas a verificação de horário dentro da função adiciona uma camada de segurança.
    if 9 <= current_hour <= 19:
        logger.info(f"--- Iniciando tarefa de scraping agendada às {datetime.now().strftime('%H:%M:%S')} ---")

        if not PROCESSES_TO_MONITOR:
            logger.warning("Nenhum processo configurado na lista PROCESSES_TO_MONITOR. Pulando esta execução.")
            return

        for process_data in PROCESSES_TO_MONITOR:
            adv_wpp = process_data.get('adv_wpp')
            system_identifier = process_data.get('system_identifier')
            num_processo = process_data.get('num_processo')

            if not all([adv_wpp, system_identifier, num_processo]):
                logger.warning(f"Dados incompletos na lista para o processo: {process_data}. Pulando este item.")
                continue

            try:
                # 1. Chamar a função de scraping do PassiveConsultantService
                logger.info(f"Raspando processo: {num_processo} do sistema: {system_identifier} para {adv_wpp}...")

                # AQUI É O PONTO CENTRAL: CHAMA SUA FUNÇÃO DE SCRAPING!
                scraped_dto: ProcessoScrapedDTO = passive_consultant_service.process_passive_consultation(
                    adv_wpp, system_identifier, num_processo
                )

                logger.info(f"Scraping concluído para o processo: {num_processo}.")

                # 2. Printar o resultado do scraping (o DTO retornado)
                print("\n" + "=" * 50)
                print(f"RESULTADO DO SCRAPING PARA O PROCESSO {num_processo}:")
                # Usamos .json() para uma representação JSON legível do Pydantic DTO
                print(scraped_dto.json(indent=4))
                print("=" * 50 + "\n")

            except Exception as e:
                logger.error(f"Erro ao raspar o processo '{num_processo}': {e}", exc_info=True)

        logger.info("--- Tarefa de scraping agendada concluída. ---")

    else:
        logger.info(
            f"Fora do horário de operação (9h-19h). Hora atual: {datetime.now().strftime('%H:%M:%S')}. Aguardando próximo ciclo.")


# --- Configuração e Início do Scheduler ---
def start_active_consultant_service():
    """
    Cria e inicia o APScheduler para executar a tarefa de scraping agendada.
    """
    # BackgroundScheduler é usado para scripts que rodam em segundo plano.
    scheduler = BackgroundScheduler()

    # Adiciona a tarefa `perform_scheduled_scraping` ao agendador.
    scheduler.add_job(
        id='initial_process_scraping',  # Um ID único para esta tarefa inicial
        func=perform_scheduled_scraping,  # A função que será executada
        trigger='interval',  # Usamos 'interval' em vez de 'cron'
        seconds=10,  # Roda após 10 segundos
        name='Consulta Ativa Inicial de Processos',  # Nome amigável para a tarefa
        replace_existing=True,  # Garante que não haja jobs duplicados
        max_instances=1  # Garante que rode apenas uma vez
    )

    logger.info("Serviço de consulta ativa iniciado. Agendador configurado.")
    scheduler.start()  # Inicia o agendador!

    # Este loop mantém o script Python rodando indefinidamente.
    # O scheduler opera em um thread separado, então o thread principal precisa estar ativo.
    try:
        while True:
            time.sleep(2)  # Pausa por 2 segundos para evitar consumo excessivo de CPU.
    except (KeyboardInterrupt, SystemExit):
        # Captura Ctrl+C (KeyboardInterrupt) ou sinais de saída do sistema (SystemExit)
        # para desligar o scheduler de forma limpa.
        scheduler.shutdown()
        logger.info("Serviço de consulta ativa encerrado.")


# --- Ponto de Entrada Principal ---
if __name__ == '__main__':
    start_active_consultant_service()

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







