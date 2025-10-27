// init-mongo.js
print("=== Инициализация MongoDB ===");

try {
  // Подключаемся к admin
  const adminDB = db.getSiblingDB('admin');

  // Создаём rootuser (если нет)
  if (!adminDB.getUser("rootuser")) {
    adminDB.createUser({
      user: "rootuser",
      pwd: "rootpassword",
      roles: [ { role: "root", db: "admin" } ]
    });
    print("rootuser создан");
  } else {
    print("rootuser уже существует");
  }

  // Переключаемся на mydb
  const mydb = db.getSiblingDB('mydb');

  // Создаём appuser с правами readWrite
  if (!mydb.getUser("appuser")) {
    mydb.createUser({
      user: "appuser",
      pwd: "apppassword",
      roles: [ { role: "readWrite", db: "mydb" } ]
    });
    print("appuser создан");
  } else {
    print("appuser уже существует");
  }

  // Создаём коллекцию documents (если нет)
  if (!mydb.getCollectionNames().includes("documents")) {
    mydb.createCollection("documents");
    print("Коллекция 'documents' создана");
  }

  // Добавляем тестовый документ
  if (mydb.documents.countDocuments({ filename: "test.pdf" }) === 0) {
    mydb.documents.insertOne({
      filename: "test.pdf",
      uploaded_at: new Date(),
      size: 1024,
      contentType: "application/pdf",
      metadata: {
        appointment_id: null
      }
    });
    print("test.pdf добавлен");
  } else {
    print("test.pdf уже существует");
  }

  print("=== Инициализация завершена успешно ===");
} catch (error) {
  print("ОШИБКА: " + error);
  throw error;
}