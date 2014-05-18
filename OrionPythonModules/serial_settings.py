# serial_settings - A placeholder for the module on the OrionLXm


class SerialSettings(object):
    def __init__(self):
        self.cards = [
            {'type': '124',
             'ports': [
                 {'type': 'Loopback'},
                 {'type': 'Loopback'},
                 {'type': 'Loopback'},
                 {'type': 'Loopback'}, ]
            },
            {'type': '124',
             'ports': [
                 {'type': 'Loopback'},
                 {'type': 'Loopback'},
                 {'type': 'Loopback'},
                 {'type': 'Loopback'}, ]
            }]

    def apply(self):
        pass