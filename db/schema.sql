---
--- Tabla de datos
---
CREATE TABLE IF NOT EXISTS datos
  (id_sensor  INTEGER PRIMARY KEY,
  temperatura TEXT,
  humedad     TEXT,
  VOD         TEXT,
  fecha       DateTime NOT NULL,
  FOREIGN KEY(id_sensor) REFERENCES sensores(id_sensor));


---
--- Tabla de sensores
---
CREATE TABLE IF NOT EXISTS sensores
   (id_sensor   INTEGER PRIMARY KEY AUTOINCREMENT,
    id_tipo     INTEGER,
    nombre      TEXT,
    descripcion TEXT,
    FOREIGN KEY(id_tipo) REFERENCES sensores(id_tipo));
  
    
---
--- Tabla tipo de sensores
--- 
--- DHT11, DHT22, CCS811, etc
---
CREATE TABLE IF NOT EXISTS tipo_sensores
   (id_tipo     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT,
    descripcion TEXT
   );
