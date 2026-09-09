from flask import Flask, request, jsonify
from infrastructure.database import engine, Base, SessionLocal
from infrastructure.models import PedidoCompraModel, ItemPedidoModel 
from ingestion.factories.strategy_factory import StrategyFactory

app = Flask(__name__)

# Cria as tabelas caso não existam
Base.metadata.create_all(bind=engine)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "API V360 rodando com sucesso e Tabelas criadas!"}), 200

@app.route('/api/v1/ingest/<client_code>', methods=['POST'])
def ingest_data(client_code):
    """
    Endpoint universal de ingestão. 
    Exemplo de chamada: POST /api/v1/ingest/ALFA
    """
    db = SessionLocal()
    try:
        raw_data = request.get_json()
        if not raw_data:
            return jsonify({"error": "Payload JSON vazio ou inválido"}), 400

        # Obtém a estratégia correta através da Fábrica
        strategy = StrategyFactory.get_strategy(client_code, db)
        
        # Executa a ingestão e normalização
        strategy.process(raw_data)

        return jsonify({
            "status": "success",
            "message": f"Dados do cliente {client_code.upper()} ingeridos e normalizados com sucesso!"
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Erro interno ao processar carga: {str(e)}"}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')