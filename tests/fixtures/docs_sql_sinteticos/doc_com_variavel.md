# IXX — Indicador de exemplo (fixture sintética, não é um indicador real)

```python
SQL_I99 = """
WITH parametros AS (
    SELECT CAST('{ini}' AS DATE) AS data_inicio,
           CAST('{fim}' AS DATE) AS data_fim
)
SELECT u.id
FROM unidades u
JOIN planos_entregas pe ON pe.unidade_id = u.id
WHERE date(pe.data_inicio) >= parametros.data_inicio
  AND JSON_UNQUOTE(u.nome) IS NOT NULL
"""
```
