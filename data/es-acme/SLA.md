# SLA — Acuerdo de Nivel de Servicio

_Fuente: Customer_Support/SLA.pdf (AcmeTech Solutions Inc., traducido del corpus original en inglés en data/acme/). Documento CS-SLA-003 | Versión: v3.0 | Vigencia: 1 de enero de 2026 | Clasificación: Interno y Confidencial._

## 1. SLA de disponibilidad (uptime) de la plataforma
AcmeTech garantiza 99.9% de uptime mensual para clientes del nivel Enterprise y 99.5% para clientes del nivel Growth, medido contra la disponibilidad central de la API y la aplicación. El nivel Starter no incluye garantía formal de uptime.

## 2. SLA de tiempos de respuesta de soporte
Tiempos de respuesta objetivo por nivel y prioridad:

- **Enterprise**: P1: 1 hora, P2: 4 horas, P3: 1 día hábil, P4: 2 días hábiles.
- **Growth**: P1: 4 horas, P2: 8 horas, P3: 2 días hábiles, P4: 4 días hábiles.
- **Starter**: P1: 8 horas, P2: 1 día hábil, P3: 3 días hábiles, P4: 5 días hábiles.

## 3. Objetivos de tiempo de resolución
Aunque el tiempo de resolución varía según la complejidad, AcmeTech apunta a resolver el 90% de los problemas P1 dentro de 4 horas y el 90% de los P2 dentro de 1 día hábil para clientes Enterprise.

## 4. Créditos de servicio
Si el uptime mensual cae por debajo del umbral garantizado, los clientes Enterprise pueden recibir créditos de servicio de 5% a 30% de su tarifa de suscripción mensual, aplicados automáticamente a la factura del mes siguiente, según su Master Service Agreement.

## 5. Exclusiones del SLA
El SLA de uptime no aplica a caídas causadas por:

- Ventanas de mantenimiento programado comunicadas con al menos 48 horas de anticipación.
- Eventos de fuerza mayor fuera del control razonable de AcmeTech.
- Problemas causados por el cliente, incluyendo mala configuración o exceder los límites de tasa (rate limits) documentados.
- Caídas de servicios de terceros fuera de la infraestructura directa de AcmeTech (p. ej., que la instancia de Salesforce del propio cliente esté caída).

## 6. Metodología de medición
El uptime se mide con monitoreo sintético automatizado contra la API central y los endpoints de la aplicación a intervalos de 1 minuto desde múltiples ubicaciones geográficas; el porcentaje mensual se calcula como (minutos totales − minutos de caída) / minutos totales.

## 7. Cómo solicitar un crédito de servicio
Los clientes deben enviar la solicitud de crédito dentro de 30 días del mes en que no se cumplió el SLA, con evidencia de respaldo si la tienen; AcmeTech verifica contra sus datos internos de monitoreo antes de emitir el crédito.

## 8. Ventanas de disponibilidad de soporte
El horario estándar es de 8 AM a 8 PM en el horario comercial regional del cliente para los niveles Growth y Starter; los clientes Enterprise reciben cobertura 24/7 para problemas P1 y P2 según el SOP de Soporte.

## 9. Avisos de mantenimiento programado
El mantenimiento que pueda afectar la disponibilidad se anuncia en la página de estado y por correo a los administradores de cuenta con al menos 48 horas de anticipación, programado en ventanas de bajo tráfico según patrones históricos por región.

## 10. Revisión y actualización del SLA
Este SLA se revisa anualmente y puede actualizarse con 60 días de aviso a los clientes existentes; los compromisos contractuales firmados en un Master Service Agreement prevalecen sobre este documento general donde haya conflicto.

## 11. Preguntas frecuentes
**P: ¿El SLA cubre específicamente la app móvil AcmeFlow?**
R: El SLA cubre la disponibilidad central de la API y la aplicación web; los problemas de la app móvil se atienden como tickets estándar, no bajo el SLA de uptime.

**P: ¿Qué pasa si una caída afecta solo una región de AWS?**
R: El uptime se mide globalmente en la región asignada combinado con el failover automático, así que un failover exitoso dentro del RTO no cuenta como caída total para el SLA.

**P: ¿Los créditos pueden pagarse en efectivo en vez de aplicarse a la factura?**
R: No, los créditos se aplican solo como descuento a futuras tarifas de suscripción, según los términos estándar.

## 12. Documentos relacionados
Este SLA debe leerse junto con el SOP de Soporte, la Guía de Escalamiento y el Master Service Agreement del cliente.

## 13. Historial de revisiones
- v3.0 (1 de enero de 2026): se agregaron las secciones de Exclusiones y Metodología de Medición.
- v2.6 (1 de julio de 2025): la ventana de solicitud de créditos se fijó en 30 días.
- v2.0 (1 de enero de 2025): se introdujeron garantías de uptime por niveles.

## 14. Glosario
- **Uptime**: porcentaje de tiempo en que los servicios centrales están disponibles, medido por monitoreo sintético.
- **Crédito de servicio**: reembolso parcial de la suscripción cuando no se cumple un SLA garantizado.
- **Monitoreo sintético**: verificaciones automatizadas que simulan solicitudes reales para medir disponibilidad.
- **Master Service Agreement (MSA)**: contrato marco que puede incluir términos SLA específicos del cliente.

## 15. Apéndice: ejemplo de cálculo de crédito
Si el uptime mensual de un cliente Enterprise se mide en 99.5% contra una garantía de 99.9%, puede calificar para un crédito según el esquema de su Master Service Agreement (típicamente un porcentaje de la tarifa mensual escalado al tamaño del incumplimiento). El cliente solicita dentro de 30 días del mes afectado y AcmeTech verifica contra el monitoreo interno antes de emitir el crédito como ajuste a la siguiente factura.

## 16. Negociación de SLA personalizado Enterprise
Cuentas Enterprise estratégicas selectas pueden negociar términos personalizados (p. ej., mayor garantía de uptime o respuestas más rápidas) como parte de su Master Service Agreement, sujetos a revisión del VP de Soporte al Cliente y Legal. Esos términos prevalecen sobre este SLA general para ese cliente y se registran en la plataforma de Customer Success.

## 17. Ejemplo ilustrativo de línea de tiempo SLA
Un cliente Enterprise abre un ticket P2 a las 2:00 PM por una integración rota. Según el SLA, AcmeTech debe responder dentro de 4 horas, así que la primera respuesta sustantiva vence a las 6:00 PM. El equipo resuelve la causa raíz al siguiente día hábil, dentro del objetivo del 90% de P2 en 1 día hábil. Como se cumplió el SLA de respuesta y se resolvió rápido, no aplica crédito; si la primera respuesta hubiera pasado las 6:00 PM, el cliente podría haber solicitado un crédito según la Sección 7.
