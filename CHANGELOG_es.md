# Registro de cambios

Los cambios notables de krunner-py-wtk. Las versiones publicadas, con sus
archivos zip, están en
[GitHub](https://github.com/nivaca/krunner-py-wtk/releases); el código
está también en [Codeberg](https://codeberg.org/nivaca/krunner-py-wtk).

## 1.0.1 — 2026-11-17

- Requiere Python 3.14 o posterior: con un Python más viejo, el runner y
  el diálogo de configuración se detienen con un mensaje. El README
  también lo dice.
- El zip `krunner-py-wtk-1.0.1.zip` contiene el programa completo, que se
  instala con `python3 install.py [--py-wtk FOLDER]`. Es la primera
  versión publicada.

## 1.0 — 2026-11-05

- Primera versión: py-wtk, el Wiktionary inglés, en KRunner (KDE Plasma
  6). Tras el prefijo `wtk`, una palabra da un resultado por cada
  categoría gramatical en cada lengua, con la línea del lema y las
  primeras definiciones; `@la` o `@Spanish` restringen las lenguas, y una
  palabra sin página da las páginas cuyo título empieza como ella.
- Enter abre la entrada en la ventana de py-wtk. Las acciones copian la
  entrada con todas sus definiciones, la abren en Wiktionary y abren la
  configuración.
- Wiktionary está en la red, así que el runner espera una breve pausa en
  la escritura y hace la consulta desde un hilo aparte; las páginas
  quedan en la caché en disco de py-wtk, y los últimos resultados, en
  memoria.
- Una ventana de configuración (`wtk ?`, el menú de aplicaciones o
  `python3 settings_dialog.py`) para el prefijo, las lenguas, el número
  de resultados y el número de definiciones, que se guardan en
  `~/.config/krunner-py-wtk/settings.ini`.
- `install.py` y `uninstall.py`, y pruebas que no necesitan la red.
- Esta versión no se etiquetó ni se publicó.
