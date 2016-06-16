class AddressOrigin:
    ogn_ddb = 1
    flarmnet = 2
    user_defined = 3
    seen = 4

    def __init__(self, origin):
        if origin in [1, 2, 3, 4]:
            self.origin = origin
        else:
            raise ValueError('no address origin with id {} known'.format(origin))

    def name(self):
        if self.origin == self.ogn_ddb:
            return 'OGN-DDB'
        elif self.origin == self.flarmnet:
            return 'FlarmNet'
        elif self.origin == self.user_defined:
            return 'user-defined'
        elif self.origin == self.seen:
            return 'seen'
        return ''
