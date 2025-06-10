import logging
import time # Para manter o script rodando
from datetime import datetime, timedelta
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from modules.core.process_consultant import ProcessConsultant
from modules.models.process_dtos import ProcessoScrapedDTO, AnaliseUltimoMovimentoDTO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

process_consultant = ProcessConsultant()


class ActiveConsultantService :
    def __init__(self):

        self.scheduler = BackgroundScheduler()
        self.process_consultant = ProcessConsultant()
        self.processes_to_monitor = PROCESSES_TO_MONITOR_LIST

    def _perform_scraping(self, num_processo, system_identifier, adv_wpp)-> ProcessoScrapedDTO | None :
        """
        Main scheduled function that iterates over the list of processes
        and performs scraping for each, printing the result.
        """
        logger.info(f"--- Iniciando a Ordenação do Scrape")

        try:
            logger.info(f"Raspando processo: {num_processo} do sistema: {system_identifier} para {adv_wpp}...")

            # Call the scraping function from the instantiated service
            scraped_dto: ProcessoScrapedDTO = self.process_consultant.get_process_details(
                 num_processo ,system_identifier
            )

            logger.info(f"Scraping concluído para o processo: {num_processo}.")

            logger.info("\n" + "=" * 50)
            logger.info(f"RESULTADO DO SCRAPING PARA O PROCESSO {num_processo}:")
            logger.info(scraped_dto)
            logger.info("=" * 50 + "\n")

            return scraped_dto

        except Exception as e:
            logger.error(f"Erro ao raspar o processo '{num_processo}': {e}", exc_info=True)
            return None

    logger.info("--- Tarefa de scraping agendada concluída. ---")

    def _analyze_last_movement(self, scraped_dto: ProcessoScrapedDTO) -> AnaliseUltimoMovimentoDTO:
        """
        Analiza um ProcessoScrapedDTO para extrair o último movimento
        e determinar se ele é recente.
        """
        logger.info(f"Iniciando análise do último movimento para o processo: {scraped_dto.numeroProcesso}")

        ultimo_movimento = None
        movimento_recente = False
        ultima_atualizacao_delta_horas = 0.0

        if scraped_dto.movimentos:
            # Garante que estamos pegando o movimento com a dataHora mais recente
            ultimo_movimento = max(scraped_dto.movimentos, key=lambda m: m.dataHora)
            logger.info(f"Último movimento encontrado para {scraped_dto.numeroProcesso}: '{ultimo_movimento.nome}' em {ultimo_movimento.dataHora}")

            # Calcula a diferença de tempo desde a última atualização
            delta_tempo = datetime.now() - ultimo_movimento.dataHora
            ultima_atualizacao_delta_horas = delta_tempo.total_seconds() / 3600
            logger.info(f"Delta de tempo para {scraped_dto.numeroProcesso}: {ultima_atualizacao_delta_horas:.2f} horas.")

            # Define 'movimento_recente' com base no limite de 3 horas
            if ultima_atualizacao_delta_horas < 3:
                movimento_recente = True
                logger.info(f"Movimento para {scraped_dto.numeroProcesso} é considerado RECENTE (< 3h).")
            else:
                movimento_recente = False
                logger.info(f"Movimento para {scraped_dto.numeroProcesso} NÃO é considerado recente (>= 3h).")
        else:
            logger.warning(f"Processo {scraped_dto.numeroProcesso} não possui movimentos. 'ultimoMovimento' será None.")


        analise_dto = AnaliseUltimoMovimentoDTO(
            partesEnvolvidas=scraped_dto.partesEnvolvidas,
            numeroProcesso=scraped_dto.numeroProcesso,
            tribunal=scraped_dto.tribunal,
            sistema=scraped_dto.sistema,
            grau=scraped_dto.grau,
            dataHoraUltimaAtualizacao=scraped_dto.dataHoraUltimaAtualizacao,
            ultimoMovimento=ultimo_movimento,
            movimento_recente=movimento_recente,
            ultima_atualizacao_delta_horas=ultima_atualizacao_delta_horas
        )
        logger.info(f"Análise finalizada para o processo: {scraped_dto.numeroProcesso}. Movimento recente: {movimento_recente}")

        logger.info(
            f"DTO completo: {scraped_dto.numeroProcesso}.")
        return analise_dto

    def orchestrate_active_consultant(self) -> List[AnaliseUltimoMovimentoDTO]:
        """
        Orquestra o scraping de todos os processos na lista e a análise do último movimento de cada um.
        Retorna uma lista de AnaliseUltimoMovimentoDTO para processos bem-sucedidos.
        """
        logger.info(
            f"--- Iniciando Orquestração da Consulta Ativa de Processos às {datetime.now().strftime('%H:%M:%S')} ---")

        if not self.processes_to_monitor:
            logger.warning("Nenhum processo configurado na lista PROCESSES_TO_MONITOR. Pulando esta execução.")
            logger.info("--- Orquestração da Consulta Ativa de Processos Concluída. ---")  # Log de fim
            return []  # Retorna lista vazia se não houver nada para fazer

        analyzed_results: List[AnaliseUltimoMovimentoDTO] = []  # Lista para coletar os DTOs analisados

        for i, process_data in enumerate(self.processes_to_monitor):
            num_processo = process_data.get('num_processo')
            system_identifier = process_data.get('system_identifier')
            adv_wpp = process_data.get('adv_wpp')  # Certifique-se de que adv_wpp é usado, se necessário

            logger.info(
                f"Processando item {i + 1}/{len(self.processes_to_monitor)}: Processo {num_processo} no sistema {system_identifier}.")

            if not all([adv_wpp, system_identifier, num_processo]):
                logger.warning(f"Dados incompletos encontrados para o processo: {process_data}. Pulando este item.")
                continue

            # Etapa 1: Realizar o scraping para o processo atual
            scraped_dto = self._perform_scraping(num_processo, system_identifier, adv_wpp)

            # Etapa 2: Se o scraping foi bem-sucedido, proceed to analysis
            if scraped_dto:  # Verifica se não é None (se houve erro no scraping, será None)
                try:
                    analise_dto = self._analyze_last_movement(scraped_dto)
                    analyzed_results.append(analise_dto)  # Adiciona a análise à lista de resultados

                    # Imprimir o resultado da análise (fora do logger para visualização clara)
                    print("\n" + "#" * 50)
                    print(f"RESULTADO DA ANÁLISE DO ÚLTIMO MOVIMENTO PARA O PROCESSO {analise_dto.numeroProcesso}:")
                    print(analise_dto.model_dump_json(indent=4))
                    print("#" * 50 + "\n")

                except Exception as e:
                    logger.error(f"Erro ao analisar o processo '{num_processo}': {e}", exc_info=True)
            else:
                logger.warning(f"Scraping falhou ou retornou vazio para o processo {num_processo}. Análise pulada.")

            logger.info(f"Finalizado processamento para o processo: {num_processo}.")

        logger.info("--- Orquestração da Consulta Ativa de Processos Concluída. ---")
        logger.info(analyzed_results)


        return analyzed_results


    def start_service(self):
        """
        Creates and starts the APScheduler to execute the scheduled scraping task.
        """
        self.scheduler.add_job(
            id='initial_process_scraping',
            func=self.orchestrate_active_consultant,
            trigger=DateTrigger(run_date=datetime.now() + timedelta(seconds=5)),
            seconds=10,
            name='Consulta Ativa Inicial de Processos',
            replace_existing=True,
            max_instances=1,  # Permite apenas 1 instância da tarefa rodando
            coalesce=True,  # Principal para "só iniciar a próxima quando a anterior acabar"
            misfire_grace_time=15  # Tempo em segundos para descartar execuções perdidas (ajuste conforme necessidade)
        )

        logger.info("Serviço de consulta ativa iniciado. Agendador configurado.")
        self.scheduler.start()

        # This loop keeps the Python script running indefinitely.
        try:
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            self.scheduler.shutdown()
            logger.info("Serviço de consulta ativa encerrado.")


PROCESSES_TO_MONITOR_LIST = [
        {
            "adv_wpp": "+5521996800927",
            "system_identifier": "2",
            "num_processo": "0809129-51.2024.8.19.0001"
        },
        {
            "adv_wpp": "+5521996800927",
            "system_identifier": "1",
            "num_processo": "3002543-43.2025.8.19.0001"
        }
    ]





# --- Main Entry Point ---
if __name__ == '__main__':


    active_consultant = ActiveConsultantService()
    # Start the service
    active_consultant.start_service()







