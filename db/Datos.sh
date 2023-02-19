cat Datos.sql | grep -v "^#" | sqlite3 sensoresTHV.db
