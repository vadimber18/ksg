user_schema = {
    'type': 'object',
    'properties': {
        'id': {'type': 'number'},
        'username': {'type': 'string'},
        'email': {'type': 'string'},
        'superuser': {'type': 'boolean'},
        'userpic': {'type': ['string', 'null']}
    },
    'required': [
        'id', 'username', 'email', 'superuser', 'userpic'
    ]
}
