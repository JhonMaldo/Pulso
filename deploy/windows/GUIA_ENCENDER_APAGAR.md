# Cómo encender y apagar Pulso

Pulso corre en tu PC (Windows + la VM `ubuntu`) y se publica en Internet por `nodo0`, en la nube. Si tu PC está apagada, la página https://mentalhealth-app.duckdns.org muestra **502 o 504** (NGINX funciona, pero no encuentra la app). No se borra nada: al encender de nuevo, todo vuelve.

Los scripts están en `Pulso\deploy\windows\`:

| Archivo | Para qué |
|---|---|
| `levantar_pulso.bat` | Doble clic para encender todo y comprobar que funcione |
| `apagar_pulso.bat` | Doble clic para apagar todo en orden antes de apagar la PC |
| `levantar_pulso.ps1` y `apagar_pulso.ps1` | El código de cada script (no hace falta abrirlos) |

## Qué partes hay

| Parte | Dónde corre | ¿Arranca sola? |
|---|---|---|
| NGINX, HTTPS y Headscale | `nodo0`, en la nube | Sí, siempre encendido |
| Pulso (pantallas y API) | VM `ubuntu` en tu PC | Sí, cuando la VM enciende (servicio `pulso`) |
| VPN de la VM | VM `ubuntu` | Sí, cuando la VM enciende |
| La VM `ubuntu` | VirtualBox, en tu PC | **No**: la enciende el script |
| Ollama (la IA) | Windows, en tu PC | Normalmente sí al iniciar sesión; el script lo comprueba |

## Encender todo

### Antes de empezar

1. Conecta el disco donde está la VM. Debe aparecer en el Explorador como **`D:`** (la VM está en `D:\VirtualBox VMs\ubuntu`).
2. Cierra lo que no uses, sobre todo navegadores con muchas pestañas, Spotify y juegos. La PC tiene 7 GB de RAM y la VM más la IA necesitan unos 3.5 GB libres.

### Paso a paso

1. Abre la carpeta `Pulso\deploy\windows`.
2. Haz **doble clic en `levantar_pulso.bat`**. Se abre una ventana negra.
3. Si Windows pregunta «¿Quieres permitir que esta aplicación haga cambios?», responde **Sí**. Es para detener MySQL y PostgreSQL, que ocupan memoria. Solo aparece si están encendidas.
4. Espera de 3 a 5 minutos. Verás 7 pasos:

   | Paso | Qué hace | Qué debes ver |
   |---|---|---|
   | 1 | Revisa que el disco `D:` esté conectado | `OK Disco conectado` |
   | 2 | Detiene MySQL y PostgreSQL | `OK Bases de datos detenidas` o `No hay bases de datos encendidas` |
   | 3 | Mide la memoria libre | `OK ... MB disponibles`. Si falta, te muestra qué programas ocupan más: ciérralos y presiona Enter, o escribe `S` para seguir así |
   | 4 | Abre Ollama (la IA) | `OK Ollama 0.40.8 responde (solo en esta PC)` |
   | 5 | Enciende la VM sin ventana | `OK VM encendida (sin ventana)` |
   | 6 | Espera a que la página responda en Internet | Puntos `.....` y luego `OK https://mentalhealth-app.duckdns.org responde` |
   | 7 | Espera 60 s y pide una explicación real a la IA | `OK La IA respondió en ... s usando calcular_afinidad(...)` |

5. Cuando diga **`=== Listo ===`**, presiona Enter para cerrar la ventana y abre https://mentalhealth-app.duckdns.org.

El paso 7 deja el modelo cargado, así que el primer «¿Por qué?» en la página ya no tarda de más.

### Comprobar a mano (opcional)

En PowerShell:

```powershell
curl.exe https://mentalhealth-app.duckdns.org/api/salud/ollama
```

Si responde `{"ok":true,"modelo":"granite4.2:3b",...}`, la página y la IA están arriba.

## Apagar todo

Hazlo antes de apagar la PC o de desconectar el disco `D:`.

1. Abre la carpeta `Pulso\deploy\windows`.
2. Haz **doble clic en `apagar_pulso.bat`**.
3. Espera de 30 s a 2 minutos. Verás:
   - `[1/2] Máquina virtual`: apaga Linux de forma normal, como presionar el botón de encendido. Si en 2 minutos no termina, fuerza el apagado.
   - `[2/2] Ollama (IA)`: cierra Ollama para liberar memoria.
4. Cuando diga **`=== Listo ===`**, presiona Enter. Ya puedes apagar la PC o desconectar el disco.

Mientras todo esté apagado, la página mostrará 502 o 504. `nodo0` sigue encendido en la nube; no hay que hacer nada ahí.

> La VM está configurada con **1 núcleo y 1.5 GB de RAM**. No la subas a 2 o más núcleos: en esta PC VirtualBox corre encima de Hyper-V y, con 2 núcleos, Linux se quedó sin CPU (mensajes `rcu_preempt ... starved` y `soft lockup`) y la página dio 504. Con 1 núcleo pasó una prueba de 4 explicaciones con IA seguidas sin fallos.

> No uses «Guardar el estado de la máquina» en VirtualBox para apagar la VM. Cuando se reanudó después de dos semanas guardada, la VM se colgó. El script la apaga de forma normal.

## Si algo falla

| Lo que ves | Causa probable | Qué hacer |
|---|---|---|
| `XX No encuentro D:\VirtualBox VMs\ubuntu\ubuntu.vbox` | El disco no está conectado o tomó otra letra | Conéctalo. Si aparece con otra letra, cámbiala a `D:` en «Administración de discos» de Windows |
| El paso 3 dice que hay poca memoria | Hay programas abiertos que ocupan RAM | Cierra los que muestra la lista y presiona Enter para volver a medir |
| `XX Ollama no responde` | Ollama no pudo arrancar | Abre «Ollama» desde el menú Inicio, espera 10 s y vuelve a correr `levantar_pulso.bat` |
| `XX La URL no responde` tras 4 minutos | La VM se trabó al arrancar (pasa cuando falta memoria) | Corre `apagar_pulso.bat`, cierra programas y vuelve a correr `levantar_pulso.bat` |
| `!! Respondió la explicación automática` | La IA tardó más de 3 minutos | La página funciona igual, con la explicación de plantilla. Cierra programas y prueba «¿Por qué?» otra vez |
| En VirtualBox la VM muestra `rcu_preempt ... starved` o `soft lockup` | La VM se quedó sin CPU (Hyper-V + poca RAM) | Revisa que tenga 1 núcleo (Configuración → Sistema → Procesador), cierra programas y corre `apagar_pulso.bat` y luego `levantar_pulso.bat` |
| La página muestra 502 o 504 | La VM está apagada o trabada | Corre `levantar_pulso.bat`. Si dice que la VM ya estaba encendida y aun así falla, corre `apagar_pulso.bat` y luego `levantar_pulso.bat` |
| Windows no deja abrir el `.bat` | Bloqueo de seguridad de archivos descargados | Clic derecho en el archivo → Propiedades → marca «Desbloquear» → Aceptar |

## Encender a mano (si no quieres usar el script)

1. En PowerShell como administrador, detén las bases de datos:
   ```powershell
   Stop-Service mysql, MySQL80, postgresql-x64-13, postgresql-x64-17 -Force
   ```
2. Abre **Ollama** desde el menú Inicio (aparece un ícono junto al reloj).
3. Abre **VirtualBox**, selecciona `ubuntu` y haz clic en **Iniciar**. No hace falta iniciar sesión en Linux: Pulso arranca solo.
4. Espera 2 minutos y abre https://mentalhealth-app.duckdns.org.

## Antes de la demo

- [ ] Disco `D:` conectado y PC enchufada a la corriente (que no se suspenda)
- [ ] Navegadores y programas pesados cerrados
- [ ] `levantar_pulso.bat` terminó con `La IA respondió en ... s`
- [ ] Abrir la página desde un celular **con datos móviles** (sin Wi-Fi) y probar «¿Por qué?» una vez
- [ ] Desactivar la suspensión de Windows durante la presentación (Configuración → Sistema → Energía → «Nunca»)
