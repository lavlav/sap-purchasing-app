#!/bin/bash

/opt/mssql/bin/sqlservr &

echo "Waiting for SQL Server to start..."
sleep 12

echo "Running seed.sql..."
/opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'Mock^Database' -i /db-init/seed.sql

#echo "Running test_data.sql..."
#/opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'Mock^Database' -i /db-init/test_data.sql

wait