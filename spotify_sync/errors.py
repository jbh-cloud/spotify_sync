class SnapshotFileNotExists(Exception):
    pass


class RestoreZipNotExists(Exception):
    pass


class JsonSchemaInvalid(Exception):
    pass


class SpotifyError(Exception):
    pass


class OAuthNotFound(SpotifyError):
    pass


class DeezerError(Exception):
    pass


class ArlInvalid(DeezerError):
    pass
