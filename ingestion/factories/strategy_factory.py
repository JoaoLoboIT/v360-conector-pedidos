from sqlalchemy.orm import Session
from ingestion.strategies.alfa.alfa_strategy import AlfaIngestionStrategy
from ingestion.strategies.beta.beta_strategy import BetaIngestionStrategy

class StrategyFactory:
    
    @staticmethod
    def get_strategy(client_code: str, db: Session):
        client = client_code.upper()
        
        if client == "ALFA":
            return AlfaIngestionStrategy(db)
        if client == "BETA":
            return BetaIngestionStrategy(db)
        
        raise ValueError(f"Nenhuma estratégia de ingestão encontrada para o cliente: {client_code}")