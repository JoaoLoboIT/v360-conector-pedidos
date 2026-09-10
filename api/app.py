from flask import Flask, request, jsonify
from sqlalchemy.orm import joinedload
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

@app.route('/api/v1/pedidos', methods=['GET'])
def listar_pedidos():
    """
    Endpoint para listar pedidos de compra com filtros operacionais:
    - cliente: ex: ALFA, BETA
    - fornecedor: busca por CNPJ exato ou parte do nome
    - status: ex: ABERTO, BLOQUEADO
    - pendentes: 'true' para trazer apenas pedidos com saldo a receber nos itens
    """
    db = SessionLocal()
    try:
        query = db.query(PedidoCompraModel).options(joinedload(PedidoCompraModel.itens))

        # 1. Filtro por cliente de origem
        cliente = request.args.get('cliente')
        if cliente:
            query = query.filter(PedidoCompraModel.codigo_cliente == cliente.upper())

        # 2. Filtro por fornecedor (CNPJ ou Nome)
        fornecedor = request.args.get('fornecedor')
        if fornecedor:
            query = query.filter(
                (PedidoCompraModel.cnpj_fornecedor == fornecedor) |
                (PedidoCompraModel.nome_fornecedor.ilike(f"%{fornecedor}%"))
            )

        # 3. Filtro por situação do pedido
        status = request.args.get('status')
        if status:
            query = query.filter(PedidoCompraModel.status == status.upper())

        # 4. Filtro por itens com quantidades pendentes de recebimento
        pendentes = request.args.get('pendentes')
        if pendentes and pendentes.lower() == 'true':
            query = query.join(PedidoCompraModel.itens).filter(
                ItemPedidoModel.quantidade_pedida > ItemPedidoModel.quantidade_recebida
            ).distinct()

        pedidos = query.all()

        resultado = []
        for p in pedidos:
            resultado.append({
                "id": str(p.id),
                "codigo_cliente": p.codigo_cliente,
                "numero_pedido_origem": p.numero_pedido_origem,
                "cnpj_fornecedor": p.cnpj_fornecedor,
                "nome_fornecedor": p.nome_fornecedor,
                "data_emissao": p.data_emissao.strftime("%Y-%m-%d"),
                "status": p.status,
                "moeda": p.moeda,
                "itens": [
                    {
                        "id": str(i.id),
                        "numero_linha": i.numero_linha,
                        "codigo_material": i.codigo_material,
                        "descricao_material": i.descricao_material,
                        "valor_unitario_centavos": i.valor_unitario_centavos,
                        "unidade_medida": i.unidade_medida,
                        "quantidade_pedida": float(i.quantidade_pedida),
                        "quantidade_recebida": float(i.quantidade_recebida)
                    } for i in p.itens
                ]
            })

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": f"Erro interno ao consultar pedidos: {str(e)}"}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')