from datetime import datetime
from sqlalchemy.orm import Session
from ingestion.strategies.base_strategy import BaseIngestionStrategy
from infrastructure.models import PedidoCompraModel, ItemPedidoModel

class AlfaIngestionStrategy(BaseIngestionStrategy):
    
    def __init__(self, db: Session):
        self.db = db

    def process(self, raw_data: dict) -> None:
        # O Alfa envia um dicionário contendo a chave "purchase_orders"
        orders = raw_data.get("purchase_orders", [])

        for raw_po in orders:
            # 1. Normalização dos dados do cabeçalho do pedido
            numero_pedido = str(raw_po.get("po_number"))
            
            # Tratamento de data: "2026-08-05" vira um objeto datetime
            data_criacao_str = raw_po.get("created_at")
            data_emissao = datetime.strptime(data_criacao_str, "%Y-%m-%d")

            # Tradução de status: "open" do Alfa vira "ABERTO" no nosso domínio
            status_bruto = raw_po.get("status", "").lower()
            status_mapeado = "ABERTO" if status_bruto == "open" else status_bruto.upper()

            vendor = raw_po.get("vendor", {})
            cnpj_fornecedor = vendor.get("tax_id")
            nome_fornecedor = vendor.get("name")
            moeda = raw_po.get("currency", "BRL")

            # Criamos a instância do Modelo Único de Pedido
            pedido_model = PedidoCompraModel(
                codigo_cliente="ALFA",
                numero_pedido_origem=numero_pedido,
                cnpj_fornecedor=cnpj_fornecedor,
                nome_fornecedor=nome_fornecedor,
                data_emissao=data_emissao,
                status=status_mapeado,
                moeda=moeda
            )

            self.db.add(pedido_model)
            self.db.flush() # Garante que o ID do pedido seja gerado para associar aos itens

            # 2. Processamento dos Itens aninhados
            items = raw_po.get("items", [])
            for raw_item in items:
                numero_linha = raw_item.get("line")
                codigo_material = raw_item.get("material")
                descricao = raw_item.get("description")
                uom = raw_item.get("uom")
                
                qtd_pedida = float(raw_item.get("quantity_ordered", 0))
                qtd_recebida = float(raw_item.get("quantity_received", 0))
                
                # Regra de Ouro: Conversão de float para centavos inteiros
                preco_unitario_float = float(raw_item.get("unit_price", 0.0))
                valor_centavos = int(round(preco_unitario_float * 100))

                item_model = ItemPedidoModel(
                    pedido_id=pedido_model.id,
                    numero_linha=numero_linha,
                    codigo_material=codigo_material,
                    descricao_material=descricao,
                    valor_unitario_centavos=valor_centavos,
                    
                    # Campos de normalização/conferência
                    unidade_medida=uom,
                    quantidade_pedida=qtd_pedida,
                    quantidade_recebida=qtd_recebida,

                    # Campos de auditoria (como o Alfa mandou)
                    unidade_original=uom,
                    quantidade_pedida_original=qtd_pedida,
                    fator_conversao=1.0
                )

                self.db.add(item_model)

        # Efetiva a transação no banco de dados de uma só vez (Atomicidade)
        self.db.commit()