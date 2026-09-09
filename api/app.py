from flask import Flask, jsonify
from infrastructure.database import engine, Base
# Importamos os modelos para o SQLAlchemy reconhecê-los
from infrastructure.models import PedidoCompraModel, ItemPedidoModel 

app = Flask(__name__)

# Este comando é a mágica: ele olha para os nossos modelos e cria as tabelas no banco caso não existam
Base.metadata.create_all(bind=engine)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "API V360 rodando com sucesso e Tabelas criadas!"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')