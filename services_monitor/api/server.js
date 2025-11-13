// Load environment variables from .env file
require('dotenv').config();

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const { MongoClient } = require('mongodb');

const app = express();
const PORT = process.env.API_PORT;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Authentication middleware for non-GET requests
const authenticateAPIKey = (req, res, next) => {
    // Skip authentication for GET requests
    if (req.method === 'GET') {
        return next();
    }

    const apiKey = req.headers['x-api-key'] || req.headers['authorization']?.replace('Bearer ', '');
    const validApiKey = process.env.API_KEY;

    if (!validApiKey) {
        console.warn('API_KEY not configured in environment variables');
        return res.status(500).json({
            success: false,
            error: 'Server configuration error'
        });
    }

    if (!apiKey) {
        return res.status(401).json({
            success: false,
            error: 'Authentication required for this operation',
            hint: 'Include X-API-Key header or Authorization: Bearer <key>'
        });
    }

    if (apiKey !== validApiKey) {
        return res.status(403).json({
            success: false,
            error: 'Invalid API key'
        });
    }

    next();
};

// Apply authentication middleware
app.use(authenticateAPIKey);

// MongoDB connection
let db;
let client;

async function connectToDatabase() {
    try {
        const dbServer = process.env.DB_SERVER;
        const dbPort = process.env.DB_PORT;
        const dbName = process.env.DB_NAME;
        const dbUser = process.env.DB_AUTH_USER;
        const dbPassword = process.env.DB_AUTH_PASSWORD;
        const dbAuthSource = process.env.DB_AUTHSOURCE;

        let connectionString;
        if (dbUser && dbPassword) {
            connectionString = `mongodb://${dbUser}:${dbPassword}@${dbServer}:${dbPort}/${dbName}?authSource=${dbAuthSource}`;
        } else {
            connectionString = `mongodb://${dbServer}:${dbPort}/${dbName}`;
        }

        client = new MongoClient(connectionString);
        await client.connect();
        db = client.db(dbName);
        
        console.log(`Connected to MongoDB at ${dbServer}:${dbPort}`);
    } catch (error) {
        console.error('Failed to connect to MongoDB:', error);
        process.exit(1);
    }
}

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        service: 'services-monitor-api'
    });
});

// Health check endpoint with api key authentication
app.post('/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        service: 'services-monitor-api'
    });
});

// Get all sites
app.get('/api/sites', async (req, res) => {
    try {
        const sites = await db.collection('data_collection_sites').find({}).toArray();
        res.json({
            success: true,
            data: sites,
            count: sites.length
        });
    } catch (error) {
        console.error('Error fetching sites:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to fetch sites'
        });
    }
});

// Get site by node
app.get('/api/sites/:node', async (req, res) => {
    try {
        const { node } = req.params;

        const site = await db.collection('data_collection_sites').findOne({ node });

        if (!site) {
            return res.status(404).json({
                success: false,
                error: 'Site not found'
            });
        }

        res.json({
            success: true,
            data: site
        });
    } catch (error) {
        console.error('Error fetching site:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to fetch site'
        });
    }
});

// Create new site
app.post('/api/sites', async (req, res) => {
    try {
        const { node, name, url, active } = req.body;

        // Basic validation
        if (!node || !url) {
            return res.status(400).json({
                success: false,
                error: 'Node and URL are required'
            });
        }

        // Check if node already exists
        const existingNode = await db.collection('data_collection_sites').findOne({ node });
        if (existingNode) {
            return res.status(409).json({
                success: false,
                error: 'Node already exists, use /api/sites/:id to update it'
            });
        }

        const siteData = {
            node,
            name: name || '',
            url,
            active: active !== undefined ? active : true,
            created_at: new Date(),
            updated_at: new Date()
        };

        const result = await db.collection('data_collection_sites').insertOne(siteData);
        
        res.status(201).json({
            success: true,
            data: { ...siteData, _id: result.insertedId },
            message: 'Site created successfully'
        });
    } catch (error) {
        console.error('Error creating site:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to create site'
        });
    }
});

// Update site
app.put('/api/sites/:node', async (req, res) => {
    try {
        const { node } = req.params;
        const updateData = req.body;

        if (updateData.node && updateData.node !== node) {
            return res.status(400).json({
                success: false,
                error: 'Node field must match the URL parameter and cannot be changed'
            });
        }

        if (!updateData || Object.keys(updateData).length === 0) {
            return res.status(400).json({
                success: false,
                error: 'No data provided for update'
            });
        }

        // Remove immutable fields
        delete updateData._id;
        delete updateData.created_at;
        delete updateData.updated_at;

        // Add updated timestamp
        updateData.updated_at = new Date();

        const result = await db.collection('data_collection_sites').updateOne(
            { node },
            { $set: updateData }
        );

        if (result.matchedCount === 0) {
            return res.status(404).json({
                success: false,
                error: 'Site not found'
            });
        }

        res.json({
            success: true,
            message: 'Site updated successfully'
        });
    } catch (error) {
        console.error('Error updating site:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to update site'
        });
    }
});

// Delete site
app.delete('/api/sites/:node', async (req, res) => {
    try {
        const { node } = req.params;

        const result = await db.collection('data_collection_sites').deleteOne({ node: node });

        if (result.deletedCount === 0) {
            return res.status(404).json({
                success: false,
                error: 'Site not found'
            });
        }

        res.json({
            success: true,
            message: 'Site deleted successfully'
        });
    } catch (error) {
        console.error('Error deleting site:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to delete site'
        });
    }
});

// Get collected data
app.get('/api/data', async (req, res) => {
    try {
        const { 
            page = 1, 
            limit = 50, 
            node, 
            success, 
            start_date, 
            end_date,
            active, 
            latest 
        } = req.query;

        const skip = (page - 1) * limit;
        
        // Build query for collected data
        const query = {};

        console.log('Active filter:', active);

        // Only filter by active sites if 'active' parameter is provided
        if (active !== undefined) {
            const activeFilter = active === 'true';
            
            // Get site IDs based on active status
            const sites = await db.collection('data_collection_sites')
                .find({ active: activeFilter })
                .project({ node: 1 })
                .toArray();
            
            const siteIds = sites.map(site => site.node.toString());
            query.node = { $in: siteIds };
        }

        // Apply node filter
        if (node) {
            if (active !== undefined) {
                // If active filter is applied, check if the node matches the filter
                const sites = await db.collection('data_collection_sites')
                    .find({ active: active === 'true' })
                    .project({ node: 1 })
                    .toArray();
                
                const siteIds = sites.map(site => site.node.toString());
                
                if (siteIds.includes(node)) {
                    query.node = node;
                } else {
                    // Return empty result if requesting node that doesn't match active filter
                    return res.json({
                        success: true,
                        data: [],
                        pagination: {
                            page: parseInt(page),
                            limit: parseInt(limit),
                            total: 0,
                            pages: 0
                        }
                    });
                }
            } else {
                // No active filter, just filter by node
                query.node = node;
            }
        }

        if (success !== undefined) {
            query.success = success === 'true';
        }

        if (start_date || end_date) {
            query.timestamp = {};
            if (start_date) {
                query.timestamp.$gte = new Date(start_date);
            }
            if (end_date) {
                query.timestamp.$lte = new Date(end_date);
            }
        }

        // If 'latest' parameter is true, get only the latest entry per node
        if (latest === 'true') {
            // Get latest entry per node
            const latestData = await db.collection('collected_data').aggregate([
                { $sort: { timestamp: -1 } },
                {
                    $group: {
                        _id: '$node',
                        doc: { $first: '$$ROOT' }
                    }
                },
                { $replaceRoot: { newRoot: '$doc' } },
                { $skip: skip },
                { $limit: parseInt(limit) }
            ]).toArray();

            const totalCount = await db.collection('collected_data').distinct('node', query);
            
            return res.json({
                success: true,
                data: latestData,
                pagination: {
                    page: parseInt(page),
                    limit: parseInt(limit),
                    total: totalCount.length,
                    pages: Math.ceil(totalCount.length / limit)
                }
            });
        }

        const [data, totalCount] = await Promise.all([
            db.collection('collected_data')
                .find(query)
                .sort({ timestamp: -1 })
                .skip(parseInt(skip))
                .limit(parseInt(limit))
                .toArray(),
            db.collection('collected_data').countDocuments(query)
        ]);

        res.json({
            success: true,
            data,
            pagination: {
                page: parseInt(page),
                limit: parseInt(limit),
                total: totalCount,
                pages: Math.ceil(totalCount / limit)
            }
        });
    } catch (error) {
        console.error('Error fetching collected data:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to fetch collected data'
        });
    }
});

// Toggle site active status
app.patch('/api/sites/:node/toggle', async (req, res) => {
    try {
        const { node } = req.params;

        const site = await db.collection('data_collection_sites').findOne({ node });
        
        if (!site) {
            return res.status(404).json({
                success: false,
                error: 'Site not found'
            });
        }

        const newActiveStatus = !site.active;
        
        await db.collection('data_collection_sites').updateOne(
            { node },
            { 
                $set: { 
                    active: newActiveStatus,
                    updated_at: new Date()
                } 
            }
        );

        res.json({
            success: true,
            data: { active: newActiveStatus },
            message: `Site ${newActiveStatus ? 'activated' : 'deactivated'} successfully`
        });
    } catch (error) {
        console.error('Error toggling site status:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to toggle site status'
        });
    }
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({
        success: false,
        error: 'Internal server error'
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        success: false,
        error: 'Endpoint not found'
    });
});

// Start server
async function startServer() {
    await connectToDatabase();
    
    app.listen(PORT, '0.0.0.0', () => {
        console.log(`Data Collector API server is running on port ${PORT}`);
    });
}

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('Shutting down gracefully...');
    if (client) {
        await client.close();
    }
    process.exit(0);
});

startServer().catch(console.error);
