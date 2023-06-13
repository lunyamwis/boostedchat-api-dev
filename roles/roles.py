from rolepermissions.roles import AbstractUserRole

class Admin(AbstractUserRole):
    available_permissions = {
        "create_user": True
    }


class Influencer(AbstractUserRole):
    available_permissions = {
        'create_intent': True,
    }

