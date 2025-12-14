# 🚦 Alerta Nuñez

**Alerta Nuñez** es una aplicación de monitoreo de eventos para vecinos del barrio de Nuñez. Unifica información de diversas fuentes para alertar sobre cortes de tránsito y aglomeraciones.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white) ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

## 📌 ¿Qué monitorea?

La aplicación consolida en una sola lista unificada:
1.  **River Plate (Fútbol)**: Partidos en el Monumental (Data de ESPN).
2.  **Estadio Obras**: Recitales y eventos (Web oficial).
3.  **Monumental (Recitales)**: Shows internacionales (Oasis, Dua Lipa, etc.).

## 🚀 Funcionalidades

*   **Semáforo de Alertas**:
    *   🚨 **ROJO**: Evento en los próximos 3 días.
    *   🟢 **VERDE**: Sin eventos cercanos.
*   **Modo Nocturno Inteligente**: Los eventos se muestran como "HOY" hasta las 3 AM del día siguiente.
*   **Diseño Mobile-First**: Tarjetas response para fácil lectura en celulares.
*   **Fecha Simulada**: Capacidad de "viajar en el tiempo" para pruebas (Configurable).

## 🛠️ Instalación Local

1.  Clonar el repositorio:
    ```bash
    git clone https://github.com/TU_USUARIO/alerta-nunez.git
    cd alerta-nunez
    ```

2.  Instalar dependencias:
    ```bash
    pip install -r requirements.txt
    ```

3.  Ejecutar la app:
    ```bash
    streamlit run app.py
    ```

## ⚙️ Configuración (`config.py`)

Puedes ajustar el comportamiento editando `config.py`:

```python
# FAKE_TODAY = False  (Para usar fecha real)
# FAKE_TODAY = datetime(2025, 9, 1) (Para simular una fecha)
```

## ☁️ Despliegue

Esta app está lista para ser desplegada en **Streamlit Cloud**.
Solo conecta tu repositorio y apunta a `app.py`.

---
*Hecho con ❤️ para los vecinos de Nuñez.*
