"""Keep-alive interno: el hilo pega a su propia URL pública cada < 15 min para que
Render (plan free) no suspenda el servicio por inactividad.

El cron de GitHub Actions resultó no confiable para esto: 5 corridas en 20 h para
un `*/10 * * * *`. Este hilo corre DENTRO del servicio ya despierto, así que no
depende de ningún scheduler externo. Si el servicio duerme (primer arranque del mes
o tras deploy), el primer visitante lo despierta y el hilo lo mantiene vivo.
"""

import threading
import time
import urllib.request

# Render duerme el servicio a los 15 min sin tráfico; 840s deja margen de seguridad.
RENDER_SLEEP_SECONDS = 15 * 60
MAX_INTERVAL = 840


def clamp_interval(interval: float) -> float:
    # El techo es el guard real (Render duerma a los 900s); el piso sólo evita spin.
    return max(0.01, min(float(interval), MAX_INTERVAL))


def ping(url: str) -> None:
    with urllib.request.urlopen(url, timeout=30) as resp:
        if getattr(resp, "status", 200) >= 400:
            raise RuntimeError(f"keepalive: HTTP {resp.status}")


def start_keepalive(url, interval: float = 600, ping_fn=None):
    """Lanza el hilo daemon de pings. Devuelve el Thread (o None si no hay URL).

    ping_fn es inyectable sólo para tests.
    """
    clean = (url or "").strip()
    if not clean:
        return None
    do_ping = ping_fn or ping
    period = clamp_interval(interval)

    def loop() -> None:
        while True:
            time.sleep(period)
            try:
                do_ping(clean)
            except Exception as exc:
                # Un ping fallido no mata el hilo: Render sigue despierto o reintentamos.
                print(f"keepalive: ping falló ({exc.__class__.__name__}), reintento en {period:.0f}s")

    thread = threading.Thread(target=loop, name="keepalive", daemon=True)
    thread.start()
    return thread
