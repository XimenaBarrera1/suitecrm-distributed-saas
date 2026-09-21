# MariaDB Galera Cluster - SuiteCRM Distributed SaaS

## Responsable
Lizeth

## Objetivo del componente
Implementar un clúster de base de datos MariaDB Galera para la arquitectura distribuida de SuiteCRM SaaS multi-instancia.

Este componente permitirá tener replicación de datos entre varios nodos de base de datos, alta disponibilidad y separación lógica de bases de datos por cliente.

## Relación con la arquitectura general

El clúster de base de datos estará ubicado en la red interna de la arquitectura:

- Red interna: `192.168.2.0/24`
- Balanceador de base de datos: `db-lb`
- Nodos del clúster: `db-node-1`, `db-node-2`, `db-node-3`

La base de datos no estará expuesta directamente al cliente externo ni a la DMZ. Solo los servicios internos que lo requieran podrán comunicarse con ella.

## Diseño propuesto

| Servicio | IP | Función |
|---|---|---|
| `db-lb` | `192.168.2.1` | Balanceador de conexiones hacia el clúster |
| `db-node-1` | `192.168.2.11` | Nodo 1 de MariaDB Galera |
| `db-node-2` | `192.168.2.12` | Nodo 2 de MariaDB Galera |
| `db-node-3` | `192.168.2.13` | Nodo 3 de MariaDB Galera |

## Motor seleccionado

Se selecciona MariaDB 10.11 porque es compatible con SuiteCRM Community 7.15.1 y permite implementar un clúster Galera para replicación.

## Tipo de clúster seleccionado

Se implementará un clúster maestro-maestro, también conocido como multi-master o multi-primary.

Esta decisión se toma porque MariaDB Galera Cluster está diseñado para replicación entre varios nodos activos. A diferencia de una arquitectura maestro-esclavo tradicional, donde un único nodo concentra las escrituras, Galera permite mantener los datos sincronizados entre los nodos del clúster.

## Diferencia entre replicación y balanceo

Galera se encargará de la replicación de datos entre los nodos del clúster.

HAProxy se encargará del balanceo de conexiones hacia los nodos MariaDB.

Esto significa que:

- Galera mantiene los mismos datos en los nodos.
- HAProxy sirve como punto único de acceso para las aplicaciones.
- Replicación y balanceo son responsabilidades diferentes.

## Bases de datos por cliente

Aunque el clúster es compartido, cada cliente tendrá su propia base de datos lógica.

Bases iniciales:

- `suitecrm_clientea`
- `suitecrm_clienteb`

Esto permite separar los datos de cada cliente dentro del mismo clúster.

## Pruebas planeadas

### 1. Verificar tamaño del clúster

Se validará que el clúster tenga tres nodos activos mediante:

```sql
SHOW STATUS LIKE 'wsrep_cluster_size';
