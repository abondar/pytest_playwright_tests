import json

# Temporary no-op change for git workflow verification.


def get_user_data(user_name):
    with open('fixtures/users.json') as test_data:
        user_data = json.load(test_data)
        user = user_data[user_name]['user'],
        password = user_data[user_name]['password']
    return user, password


def get_all_users_data():
    with open('fixtures/users.json') as test_data:
        user_data = json.load(test_data)
        extracted_data = tuple(user_data.items())
        return extracted_data
