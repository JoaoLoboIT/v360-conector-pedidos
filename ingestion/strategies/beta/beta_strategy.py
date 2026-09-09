import csv
import io
from datetime import datetime
from sqlalchemy.orm import Session
from ingestion.strategies.base_strategy import BaseIngestionStrategy
from infrastructure.models import PedidoCompraModel, ItemPedidoModel


class BetaIngestionStrategy(BaseIngestionStrategy):

    def __init__(self, db: Session):
        self.db = db

    def process(self, raw_data: dict) -> None:
        """
        Espera um dicionário contendo as strings dos CSVs:
        {
           "cabecalho": "NUMERO_PEDIDO;FORNECEDOR_CNPJ;...",
           "itens": "NUMERO_PEDIDO;ITEM;CODIGO_MATERIAL;..."
        }
        """
        cabecalho_csv = raw_data.get("cabecalho", "")
        itens_csv = raw_data.get("itens", "")

        if not cabecalho_csv or not itens_csv:
            raise ValueError(
                "Os dados de 'cabecalho' e 'itens' do Cliente Beta são obrigatórios."
            )

        # 1. Parse do Cabeçalho
        pedidos_dict = {}
        cabecalho_file = io.StringIO(cabecalho_csv.strip())
        reader_cab = csv.DictReader(cabecalho_file, delimiter=";")

        for row in reader_cab:
            num_pedido = row.get("NUMERO_PEDIDO")

            # Remove a máscara do CNPJ (ex: 12.345.678/0001-90 vira 12345678000190)
            cnpj_com_mascara = row.get("FORNECEDOR_CNPJ", "")
            cnpj_limpo = "".join(filter(str.isdigit, cnpj_com_mascara))

            # Tratamento da data brasileira "15/08/2026"
            data_emissao_str = row.get("EMISSAO")
            data_emissao = datetime.strptime(data_emissao_str, "%d/%m/%Y")

            # Mapeamento do status (ex: "EM ABERTO" vira "ABERTO")
            situacao_bruta = row.get("SITUACAO", "").strip().upper()
            status_mapeado = (
                "ABERTO" if situacao_bruta == "EM ABERTO" else situacao_bruta
            )

            pedido_model = PedidoCompraModel(
                codigo_cliente="BETA",
                numero_pedido_origem=num_pedido,
                cnpj_fornecedor=cnpj_limpo,
                nome_fornecedor=row.get("FORNECEDOR_RAZAO_SOCIAL"),
                data_emissao=data_emissao,
                status=status_mapeado,
                moeda=row.get("MOEDA", "BRL"),
            )

            self.db.add(pedido_model)
            self.db.flush()  # Gera o UUID do pedido para vincular aos itens

            # Guarda a referência para associar os itens depois
            pedidos_dict[num_pedido] = pedido_model

        # 2. Parse dos Itens
        itens_file = io.StringIO(itens_csv.strip())
        reader_itens = csv.DictReader(itens_file, delimiter=";")

        for row in reader_itens:
            num_pedido = row.get("NUMERO_PEDIDO")
            pedido_pai = pedidos_dict.get(num_pedido)

            if not pedido_pai:
                continue  # Ignora itens cujo cabeçalho não foi enviado

            # Tratamento de números no padrão PT-BR (ex: "1.200,000" -> 1200.0)
            def parse_ptbr_decimal(value: str) -> float:
                if not value:
                    return 0.0
                # Remove o ponto de milhar e substitui a vírgula decimal por ponto
                cleaned = value.replace(".", "").replace(",", ".")
                return float(cleaned)

            qtd_pedida = parse_ptbr_decimal(row.get("QTD_PEDIDA"))
            qtd_recebida = parse_ptbr_decimal(row.get("QTD_RECEBIDA"))
            preco_unitario = parse_ptbr_decimal(row.get("PRECO_UNITARIO"))

            # Conversão para centavos inteiros
            valor_centavos = int(round(preco_unitario * 100))
            unidade = row.get("UNIDADE")

            item_model = ItemPedidoModel(
                pedido_id=pedido_pai.id,
                numero_linha=int(row.get("ITEM")),
                codigo_material=row.get("CODIGO_MATERIAL"),
                descricao_material=row.get("DESCRICAO"),
                valor_unitario_centavos=valor_centavos,
                # Campos de normalização
                unidade_medida=unidade,
                quantidade_pedida=qtd_pedida,
                quantidade_recebida=qtd_recebida,
                # Campos de auditoria (como o Beta mandou)
                unidade_original=unidade,
                quantidade_pedida_original=qtd_pedida,
                fator_conversao=1.0,
            )

            self.db.add(item_model)

        self.db.commit()
