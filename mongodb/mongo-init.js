// Helper function to create user only if it doesn't exist
function createUserIfNotExists(database, username, password, roles) {
  try {
    const existingUser = database.getUser(username);
    if (existingUser) {
      print(`User '${username}' already exists in database '${database.getName()}', skipping creation.`);
      return false;
    }
  } catch (e) {
    // User doesn't exist, continue with creation
  }
  
  try {
    database.createUser({
      user: username,
      pwd: password,
      roles: roles
    });
    print(`Successfully created user '${username}' in database '${database.getName()}'.`);
    return true;
  } catch (e) {
    print(`Error creating user '${username}' in database '${database.getName()}': ${e.message}`);
    // Continue execution even if user creation fails
    return false;
  }
}

// Switch to the main database
db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE);

// Create a user with readWrite permissions on <MONGO_INITDB_DATABASE> database. This user will be used for the loader
createUserIfNotExists(
  db,
  process.env.LOADER_DB_LOGIN,
  process.env.LOADER_DB_PASSWORD,
  [{ role: 'readWrite', db: process.env.MONGO_INITDB_DATABASE }]
);

// Create a user with read permissions on <MONGO_INITDB_DATABASE> database. This user will be used for the REST API
createUserIfNotExists(
  db,
  process.env.REST_DB_LOGIN,
  process.env.REST_DB_PASSWORD,
  [{ role: 'read', db: process.env.MONGO_INITDB_DATABASE }]
);

// Switch to the VRE Lite database
db = db.getSiblingDB(process.env.VRE_LITE_MONGO_DATABASE);

// Create a user with readWrite permissions on <VRE_LITE_MONGO_DATABASE> database. This user will be used for the VRE
createUserIfNotExists(
  db,
  process.env.VRE_LITE_DB_LOGIN,
  process.env.VRE_LITE_DB_PASSWORD,
  [{ role: 'readWrite', db: process.env.VRE_LITE_MONGO_DATABASE }]
);

print('Database initialization completed.');