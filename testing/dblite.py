#! /usr/bin/env python
# -*- coding:utf-8 -*-

#"""
#dblite.py

#class to interface with a sqlite database

#for python 2.4 or earlier download pysqlite from http://pysqlite.org/

#"""

#__author__ = "Antonio Delgado Rodriguez <adelgado@ree.es"
#__license__ = "GNU General Public License version 3"
#__date__ = "07/03/2016"
#__version__ = "0.1"

#try:

import os

import csv
import glob
import sys

    #from pysqlite2 import dbapi2 as sqlite3 # if using python 2.4
import sqlite3  # if using python 2.5 or greater

#except ImportError:
    # Checks the installation of the necessary python modules
#    print((os.linesep * 2).join(["An error found importing one module:",
#    str(sys.exc_info()[1]), "You need to install it", "Stopping..."]))
#    sys.exit(-2)



class SqliteDatabase(object):
    """ class to handle all python communication with a sqlite database file """
    def __init__(self, db_file="/db/NetMonitor.db", csv="csv"):
        database_already_exists = os.path.exists(db_file)
        # Si no existe crea la basededatos y las tablas.
        if not database_already_exists:
            print("\nBasedatos %s no existe" % db_file)
            """ Busca primero db_file pasado cambiando .db por .sql
                Busca segundo directorio pasado en db_file /schema.sql """
            sql_file = db_file.replace(".db", ".sql")
            print("Buscando schema %s ..." % sql_file)
            if (not os.path.exists(sql_file)):
                print("schema %s no encontrado ..." % sql_file)
                sql_file = os.path.dirname(sql_file) + "/schema.sql"
                print("Buscando schema %s ..." % sql_file)
                if (not os.path.exists(sql_file)):
                    print("schema %s no encontrado ..." % sql_file)
                    print("Salimos....")
                    exit(1)
            # Schema encontrado lo leeemos
            print("Leyendo schema %s ..." % sql_file)
            try:
                f = open(sql_file)
                sql = f.read()
                self.db = sqlite3.connect(db_file)
                self.setup_table(sql)
                # Si existen ficheros *.csv en el path de la base de datos los carga
                print("Buscando ficheros %s con datos iniciales ..." % csv)
                for file in os.listdir(os.path.dirname(db_file)):
                    if file[-3:] == csv:
                        print("Existen ficheros *.%s %s ..." % (csv, file))
                        self.setup_data_from_csv(db_file)
                        break
            except IOError:
                print('No se puede abrir'), db_file

        else:
            self.db = sqlite3.connect(db_file)

    def select(self, sql, header=0):
        """ select records from the database """
        #print sql
        try:
            cursor = self.db.cursor()
            cursor.execute(sql)
            records = cursor.fetchall()
            if(header):
                records.insert(0, [description[0] for description in cursor.description])
            cursor.close()
            return records
        except sqlite3.Error as e:
            print("Error %s:" % e.args[0])
        #except Error:
        #    print("Error %s:" % Error)

    def insert(self, sql):
        """ insert a new record to database and return the new primary key """
        #print sql
        try:
            newID = 0
            cursor = self.db.cursor()
            cursor.execute(sql)
            newID = cursor.lastrowid
            self.db.commit()
            cursor.close()
            return newID
        except sqlite3.Error as e:
            print("Error %s:" % e.args[0])
        #except Error:
        #    print("Error %s:" % Error)
            return -1

    def execute(self, sql):
        """ execute any SQL statement but no return value given """
        #print sql
        try:
            cursor = self.db.cursor()
            cursor.execute(sql)
            self.db.commit()
            cursor.close()
        except sqlite3.Error as e:
            print("Error %s:" % e.args[0])
        #except Error:
        #    print("Error %s:" % Error)

    def execute_script(self, sql):
        """ execute any SQL statement but no return value given """
        #print sql
        try:
            cursor = self.db.cursor()
            cursor.executescript(sql)
            self.db.commit()
            cursor.close()
        except sqlite3.Error as e:
            print("Error %s:" % e.args[0])
        #except Error:
        #    print("Error %s:" % Error)

    def setup_table(self, sql):
        """ create the database tables """
        self.db.executescript(sql)

    def setup_data_from_csv(self, db_file="/db/NetMonitor.db"):
        """ insert data from csv files """
        # traverse the directory and process each .csv file
        for csvfile in glob.glob(os.path.join(os.path.dirname(db_file), "*.csv")):
            # remove the path and extension and use what's left as a table name
            tablename = os.path.splitext(os.path.basename(csvfile))[0]
            # indica que el csv tiene cabecera
            header = True
            with open(csvfile, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if header:
                        # gather column names from the first row of the csv
                        header = False
                        for column in row:
                            if column.lower().endswith("_id"):
                                index = "%s__%s" % (tablename, column)
                                sql = "CREATE INDEX %s on %s (%s)" % (index, tablename, column)
                                self.db.execute(sql)

                        insertsql = "INSERT INTO %s VALUES (%s)" % (tablename,
                                ", ".join(["?" for column in row]))

                        rowlen = len(row)
                    else:
                        # skip lines that don't have the right number of columns
                        if len(row) == rowlen:
                            self.db.execute(insertsql, row)

                self.db.commit()


if __name__ == '__main__':
    dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    print(dir)
    basedatos = dir + '/db/NetMonitor.db'
    print(basedatos)
    db = SqliteDatabase(basedatos)
#    records = db.select("SELECT * FROM auth")
#    print("%s\n" % [record for record in records])
#    cursor = db.cursor()
#    cursor.execute("SELECT * FROM auth")
#    result = cursor.fetchall()
#    for row in result:
#        print(row)
#        print("\n")
