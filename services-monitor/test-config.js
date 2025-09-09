// Load environment variables from .env file
require('dotenv').config();

console.log('🧪 Starting server in TEST mode...');
console.log(`📡 API Port: ${process.env.API_PORT}`);
console.log(`🗄️  Database: ${process.env.DB_SERVER}:${process.env.DB_PORT}/${process.env.DB_NAME}`);

// Start the server
require('./api/server.js');
