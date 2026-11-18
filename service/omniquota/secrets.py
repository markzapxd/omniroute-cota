"""Secret Service only: intentionally no file fallback."""
class SecretStore:
    def __init__(self):
        import gi
        gi.require_version('Secret','1')
        from gi.repository import Secret
        self.Secret = Secret
        self.schema = Secret.Schema.new('io.github.omniquota',Secret.SchemaFlags.NONE,
                                        {'key':Secret.SchemaAttributeType.STRING})

    def get(self,key):
        return self.Secret.password_lookup_sync(self.schema,{'key':key},None)

    def set(self,key,value):
        ok = self.Secret.password_store_sync(self.schema,{'key':key},self.Secret.COLLECTION_DEFAULT,
                                             'OmniQuota — sessão ou senha',value,None)
        if not ok: raise RuntimeError('Não foi possível salvar no chaveiro.')

    def delete(self,key):
        self.Secret.password_clear_sync(self.schema,{'key':key},None)
