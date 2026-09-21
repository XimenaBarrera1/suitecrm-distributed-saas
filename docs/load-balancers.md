# Balanceadores por Cliente - SuiteCRM Distributed SaaS

## 1. Objetivo

Este documento describe la implementación de los balanceadores de carga por cliente dentro del proyecto `suitecrm-distributed-saas`.

El objetivo es que cada cliente tenga su propio balanceador, encargado de distribuir tráfico entre dos nodos de aplicación.

En esta fase se implementaron balanceadores con HAProxy y nodos mock con Nginx para validar el funcionamiento antes de reemplazarlos por contenedores reales de SuiteCRM.

---

## 2. Relación con la arquitectura

El tráfico entra al sistema por los dominios:

- `www.clientea.com`
- `www.clienteb.com`

Ambos dominios son resueltos por el DNS hacia:

```text
192.168.0.1
