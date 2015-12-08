class AddressOrigin:
    ogn_ddb = 1
    flarmnet = 2
    userdefined = 3

    def __init__(self, origin):
        if origin in [1, 2, 3]:
            self.origin = origin
        else:
            raise ValueError('no address origin with id {} known'.format(origin))

    def name(self):
        if self.origin == self.ogn_ddb:
            return 'ogn_ddb'
        elif self.origin == self.flarmnet:
            return 'flarmnet'
        elif self.origin == self.userdefined:
            return 'userdefined'
        return ''
