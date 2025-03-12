#!/bin/bash

#!/bin/bash

# Ждем, пока CouchDB запустится
until curl -s http://couchdb:5984/_up; do
    echo "Waiting for CouchDB..."
    sleep 1
done

# Создаем системные базы данных
echo "Creating _users database..."
curl -X PUT http://admin:admin@couchdb:5984/_users

echo "Creating _replicator database..."
curl -X PUT http://admin:admin@couchdb:5984/_replicator

# Запуск тестов
python3 testing.py

# Если тесты прошли успешно, запускаем приложение
if [ $? -eq 0 ]; then
    python3 main.py
else
    echo "Tests failed, application will not start."
    exit 1
fi