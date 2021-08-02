from dataclasses import dataclass, InitVar, field
from datetime import datetime
from typing import Any
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)

seller_order_pool = dict()
buyer_order_pool = dict()


@dataclass
class User:
    name: str
    id: str = field(default=str(uuid4()), repr=False)
    account: Any = field(init=False, repr=False)


@dataclass
class Order:
    user: User
    order_type: str
    stock_name: str = field(repr=False)
    quantity: int = field(repr=False)
    price: float = field(repr=False)
    pending_quantity: int = field(init=False, repr=False)
    id: str = field(default=str(uuid4()), repr=False)
    created_on: datetime = field(default=datetime.now(), repr=False)
    updated_on: datetime = field(default=datetime.now(), repr=False)
    completed_on: Any = field(default=None, repr=False)
    status: str = field(default="PENDING", repr=False)

    def __post_init__(self):
        self.pending_quantity = self.quantity

    @staticmethod
    def get_buyable_quantity(seller_order, buyer_order):
        buyable_quantity = 0
        if (
                seller_order.status in ["PENDING", "PROCESSING"] and
                seller_order.stock_name == buyer_order.stock_name and
                buyer_order.pending_quantity > 0 and
                buyer_order.price >= seller_order.price
        ):
            buyable_quantity = seller_order.pending_quantity if seller_order.pending_quantity < buyer_order.pending_quantity else buyer_order.pending_quantity
        return buyable_quantity

    @staticmethod
    def process_orders(seller_order, buyer_order, buyable_quantity):
        # update order fields
        buyer_order._process(buyable_quantity)
        seller_order._process(buyable_quantity)

        # update account balance and create ledger
        amount = buyable_quantity * seller_order.price
        seller_order.user.account.deposit(amount)
        buyer_order.user.account.withdraw(amount)
        ledger = OrderLedger(buyer_order=buyer_order,
                             seller_order=seller_order,
                             price=seller_order.price,
                             quantity=buyable_quantity,
                             stock=seller_order.stock_name)

        logger.info({
            "seller balance": seller_order.user.account.balance,
            "buyer_balance": buyer_order.user.account.balance,
            "ledger": ledger
        })

    def _process(self, buyable_quantity):
        self.updated_on = datetime.now()
        self.pending_quantity -= buyable_quantity

        if self.pending_quantity == 0:
            self.completed_on = datetime.now()
            self.status = "COMPLETED"
        else:
            self.status = "PROCESSING"


@dataclass
class OrderLedger:
    buyer_order: Order
    seller_order: Order
    stock: str
    quantity: str
    price: float


def refresh_order_pool():
    for seller_order in list(seller_order_pool.values()):
        for buyer_order in list(buyer_order_pool.values()):
            buyable_quantity = Order.get_buyable_quantity(seller_order=seller_order,
                                                          buyer_order=buyer_order)
            if buyable_quantity > 0:
                Order.process_orders(seller_order=seller_order,
                                     buyer_order=buyer_order,
                                     buyable_quantity=buyable_quantity)
                if buyer_order.pending_quantity == 0:
                    buyer_order_pool.pop(buyer_order.id)
        if seller_order.pending_quantity == 0:
            seller_order_pool.pop(seller_order.id)


@dataclass
class DMATAccount:
    user: User
    balance: float = 0.0
    stocks: dict = field(default_factory=dict)
    orders: dict = field(default_factory=dict)

    def create_order(self, *args, order_type=None, **kwargs):
        order = Order(*args, user=self.user, order_type=order_type, **kwargs)
        self.orders[order.id] = order
        order_pool = seller_order_pool if order_type == "SELL" else buyer_order_pool
        order_pool[order.id] = order
        refresh_order_pool()

    def withdraw(self, amount):
        self.balance -= amount

    def deposit(self, amount):
        self.balance += amount


@dataclass
class UserProfile:
    name: str
    balance: float
    user: User = field(init=False)

    def __post_init__(self):
        self.user = User(name=self.name)
        self.user.account = DMATAccount(user=self.user, balance=self.balance)
