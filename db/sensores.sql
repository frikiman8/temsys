#
# Lineas con indisponibilidad activa(tiempo = 0 no cerradas)
#
.mode column
.header on
SELECT id_sensor as ID, id_tipo as Tipo, nombre as Nombre, descripcion as Descripcion FROM sensores;
