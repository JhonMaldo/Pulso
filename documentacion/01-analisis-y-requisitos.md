# Análisis y requisitos

## Punto de partida

El proyecto original era una landing de bienestar laboral con un tablero de datos ficticios y siete preguntas sobre condiciones laborales. No registraba empresas o vacantes y no tenía una evaluación de aptitudes. Se conservó React, Vite, el nombre Pulso y la dirección visual verde, adaptando la experiencia al proceso de orientación de candidatos. Se retiró `Workspace.jsx` y se reemplazaron los cálculos y pruebas de bienestar, que ya no correspondían al objetivo.

## Objetivo

Permitir que un responsable registre una empresa, defina sus puestos disponibles y sus prioridades. Una persona responde una encuesta y recibe fortalezas, áreas de mejora y una comparación de afinidad con las vacantes registradas.

## Requisitos implementados

| Requisito | Comportamiento |
| --- | --- |
| Empresa | Nombre obligatorio para acceder a la evaluación; sector opcional |
| Vacantes | Nombre, descripción y seis prioridades; plantillas iniciales |
| Validación | No admite vacantes duplicadas ni todas las prioridades en cero |
| Encuesta | Nombre o alias, consentimiento y 12 respuestas entre 1 y 5 |
| Navegación | Permite retroceder conservando respuestas |
| Resultados | Perfil, fortalezas, áreas de mejora y ranking explicable |
| Trazabilidad | Guarda una copia del perfil de la empresa y las vacantes usadas en cada reporte |
| Exportación | JSON y diálogo nativo de impresión para guardar PDF |
| Historial | Evaluaciones consultables en memoria durante la sesión |
| Dataset | Consulta de preguntas y respuestas en español e inglés con fuente visible y catálogo de 79 temas |
| Privacidad | Sin persistencia de candidatos en navegador o servidor; borrado de sesión |

## Alcance y siguientes etapas

Es un prototipo académico local. No incluye cuentas, roles de seguridad, enlaces para encuestados remotos, almacenamiento permanente ni un modelo entrenado. Los rótulos de empresa y candidato son pasos del flujo, no controles de acceso. Cualquier persona frente a la misma sesión puede consultar los reportes.

Para convertirlo en un sistema real se requieren definición de competencias por especialistas, validación del cuestionario, pruebas de accesibilidad y usabilidad, diseño de permisos y retención de datos, y una arquitectura multiusuario. La recomendación no debe convertirse por sí sola en una decisión de contratación.
