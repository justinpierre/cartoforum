from orm_classes import sess, Users


def get_alternate_username(username):
    while True:
        for i in range(1000000):
            alt_name = u"{}{}".format(username, i)
            userquery = sess.query(Users).filter_by(username='{}'.format(alt_name)).count()
            if userquery == 0:
                return alt_name
