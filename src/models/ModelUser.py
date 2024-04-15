from .entities.User import User


class ModelUser():

    @classmethod
    def login(self, db, user):
        try:
            cursor = db.connection.cursor()
            sql = """SELECT id, email, password, fullname FROM user 
                    WHERE email = '{}'""".format(user.email)
            cursor.execute(sql)
            row = cursor.fetchone()
            if row != None:
                user = User(row[0], row[1], User.check_password(row[2], user.password), row[3])
                return user
            else:
                return None
        except Exception as ex:
            raise Exception(ex)

    @classmethod
    def get_by_id(self, db, id):
        try:
            cursor = db.connection.cursor()
            sql = "SELECT id, email, fullname FROM user WHERE id = {}".format(id)
            cursor.execute(sql)
            row = cursor.fetchone()
            if row != None:
                return User(row[0], row[1], None, row[2])
            else:
                return None
        except Exception as ex:
            raise Exception(ex)

    @classmethod
    def register(self, db, user):
        try:
            cursor = db.connection.cursor()
            sql = """SELECT id, email, password, fullname FROM user 
                    WHERE email = '{}'""".format(user.email)
            cursor.execute(sql)
            row = cursor.fetchone()
            if row != None:
                user = User(row[0], row[1], User.create_password(row[2], user.password), row[3])

                print(user)

                #sql = """INSERT INTO user (email, password, fullname, id_usertype) 
                #        VALUES ('{}', '{}', '{}', '{}')""".format(user.email, hashed_password, user.fullname, user.id_usertype)
                #cursor.execute(sql)

            else:
                return None
        except Exception as ex:
            raise Exception(ex)