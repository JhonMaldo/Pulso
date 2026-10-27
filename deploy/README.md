# Despliegue de Pulso (actividades 5 y 10)

> **Uso diario:** para encender o apagar Pulso en la PC anfitriona basta un doble clic. Ver [windows/GUIA_ENCENDER_APAGAR.md](windows/GUIA_ENCENDER_APAGAR.md).

Arquitectura: celular → `https://TU_SUBDOMINIO.duckdns.org` → NGINX en `nodo0` (`100.64.0.2`) → túnel de Headscale → VM cliente (`IP_VPN_DE_LA_VM:8000`, FastAPI + pantallas) → Ollama en `localhost:11434` dentro de la misma VM.

Reemplaza en todos los pasos:

| Marcador | De dónde sale |
|---|---|
| `IP_VPN_DE_LA_VM` | **`100.64.0.1`** (VM VirtualBox `ubuntu`, nodo `alonso`; confirmado con `tailscale ip -4` el 21 oct) |
| `TU_SUBDOMINIO` | **`mentalhealth-app`** (`mentalhealth-app.duckdns.org`, certificado válido hasta el 14 ene 2027) |
| `USUARIO_VM` | **`alonso`** |

Datos de la VM confirmados el 21 oct: Ubuntu 26.04 LTS, Python 3.14.4, sin Node (compilar `dist/` en otra PC y copiarlo), Ollama 0.33.2 en Docker con `granite4.2:3b` y `tinyllama`. El usuario `alonso` no está en el grupo `docker` (usar `sudo`). **Ollama escucha en `0.0.0.0:11434`**: correr `vm_ollama_localhost.sh`.

Ningún paso imprime llaves, tokens ni contraseñas. El `.env` real no se sube a git.

## 1. Preparar la VM (rol 4)

1. Enciende la computadora que hospeda la VM y luego la VM (VirtualBox). Dale al menos **4 GB de RAM**: con 3 GB el modelo se colgaba (reporte del agente del clima).
2. Revisa el reloj (en el pasado causó errores 401 y de `apt`): `timedatectl`; si está mal, `sudo systemctl restart systemd-timesyncd`.
3. Reconéctala a Headscale:
   ```bash
   sudo tailscale up --login-server=http://79.143.88.200:8080
   ```
   Si sale `changing settings via 'tailscale up' requires mentioning all non-default flags`, copia y corre el comando que sugiere el mensaje (en el reporte fue `--accept-routes`).
4. Comprueba:
   ```bash
   tailscale status        # nodo0 y esta VM deben salir sin "offline"
   tailscale ip -4         # anota IP_VPN_DE_LA_VM
   ping -c 3 100.64.0.2    # nodo0 responde por la VPN
   ```

## 2. Ollama solo en localhost (rol 4)

```bash
git clone https://github.com/JhonMaldo/Pulso.git ~/Pulso   # o git pull si ya existe
cd ~/Pulso
sudo bash deploy/vm_ollama_localhost.sh   # deja el 11434 en 127.0.0.1 y con reinicio automático
bash deploy/verificar_ollama.sh           # ollama list, /api/tags y una llamada con tool
```

Si `verificar_ollama.sh` no muestra `tool_calls` o tarda más de 60 s, prueba un modelo pequeño con buen soporte de tools, por ejemplo `qwen2.5:1.5b` o `llama3.2:3b` (`sudo docker exec ollama ollama pull qwen2.5:1.5b`), y ponlo en `OLLAMA_MODELO`.

## 3. La app en la VM (rol 4)

```bash
cd ~/Pulso
sudo apt install -y python3-venv nodejs npm      # node 20.19+ o 22.12+ para Vite
npm ci && npm run build                          # genera dist/
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env                # OLLAMA_MODELO = el de `ollama list`
.venv/bin/python validar_datos.py
.venv/bin/python -m pytest -q                    # todo debe pasar
```

Si no hay Node en la VM: corre `npm run build` en otra computadora y copia la carpeta `dist/` a `~/Pulso/dist`.

Servicio y firewall:

```bash
sed "s/USUARIO_VM/$(whoami)/g" ~/Pulso/deploy/pulso.service | sudo tee /etc/systemd/system/pulso.service
sudo systemctl daemon-reload
sudo systemctl enable --now pulso
systemctl status pulso --no-pager
curl http://localhost:8000/api/salud             # {"ok":true}
curl http://localhost:8000/api/salud/ollama      # "ok": true si el modelo está
sudo bash ~/Pulso/deploy/vm_ufw.sh               # 8000 solo desde tailscale0; 11434 cerrado
```

Para actualizar después de un `git pull`: `npm run build && sudo systemctl restart pulso`.

## 4. NGINX en nodo0 (rol 4)

Desde la carpeta del repositorio, copia el archivo a nodo0 y corre el script:

```bash
scp -i TU_LLAVE deploy/nginx/pulso.conf deploy/nodo0_nginx.sh deploy/nodo0_ufw.sh root@79.143.88.200:/root/
ssh -o ServerAliveInterval=30 -i TU_LLAVE root@79.143.88.200
df -h /                                           # antes de nada: espacio libre
curl -s -m 5 http://IP_VPN_DE_LA_VM:8000/api/salud   # nodo0 llega a la VM por la VPN
bash /root/nodo0_nginx.sh TU_SUBDOMINIO IP_VPN_DE_LA_VM
```

El script respalda la configuración en `/root/nginx-respaldo-*.tgz`, desactiva el sitio que mandaba todo a `danielserv:11434`, activa `pulso`, corre `nginx -t` y recarga.

Si `nginx -t` dice que no encuentra el certificado, revisa el nombre con `certbot certificates` y ajusta las rutas `ssl_certificate` en `/etc/nginx/sites-available/pulso`. Si el certificado no existe: `certbot --nginx -d TU_SUBDOMINIO.duckdns.org`.

En nodo0 solo va NGINX: no instales Python, Node ni Ollama ahí.

## 5. Firewall de nodo0 (rol 4)

```bash
bash /root/nodo0_ufw.sh
```

Abre 22, 80, 443, 8080 (Headscale) y `tailscale0`, con un temporizador que apaga UFW en 10 minutos por si pierdes el acceso. Comprueba en otra terminal lo que indica el script y **cancela el temporizador** (`systemctl stop ufw-rescate3.timer`). En el panel de Clouding también deben estar abiertos 80, 443 y 8080.

## 6. Evidencias

Sigue [checklist_evidencias.md](checklist_evidencias.md).
