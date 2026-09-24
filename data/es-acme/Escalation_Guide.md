# Escalation_Guide — Guía de Escalamiento de Soporte

_Fuente: Customer_Support/Escalation_Guide.pdf (AcmeTech Solutions Inc., traducido del corpus original en inglés en data/acme/). Documento CS-ESC-002 | Versión: v2.9 | Vigencia: 1 de noviembre de 2025 | Clasificación: Interno y Confidencial._

## 1. Niveles de escalamiento
Soporte opera un modelo de escalamiento de tres niveles:

- **Nivel 1 (Tier 1)**: Soporte de primera línea, atiende resolución general de problemas y preguntas de cuentas.
- **Nivel 2 (Tier 2)**: Soporte técnico, atiende problemas complejos del producto y resolución de API.
- **Nivel 3 (Tier 3)**: Guardia de Ingeniería (Engineering On-Call), atiende sospechas de bugs, problemas de datos e interrupciones.

## 2. Cuándo escalar
Los tickets deben escalarse a Nivel 2 si no se resuelven tras 2 horas para P1, 8 horas para P2 o 3 días hábiles para P3. Cualquier ticket con sospecha de pérdida de datos o problema de seguridad debe escalarse a Nivel 3 y al equipo de Seguridad de inmediato, sin importar la prioridad.

## 3. Proceso de escalamiento
Los escalamientos se envían con el botón «Escalar» (Escalate) en Zendesk, que automáticamente avisa por pager al responsable de guardia de Nivel 2 o Nivel 3 vía PagerDuty y crea un hilo de incidente vinculado en Slack.

## 4. Escalamiento ejecutivo
Las cuentas Enterprise estratégicas o en riesgo pueden escalarse al VP de Soporte al Cliente para atención a nivel ejecutivo. Los escalamientos ejecutivos se registran en la plataforma de Customer Success (Gainsight) y se revisan semanalmente en la reunión de Salud del Cliente.

## 5. Roles y responsabilidades
- **Agente de Nivel 1**: triage inicial y disparo del escalamiento.
- **Respondedor de Nivel 2**: resuelve problemas técnicos complejos; escala a Nivel 3 si se confirma un bug del producto.
- **Ingeniero de guardia de Nivel 3**: investiga sospechas de bugs, problemas de datos o interrupciones.
- **VP de Soporte al Cliente**: atiende escalamientos ejecutivos de cuentas estratégicas.

## 6. Requisitos de entrega (handoff) del escalamiento
Cada escalamiento debe incluir un resumen de entrega completo (descripción del problema, pasos de reproducción, impacto al cliente e intentos previos de resolución) antes de ser aceptado por el siguiente nivel, para evitar preguntas redundantes al cliente.

## 7. Escalamiento entre equipos
Los problemas que requieren participación de Ingeniería, Producto o Legal más allá del Nivel 3 estándar se canalizan como solicitud de Escalamiento Multifuncional (Cross-Functional) en Jira, revisada a diario por un responsable de triage rotativo de cada equipo.

## 8. Métricas e informes de escalamiento
El liderazgo de Soporte revisa mensualmente el volumen de escalamientos y las métricas de tiempo de resolución por nivel, usando los valores atípicos para identificar problemas recurrentes del producto que merecen una corrección permanente en vez de escalamientos manuales repetidos.

## 9. Prevención de la fatiga por escalamientos
Los respondedores de Nivel 2 y Nivel 3 tienen un límite máximo de carga de escalamientos de guardia por semana, monitoreado vía PagerDuty, con balanceo de carga hacia el resto del equipo de soporte técnico si alguien se acerca al límite.

## 10. Preguntas frecuentes
**P: ¿Puede un cliente pedir escalar directamente, saltando el Nivel 1?**
R: Los clientes Enterprise pueden pedir escalamiento directo por su canal dedicado de Slack, monitoreado por respondedores de Nivel 2.

**P: ¿Qué pasa si Nivel 2 y Nivel 3 no coinciden en si algo es un bug?**
R: El ingeniero de guardia de Nivel 3 tiene la determinación técnica final, con escalamiento al Engineering Manager si no se resuelve.

**P: ¿Los escalamientos se miden aparte de las métricas normales?**
R: Sí, los escalamientos llevan una etiqueta dedicada en Zendesk y aparecen en un tablero separado revisado semanalmente.

## 11. Documentos relacionados
Esta guía debe leerse junto con el SOP de Soporte y el SLA.

## 12. Historial de revisiones
- v2.9 (1 de noviembre de 2025): se agregaron las secciones de Escalamiento entre Equipos y Métricas.
- v2.5 (1 de mayo de 2025): se introdujo el requisito del resumen de entrega.
- v2.0 (1 de noviembre de 2024): se documentó el modelo de tres niveles.

## 13. Glosario
- **Tier 1/2/3**: la estructura de tres niveles desde soporte de primera línea hasta guardia de ingeniería.
- **Resumen de entrega (Handoff Summary)**: documentación obligatoria que acompaña cada escalamiento entre niveles.
- **Escalamiento Multifuncional**: escalamiento que requiere participación de Ingeniería, Producto o Legal.
- **Gainsight**: plataforma usada para seguir escalamientos ejecutivos de cuentas.

## 14. Apéndice: ejemplo de ruta de escalamiento
Un cliente Enterprise reporta fallas intermitentes de sincronización entre AcmeSync y su instancia de Salesforce. Nivel 1 confirma que no es un problema conocido de configuración y escala a Nivel 2 dentro de la ventana P1 de 2 horas. La investigación de Nivel 2 revela un probable bug en la lógica de reintentos de sincronización, lo que amerita escalar a la guardia de Ingeniería de Nivel 3, que confirma el bug y publica un hotfix fuera del tren de releases estándar dada la severidad P1 y el defecto confirmado.

## 15. Mejora continua
La Guía de Escalamiento se revisa trimestralmente contra los datos reales para decidir si los umbrales (p. ej., el disparador P1 de 2 horas a Nivel 2) siguen adecuados. Los cambios de umbrales los propone el VP de Soporte al Cliente y se aprueban junto con el liderazgo de Ingeniería, pues umbrales más estrictos aumentan la carga de guardia de Nivel 3.

## 16. Capacitación de nuevos respondedores
Los respondedores nuevos de Nivel 2 y Nivel 3 acompañan (shadowing) al menos 5 escalamientos reales antes de entrar solos a la rotación de guardia, y completan una lista de verificación que cubre el formato del resumen de entrega, PagerDuty y el proceso Multifuncional antes de entrar al cronograma.

## 17. Casos de estudio
**Caso 1 — Discrepancia de facturación:** un cliente Growth reporta un cobro por un plan del que ya se había dado de baja. Nivel 1 confirma la solicitud en el historial pero no tiene acceso al sistema de facturación, así que escala directo al equipo de Facturación (ruta especializada de Nivel 2) en vez de Soporte Técnico general; se resuelve dentro de 4 horas.

**Caso 2 — Sospecha de seguridad:** un cliente reporta que un ex-empleado aún parece tener acceso. Como toca seguridad de la cuenta, el ticket se escala de inmediato a Nivel 3 y al equipo de Seguridad según la Sección 2, sin importar la prioridad, y el acceso se revoca dentro de la hora.
