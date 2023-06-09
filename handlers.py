
class DB_Writer:

    def __init__(self, conn) -> None:
        self.__conn = conn
        self.__cursor = conn.cursor()

    def reg_user(self, username, password):
        query = "INSERT INTO users(username, password) VALUES (?, ?)"
        data = (username, password)
        self.__cursor.execute(query, data)
        self.__conn.commit()

    def login_user(self, username, password):
        query = "SELECT password FROM users WHERE username = ?"
        check_data = self.__cursor.execute(query, (username, )).fetchone()[0]
        return check_data == password
    
    def get_product_mark(self, product_id):
        query = "SELECT p.nume, e.nota FROM Evaluari e JOIN Produse p ON p.id = e.FK_product_id WHERE p.id = ? and e.status = 1"
        data = self.__cursor.execute(query, (product_id, )).fetchall()
        return data
    
    def get_product_evals(self, product_id):
        query = "SELECT p.nume, e.text, e.nota FROM Evaluari e JOIN Produse p ON p.id = e.FK_product_id WHERE p.id = ? and e.status = 1"
        data = self.__cursor.execute(query, (product_id, )).fetchall()
        return data
        

def task1(data):
    prod_name = data[0][0]
    prod_marks = [mark for _, mark in data]
    prod_mark = sum(prod_marks) / len(prod_marks)
    return prod_name, prod_mark

def task2(data):
    prod_name = data[0][0]
    prod_evaluations = [ (item[1], item[2]) for item in data ] 
    return prod_name, prod_evaluations
