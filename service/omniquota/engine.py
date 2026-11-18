from datetime import datetime, timezone
from .quota import normalize_usage, panel_percent, number
from .client import ApiError

class Engine:
    def __init__(self):
        self.generation = 0
        self.busy = False
        self.reset()

    def reset(self):
        self.generation += 1
        self.busy = False
        self.delay = 60
        self.state = {'version':1,'status':'signed-out','windows':[], 'remainingPercent':None,
                      'bankedResetCredits':None,'updatedAt':None,'message':'Entre para consultar a cota.','stale':False}

    def begin(self):
        if self.busy: return None
        self.busy = True
        return self.generation

    def success(self,ticket,payload):
        if ticket != self.generation: return
        windows = normalize_usage(payload)
        credits = payload.get('bankedResetCredits')
        credits = int(credits) if number(credits) and credits >= 0 and credits == int(credits) else None
        self.state.update(bankedResetCredits=credits,status='ready' if panel_percent(windows) is not None else 'unsupported',
                          windows=windows,remainingPercent=panel_percent(windows),
                          updatedAt=datetime.now(timezone.utc).isoformat(),
                          stale=bool(payload.get('_stale')),
                          message='Dados anteriores do provedor.' if payload.get('_stale') else
                          ('Menor saldo entre as janelas conhecidas.' if windows else 'Cota indisponível nesta conexão.'))
        self.busy = False
        self.delay = 60

    def failure(self,ticket,error):
        if ticket != self.generation: return
        code = error.status if isinstance(error,ApiError) else 500
        # Never expose raw exception strings: keyring/HTTP errors can contain secrets.
        message = str(error) if isinstance(error,ApiError) else 'Erro no serviço ou chaveiro. Verifique as dependências e desbloqueie o chaveiro.'
        self.state.update(status='signed-out' if code == 401 else 'unsupported' if code == 501 else 'error',
                          message=message,stale=self.state['updatedAt'] is not None)
        self.delay = max(min(self.delay*2,900),getattr(error,'retry_after',60))
        self.busy = False
