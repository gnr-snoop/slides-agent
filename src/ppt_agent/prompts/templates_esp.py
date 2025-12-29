"""Plantillas de prompts para el Agente PPT.

Estos prompts guían al LLM en el análisis de documentos y la generación de planes de presentación.
"""

SLIDE_TYPES_DESCRIPTION = """
Tipos de diapositivas disponibles:

1. **title** - Diapositiva de título (primera diapositiva)
   - title: Título principal de la presentación
   - subtitle: Subtítulo opcional
   - author: Nombre del presentador/empresa
   - date: Fecha de la presentación

2. **agenda** - Diapositiva de agenda/índice
   - title: Generalmente "Agenda" o "Contenido"
   - items: Lista de puntos de la agenda

3. **content** - Diapositiva de contenido general
   - title: Título de la diapositiva
   - body: Contenido principal (puede incluir viñetas)
   - image_suggestion: Sugerencia opcional de imagen/diagrama

4. **key_points** - Resalta puntos importantes
   - title: Título de la diapositiva
   - points: Lista de puntos, cada uno con 'title' y 'description'

5. **section_header** - Separador de sección
   - title: Título de la sección
   - subtitle: Subtítulo opcional

6. **closing** - Diapositiva final
   - title: Generalmente "Gracias" o "Próximos Pasos"
   - message: Llamada a la acción o mensaje de cierre
"""

DOCUMENT_ANALYSIS_PROMPT = """Eres un experto analista de negocios y consultor de presentaciones.

Analiza el siguiente documento de propuesta técnica y económica y extrae la información clave que ayudará a crear una presentación efectiva.

## Documento a Analizar:
{document}

## Tu Tarea:
Analiza el documento y proporciona un análisis estructurado que incluya:

1. **Tema Principal**: ¿De qué trata el tema/propuesta central?
2. **Secciones Clave**: ¿Cuáles son las principales secciones o temas del documento?
3. **Aspectos Técnicos Destacados**: ¿Qué aspectos técnicos deben enfatizarse?
4. **Aspectos Económicos Destacados**: ¿Qué beneficios o costos de negocio/económicos deben resaltarse?
5. **Audiencia Objetivo**: ¿Quién es la audiencia prevista para esta presentación?
6. **Tono Sugerido**: ¿Qué tono sería más apropiado (formal, persuasivo, técnico, etc.)?

## Formato de Salida:
Responde con un objeto JSON con esta estructura:
```json
{{
  "main_topic": "string",
  "key_sections": ["string", ...],
  "technical_highlights": ["string", ...],
  "economic_highlights": ["string", ...],
  "target_audience": "string",
  "suggested_tone": "string"
}}
```
"""

PLAN_GENERATION_PROMPT = """Eres un experto diseñador de presentaciones especializado en propuestas técnicas y de negocios.

Basándote en el análisis del documento a continuación, crea un plan de presentación completo.

## Análisis del Documento:
{analysis}

## Documento Original:
{document}

## Tipos de Diapositivas Disponibles:
{slide_types}

## Tu Tarea:
Crea un plan de presentación que:
1. Comience con una diapositiva de título atractiva
2. Incluya una agenda/resumen
3. Cubra todos los puntos técnicos clave
4. Destaque los beneficios económicos
5. Termine con una clara llamada a la acción o próximos pasos

## Directrices:
- Apunta a 10-15 diapositivas para una presentación de 30 minutos
- Usa tipos de diapositivas apropiados para diferentes contenidos
- Incluye notas del orador para cada diapositiva
- Haz que los títulos sean concisos e impactantes
- Asegura un flujo lógico entre diapositivas
- Equilibra la profundidad técnica con el valor de negocio

## Formato de Salida:
Responde con un objeto JSON con esta estructura:
```json
{{
  "title": "Título de la presentación",
  "description": "Breve descripción",
  "target_audience": "Audiencia prevista",
  "estimated_duration_minutes": 30,
  "slides": [
    {{
      "slide_type": "title",
      "title": "Título Principal",
      "subtitle": "Subtítulo",
      "author": "Autor",
      "date": "Fecha",
      "speaker_notes": "Notas"
    }},
    {{
      "slide_type": "agenda",
      "title": "Agenda",
      "items": ["Punto 1", "Punto 2"],
      "speaker_notes": "Notas"
    }},
    {{
      "slide_type": "content",
      "title": "Título de la Diapositiva",
      "body": "Texto del contenido",
      "image_suggestion": "",
      "speaker_notes": "Notas"
    }},
    ... más diapositivas
  ]
}}
```

Tipos de diapositivas: title, agenda, content, key_points, section_header, closing

Genera el plan de presentación completo con todos los detalles de las diapositivas.
"""

PLAN_REVISION_PROMPT = """Eres un experto diseñador de presentaciones que ayuda a revisar un plan de presentación basándose en los comentarios del usuario.

## Plan de Presentación Actual:
{current_plan}

## Comentarios del Usuario:
{feedback}

## Documento Original:
{document}

## Tipos de Diapositivas Disponibles:
{slide_types}

## Tu Tarea:
Revisa el plan de presentación basándote en los comentarios del usuario. Asegúrate de:
1. Abordar todos los puntos mencionados en los comentarios
2. Mantener la coherencia general de la presentación
3. Mantener un número razonable de diapositivas (10-20)
4. Preservar los aspectos que el usuario no mencionó (probablemente está satisfecho con esos)

## Formato de Salida:
Responde con el plan de presentación revisado completo como un objeto JSON con la misma estructura que el plan original:
```json
{{
  "title": "Título de la presentación",
  "description": "Breve descripción",
  "target_audience": "Audiencia prevista",
  "estimated_duration_minutes": 30,
  "slides": [ ... objetos de diapositivas ... ]
}}
```

Genera el plan de presentación revisado completo en formato JSON.
"""


REVIEW_PLAN_TEMPLATE = """
## Revisión del Plan de Presentación

{summary}

## Contenido Detallado de las Diapositivas:
{detailed_view}

---
**Por favor, revisa el plan anterior y responde con una de las siguientes opciones:**
- **"aprobar"** - Aceptar este plan y continuar
- **"rechazar"** - Rechazar este plan por completo
- **Tus comentarios** - Proporcionar cambios específicos que te gustaría hacer

Revisiones restantes: {remaining_revisions}
"""