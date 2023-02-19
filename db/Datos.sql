#
# Lineas
#
.mode column
.header on
SELECT S.nombre as nombre, D.temperatura as temperatura, D.humedad as humedad, D.fecha as fecha FROM sensores S, Datos D WHERE S.id_sensor = D.id_sensor;
