import shelve


def del_local_data():
    with shelve.open("data/data") as db:
        for i in db:
            del db[i]


if __name__ == '__main__':
    del_local_data()
