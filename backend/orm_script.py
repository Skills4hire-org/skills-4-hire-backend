
import psycopg2


def ready():
    conn = psycopg2.connect(
        host="13.43.174.140",
        dbname="postgres",
        user="postgres",
        password="C0Oj9RnbMUdqRHPc",
        sslmode="require"
    )
    print("Connected!")
    conn.close()


if __name__ == "__main__":
    ready()

# import psycopg2
# conn = psycopg2.connect(
#     host="13.43.174.140",  # IPv4 directly
#     dbname="postgres",
#     user="postgres",
#     password="YOUR_PASSWORD",
#     sslmode="require"
# )

