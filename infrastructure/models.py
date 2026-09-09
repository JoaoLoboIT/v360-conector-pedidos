import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from infrastructure.database import Base
from sqlalchemy import func


class PedidoCompraModel(Base):
    __tablename__ = "pedidos_compra"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_cliente = Column(String, nullable=False)
    numero_pedido_origem = Column(String, nullable=False)
    cnpj_fornecedor = Column(String, nullable=False)
    nome_fornecedor = Column(String, nullable=True)
    data_emissao = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    moeda = Column(String, default="BRL")

    itens = relationship(
        "ItemPedidoModel", back_populates="pedido", cascade="all, delete-orphan"
    )
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())


class ItemPedidoModel(Base):
    __tablename__ = "itens_pedido"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(
        UUID(as_uuid=True), ForeignKey("pedidos_compra.id"), nullable=False
    )
    numero_linha = Column(Integer, nullable=False)
    codigo_material = Column(String, nullable=False)
    descricao_material = Column(String, nullable=True)
    valor_unitario_centavos = Column(Integer, nullable=False)

    # CAMPOS DA NOSSA PLATAFORMA (Valores normalizados para a conferência da V360)
    unidade_medida = Column(
        String, nullable=False
    )  # Ex: UN (Mesmo que o cliente mande CX)
    quantidade_pedida = Column(
        Numeric(15, 4), nullable=False
    )  # Ex: 120 (Se vieram 10 CX com fator 12)
    quantidade_recebida = Column(
        Numeric(15, 4), default=0.0
    )  # Ex: 24  (Se já vieram 2 CX)

    # CAMPOS DE AUDITORIA (Exatamente como veio do ERP do cliente)
    unidade_original = Column(String, nullable=False)  # Ex: CX
    quantidade_pedida_original = Column(Numeric(15, 4), nullable=False)  # Ex: 10
    fator_conversao = Column(Numeric(15, 4), default=1.0)  # Ex: 12

    pedido = relationship("PedidoCompraModel", back_populates="itens")
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
