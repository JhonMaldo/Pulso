#!/usr/bin/env bash
# Firewall de nodo0 con temporizador de rescate (sección 8 del reporte del servidor).
# Correr en nodo0 con: bash nodo0_ufw.sh   (como root)
#
# NO usar "solo SSH, 80 y 443" (sección 6.8 del plan): en nodo0 eso apagaría Headscale (8080) y toda la VPN.
set -euo pipefail

# 1. Seguro: si te quedas sin acceso, UFW se apaga solo en 10 minutos.
systemd-run --unit=ufw-rescate3 --on-active=10m /usr/sbin/ufw disable

# 2. Reglas
ufw allow 22/tcp            # SSH
ufw allow 80/tcp            # HTTP (redirección y renovación de Certbot)
ufw allow 443/tcp           # HTTPS (Pulso)
ufw allow 8080/tcp          # Headscale: sin esto se cae la VPN
ufw allow in on tailscale0  # tráfico dentro de la VPN
ufw default deny incoming
ufw default allow outgoing
ufw --force enable
ufw status verbose

cat <<'TXT'

3. AHORA, en OTRA terminal y sin cerrar esta, comprueba:
   ssh -o ServerAliveInterval=30 -i TU_LLAVE root@79.143.88.200     (entra)
   curl http://79.143.88.200:8080/health                              ({"status":"pass"})
   curl -I https://TU_SUBDOMINIO.duckdns.org                          (responde)
   tailscale ping IP_VPN_DE_LA_VM                                     (pong)

4. Si todo responde, cancela el seguro ANTES de 10 minutos:
   systemctl stop ufw-rescate3.timer
   systemctl list-timers --all | grep ufw        (no debe mostrar nada)
   ufw status                                    (debe decir active)
TXT
