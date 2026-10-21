# Guion del video (2 a 3 minutos, máximo 3)

Grabar el celular con datos móviles (Wi-Fi apagado) en pantalla dividida o con grabación de pantalla del celular, más la pantalla de una PC para las terminales. Cada integrante narra una parte. Ensayar con cronómetro.

| Tiempo | Quién | En pantalla | Narración |
|---|---|---|---|
| 0:00–0:15 | Rol 1 | Pantalla de inicio en el celular; barra de estado sin Wi-Fi | «Pulso ayuda a quien busca su primer empleo: contesta una prueba de 8 aptitudes y le recomienda vacantes con IA. Estamos en un celular con datos móviles, entrando por Internet.» |
| 0:15–0:40 | Rol 2 | Aviso de uso, alias opcional, 3 o 4 preguntas (opción múltiple y escala), barra de progreso; adelantar el resto | «El aviso deja claro que es una orientación. Hay preguntas de opción múltiple y de escala, algunas invertidas, y no pedimos datos personales.» |
| 0:40–1:00 | Rol 3 | Resultados: gráfica de las 8 aptitudes y 5 vacantes con porcentaje | «El motor en Python calcula el perfil y la afinidad con una fórmula transparente: si la persona alcanza el mínimo es fortaleza, si no, es brecha.» |
| 1:00–1:30 | Rol 3 | Detalle de vacante → «¿Por qué?» → «Cargando» → «Generada con IA» y la lista de tools | «La IA no recibe los números: Ollama llama a la tool calcular_afinidad, que ejecuta nuestro motor, y a obtener_vacante. Si Ollama falla o cambia un porcentaje, sale la explicación automática.» |
| 1:30–1:50 | Rol 5 | Sección «Apoyo en la búsqueda de empleo», escribir «Estoy nervioso por mi entrevista» | «Usamos el dataset KB_limpio para un módulo de apoyo: busca la respuesta más parecida con TF-IDF. No se guarda ni afecta los resultados.» |
| 1:50–2:30 | Rol 4 | Terminal: `tailscale status` (nodo0 y VM online), `cat /etc/nginx/sites-available/pulso`, `nginx -t`, `curl https://…/api/salud` | «NGINX en nodo0 recibe el HTTPS y lo manda por la VPN de Headscale a nuestra VM, donde corren FastAPI y Ollama. Ollama solo escucha en localhost y el puerto 8000 solo se abre a la VPN.» |
| 2:30–2:45 | Rol 1 | Diagrama de red del README | «Este es el recorrido completo: Internet, DuckDNS, NGINX, el túnel y la VM.» |
| 2:45–2:55 | Rol 1 | Proyecto abierto en Antigravity con Claude Code en la terminal | «Lo desarrollamos en Antigravity con Claude Code, trabajando en SCRUM con ramas por rol.» |

**Antes de grabar:** VM encendida y `online`, `systemctl status pulso` activo, Ollama con el modelo cargado (haz una explicación de prueba para que no tarde en el video), terminales sin llaves ni tokens visibles.

**Respaldo:** si la red falla el día de la demo, usar este video y las capturas de `deploy/checklist_evidencias.md`.
