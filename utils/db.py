import psycopg2, os 

def get_connection():
    return psycopg2.connect(os.getenv("DB_CONFIG"))

def create_tables():
    connexion = get_connection()
    cursor = connexion.cursor()

    connexion.execute("""CREATE TABLE IF NOT EXISTS annonces (
            id INT PRIMARY KEY,
            name VARCHAR(255),
            price INT(50),
            surface INT(50),
            url VARCHAR(255),
        """)

    connexion.commit()

    cursor.close()
    connexion.close()