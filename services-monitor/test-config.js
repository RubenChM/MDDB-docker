// Load environment variables from .env file
require('dotenv').config();

// Test configuration for services-monitor API
process.env.API_PORT = process.env.API_PORT;
process.env.DB_SERVER = process.env.DB_SERVER;
process.env.DB_PORT = process.env.DB_PORT;
process.env.DB_NAME = process.env.DB_NAME;
process.env.DB_AUTH_USER = process.env.DB_AUTH_USER;
process.env.DB_AUTH_PASSWORD = process.env.DB_AUTH_PASSWORD;
process.env.DB_AUTHSOURCE = process.env.DB_AUTHSOURCE;

console.log('🧪 Starting server in TEST mode...');
console.log(`📡 API Port: ${process.env.API_PORT}`);
console.log(`🗄️  Database: ${process.env.DB_SERVER}:${process.env.DB_PORT}/${process.env.DB_NAME}`);

// Start the server
require('./api/server.js');
