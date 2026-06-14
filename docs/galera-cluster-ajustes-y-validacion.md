# Ajustes de configuración y validación del clúster Galera

**Responsable:** Ximena

---

## Problema identificado

La configuración original usaba un único archivo genérico para los tres nodos:
database/galera/conf/galera.cnf
Ese archivo no tenía `wsrep_node_name` ni `wsrep_node_address`, por lo que todos los nodos arrancaban sin identidad propia dentro del clúster. Esto causaba que ningún nodo pudiera establecer una vista primaria (`Primary view`) y todos terminaban en estado `NON-PRIMARY`, abortando repetidamente.

---

## Solución implementada

Se crearon tres archivos de configuración independientes, uno por nodo:

- `database/galera/conf/galera-node1.cnf`
- `database/galera/conf/galera-node2.cnf`
- `database/galera/conf/galera-node3.cnf`

Cada archivo define la identidad específica del nodo:

```ini
wsrep_node_name=db-node-1
wsrep_node_address=192.168.2.11
```

Se modificó `docker-compose.yml` para que cada contenedor monte su archivo correspondiente:

```yaml
db-node-1:
  volumes:
    - ./database/galera/conf/galera-node1.cnf:/etc/mysql/conf.d/galera.cnf:ro
```

El archivo original `galera.cnf` fue eliminado de la configuración activa.

---

## Validaciones realizadas

### Prueba 1 — Estado del clúster

```sql
SHOW STATUS LIKE 'wsrep_cluster_size';
SHOW STATUS LIKE 'wsrep_cluster_status';
SHOW STATUS LIKE 'wsrep_ready';
```

**Resultado:**
- `wsrep_cluster_size = 3`
- `wsrep_cluster_status = Primary`
- `wsrep_ready = ON`

### Prueba 2 — Replicación desde nodo 1

Se creó una base de datos desde `db-node-1`:

```sql
CREATE DATABASE prueba_galera;
```

Verificación en `db-node-2` y `db-node-3`: base de datos visible en ambos nodos.

### Prueba 3 — Escritura desde nodo secundario

Se creó una base de datos desde `db-node-2`:

```sql
CREATE DATABASE prueba_desde_nodo2;
```

Verificación en `db-node-1` y `db-node-3`: base de datos visible en ambos nodos.

### Prueba 4 — Tolerancia a fallos

Se detuvo `db-node-2`:

```bash
docker compose stop db-node-2
```

El clúster permaneció operativo con `wsrep_cluster_size = 2`.

Se creó una base de datos durante la falla:

```sql
CREATE DATABASE prueba_fallo_nodo2;
```

Resultado: visible en `db-node-1` y `db-node-3`.

### Prueba 5 — Reincorporación automática

Se reinició `db-node-2`:

```bash
docker compose up -d db-node-2
```

Verificación tras sincronización:

```sql
SHOW STATUS LIKE 'wsrep_local_state_comment'; -- Synced
SHOW STATUS LIKE 'wsrep_ready';               -- ON
SHOW STATUS LIKE 'wsrep_cluster_status';      -- Primary
SHOW STATUS LIKE 'wsrep_cluster_size';        -- 3
```

La base de datos `prueba_fallo_nodo2` fue recuperada automáticamente por el nodo al reincorporarse.

### Prueba 6 — Replicación desde nodo 3

Se creó una base de datos desde `db-node-3`:

```sql
CREATE DATABASE prueba_final_galera;
```

Verificación en `db-node-1` y `db-node-2`: base de datos visible en ambos nodos.

---

## Conclusión

- El clúster Galera opera correctamente con 3 nodos activos.
- La replicación maestro-maestro funciona desde cualquier nodo.
- El clúster mantiene disponibilidad ante la caída de un nodo.
- Los nodos recuperan automáticamente los cambios al reincorporarse.