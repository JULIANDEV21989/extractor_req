# Prompt para Análisis Manual en Claude Code / claude.ai

Si no usas la API de Anthropic, copia el contenido de `output/consolidado.md` y pégalo
en Claude Code o claude.ai con este prompt:

---

Analiza el siguiente contenido consolidado de un levantamiento de información
y genera un DOCUMENTO DE REQUERIMIENTOS TECNICOS completo y estructurado.

El documento DEBE contener estas secciones:

1. **Resumen Ejecutivo** - Qué se necesita construir y por qué
2. **Actores / Stakeholders** - Tabla con nombre, rol e interacción con el sistema
3. **Procesos de Negocio Detectados** - Flujos paso a paso tal como se describieron
4. **Requerimientos Funcionales** - Priorizados con MoSCoW, cada uno con ID, nombre y detalle
5. **Requerimientos No Funcionales** - Rendimiento, seguridad, acceso, integración
6. **Integraciones Requeridas** - Tabla con sistema, tipo, dirección y datos
7. **Restricciones y Dependencias** - Limitaciones técnicas, de negocio o presupuesto
8. **Riesgos Identificados** - Tabla con probabilidad, impacto y mitigación
9. **Alcance Propuesto** - In-scope (Fase 1) y Out-of-scope (futuras fases)
10. **Glosario** - Términos del dominio con definiciones claras
11. **Datos del Contexto de Negocio** - Empresas, direcciones, contactos mencionados

---

[PEGA AQUÍ EL CONTENIDO DE consolidado.md]
