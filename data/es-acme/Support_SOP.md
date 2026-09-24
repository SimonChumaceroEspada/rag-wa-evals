# Support_SOP — Procedimientos Operativos Estándar de Soporte al Cliente

_Fuente: Customer_Support/Support_SOP.pdf (AcmeTech Solutions Inc., traducido del corpus original en inglés en data/acme/). Documento CS-SOP-001 | Versión: v4.5 | Vigencia: 1 de diciembre de 2025 | Clasificación: Interno y Confidencial._

## 1. Recepción de tickets
Los tickets de clientes se reciben por tres canales: chat en la aplicación, correo electrónico (support@acmetech.com) y el canal dedicado de Slack para clientes Enterprise. Todos los tickets se registran automáticamente en Zendesk y se les asigna un nivel de prioridad.

## 2. Niveles de prioridad
Los tickets se clasifican en cuatro niveles de prioridad:

- **P1 (Urgente)**: caída de la plataforma o imposibilidad total de usar la funcionalidad central.
- **P2 (Alta)**: funcionalidad principal rota sin solución alternativa (workaround).
- **P3 (Media)**: problema de funcionalidad con solución alternativa disponible.
- **P4 (Baja)**: pregunta general, error menor o solicitud de funcionalidad.

## 3. Proceso de atención de tickets
Los agentes de soporte deben acusar recibo de cada ticket nuevo dentro de la ventana de SLA aplicable (ver documento SLA), recopilar los detalles de reproducción y resolver el ticket directamente o escalarlo a Soporte de Nivel 2 o a Ingeniería siguiendo la Guía de Escalamiento.

## 4. Herramientas
Los agentes de soporte usan Zendesk para la gestión de tickets, Intercom para el chat en la aplicación y una base de conocimiento compartida en Notion para las guías internas de resolución. Las sesiones de pantalla compartida con clientes se hacen por Zoom cuando se trata de problemas complejos.

## 5. Estándares de comunicación con el cliente
Toda comunicación con el cliente debe ser profesional, empática y sin jerga técnica. Los agentes deben enviar una actualización de estado al menos una vez cada 24 horas en cualquier ticket P1 o P2 abierto, aunque no se haya alcanzado una resolución.

## 6. Incorporación y certificación de agentes
Los agentes nuevos completan un programa de certificación de 3 semanas que cubre capacitación del producto, herramientas (Zendesk, Intercom) y acompañamiento (shadowing) antes de atender tickets de forma independiente. Los agentes deben aprobar una evaluación de certificación con una nota de 85% o más antes de asumir tickets por cuenta propia.

## 7. Aseguramiento de calidad
Una muestra aleatoria del 5% de los tickets resueltos por agente al mes es revisada por un líder de QA con una rúbrica estandarizada que cubre precisión, tono y cumplimiento del SOP. Las notas por debajo de 80% activan una conversación de coaching con el líder del equipo del agente.

## 8. Medición de la satisfacción del cliente
Cada ticket resuelto dispara una encuesta CSAT; AcmeTech apunta a una nota CSAT global de 90% o más en todos los niveles, revisada semanalmente por el liderazgo de Soporte con desglose por equipo.

## 9. Mantenimiento de la base de conocimiento
Se espera que los agentes reporten artículos desactualizados o faltantes de la base de conocimiento cuando los encuentren; el equipo de Gestión del Conocimiento revisa y actualiza los artículos reportados dentro de 5 días hábiles.

## 10. Manejo de conversaciones difíciles
Los agentes están entrenados para calmar a clientes frustrados con el marco «Reconocer, Disculparse, Actuar» (Acknowledge, Apologize, Act) de AcmeTech, y pueden transferir una conversación a un líder de equipo si un cliente se vuelve abusivo, sin necesidad de mayor justificación.

## 11. Cobertura fuera de horario y fines de semana
Los clientes Enterprise tienen acceso a cobertura de soporte 24/7 para problemas P1 mediante un modelo follow-the-sun entre los centros de Austin, Dublín y Bengaluru. El soporte de los niveles Growth y Starter opera en horario comercial estándar (8 AM–8 PM hora local) de lunes a viernes.

## 12. Preguntas frecuentes
**P: ¿Qué pasa si un cliente pide un reembolso?**
R: Las solicitudes de reembolso se derivan al equipo de Facturación, que las evalúa según el Master Service Agreement; los agentes no pueden autorizar reembolsos por cuenta propia.

**P: ¿Cómo se atienden las solicitudes de soporte en otros idiomas?**
R: El soporte se brinda en inglés por defecto; el soporte en español y francés está disponible para clientes Enterprise mediante una cola designada.

**P: ¿Qué pasa si un ticket abarca varios departamentos (p. ej., facturación y técnico)?**
R: El agente que originó el ticket se mantiene como único punto de contacto y coordina internamente, en lugar de transferir al cliente entre departamentos.

## 13. Documentos relacionados
Este SOP debe leerse junto con la Guía de Escalamiento y el SLA.

## 14. Historial de revisiones
- v4.5 (1 de diciembre de 2025): se agregaron las secciones de Aseguramiento de Calidad y Cobertura Fuera de Horario.
- v4.0 (1 de junio de 2025): se introdujo el modelo de cobertura Enterprise 24/7 follow-the-sun.
- v3.5 (1 de diciembre de 2024): se agregó el marco de medición CSAT.

## 15. Glosario
- **Zendesk**: la plataforma de gestión de tickets de AcmeTech.
- **Intercom**: la herramienta de chat en vivo dentro de la aplicación.
- **CSAT**: nota de satisfacción del cliente, recolectada por encuesta posterior a la resolución.
- **Follow-the-Sun**: modelo de cobertura 24/7 que rota la responsabilidad entre centros globales.
- **Líder de QA**: rol responsable de revisar la calidad de los tickets contra la rúbrica de soporte.

## 16. Apéndice: ejemplo de atención de un ticket
Un cliente Growth reporta por el chat que un flujo no se dispara. El agente lo clasifica como P3 (problema con solución alternativa: disparo manual), recopila los detalles de reproducción y revisa el runbook interno en Notion por un caso conocido similar. Al no hallar coincidencia, escala a Nivel 2 dentro de la ventana P3 de 3 días hábiles, con un resumen completo de entrega para que no se pida al cliente repetir información.

## 17. Planificación de temporada y picos de volumen
Antes de períodos conocidos de alto volumen (p. ej., picos de uso de fin de trimestre, lanzamientos grandes), el liderazgo de Soporte pronostica el volumen con tendencias históricas y ajusta turnos y guardias. El personal temporal de refuerzo puede venir de agentes cros-entrenados de equipos adyacentes, coordinado con al menos 2 semanas de anticipación al pico previsto.

## 18. Accesibilidad de los canales de soporte
El chat en la aplicación y el correo de soporte están diseñados para cumplir las pautas WCAG 2.1 AA, y los clientes pueden pedir formatos alternativos (p. ej., soporte telefónico en vez de chat) en la configuración de su cuenta o con su CSM asignado en cuentas Enterprise.
