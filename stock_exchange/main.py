from stock_exchange.models import UserProfile

user_1 = UserProfile(name="ABC", balance=20000).user
user_2 = UserProfile(name="PQR", balance=3000).user
user_3 = UserProfile(name="XYZ", balance=2000).user


if __name__ == '__main__':
    user_3.account.create_order(
        order_type="SELL",
        stock_name="FYND",
        quantity=5,
        price=300
    )

    user_1.account.create_order(
        order_type="BUY",
        stock_name="FYND",
        quantity=100,
        price=200
    )

    user_2.account.create_order(
        order_type="SELL",
        stock_name="FYND",
        quantity=90,
        price=100
    )

    user_3.account.create_order(
        order_type="SELL",
        stock_name="FYND",
        quantity=10,
        price=200
    )
