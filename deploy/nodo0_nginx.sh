#!/usr/bin/env bash
# Instala el sitio de Pulso en NGINX de nodo0 y quita el que mandaba todo a danielserv.
# Uso (como root en nodo0, con pulso.conf ya editado y copiado a /root/pulso.conf):
#   bash nodo0_nginx.sh TU_SUBDOMINIO IP_VPN_DE_LA_VM
set -euo pipefail
SUB="${1:?Falta el subdominio, por ejemplo: pulso-equipo}"
IPVM="${2:?Falta la IP VPN de la VM, por ejemplo la de tailscale ip -4}"

df -h /                                      # el disco es de 4.9 GB y ya se llenó una vez
grep -lr "100.64.0.3:11434" /etc/nginx/sites-enabled/ || true
ls -l /etc/nginx/sites-enabled/

# Respaldo de la configuración actual
tar czf /root/nginx-respaldo-$(date +%F-%H%M).tgz /etc/nginx/sites-available /etc/nginx/sites-enabled

sed -e "s/TU_SUBDOMINIO/$SUB/g" -e "s/IP_VPN_DE_LA_VM/$IPVM/g" /root/pulso.conf > /etc/nginx/sites-available/pulso

# Quitar los sitios que apuntaban a danielserv:11434 (sin autenticación)
for f in /etc/nginx/sites-enabled/*; do
  if grep -q "100.64.0.3:11434" "$f"; then echo "Desactivando $f"; rm "$f"; fi
done
ln -sf /etc/nginx/sites-available/pulso /etc/nginx/sites-enabled/pulso

nginx -t && systemctl reload nginx
certbot certificates 2>/dev/null | grep -E "Certificate Name|Domains|Expiry" || true
curl -s -m 10 "https://$SUB.duckdns.org/api/salud"; echo
