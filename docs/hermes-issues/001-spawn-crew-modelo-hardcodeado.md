# spawn_crew usa modelo hardcodeado `openai/deepseek-v4-flash` que no existe

- **Fecha**: 2026-05-03
- **Reportado por**: hermes-ghost
- **Componente**: spawn_crew
- **Severidad**: blocker

## Descripción

La tool `spawn_crew` (que lanza sub-crews de CrewAI) internamente usa el modelo
`openai/deepseek-v4-flash` hardcodeado. Este modelo no existe en OpenAI ni en
OpenCode (el proveedor configurado del usuario). Como resultado, cualquier
llamada a `spawn_crew` falla con error de autenticación/modelo no encontrado.

## Pasos para reproducir

1. Tener OpenCode configurado como proveedor de LLM (API key con last4 `s44f`).
2. Llamar `spawn_crew(template="research", task="cualquier cosa")`.
3. El crew falla porque intenta usar `openai/deepseek-v4-flash`.

## Comportamiento esperado

`spawn_crew` debería usar el modelo configurado por el usuario (ej. el de OpenCode)
o al menos un modelo válido como `gpt-4o-mini` que sí existe en OpenAI.

## Comportamiento actual

Error: el modelo `openai/deepseek-v4-flash` no es reconocido por el proveedor.

## Notas / Workaround

- Ejecutar crews manualmente desde el sandbox funciona bien (probado con
  `gpt-4o-mini` y OpenCode).
- Se puede hacer un wrapper que reciba `model_name` como parámetro o que
  lea `OPENAI_MODEL_NAME` del entorno.
- CrewAI instalado es la versión más reciente en PyPI.
