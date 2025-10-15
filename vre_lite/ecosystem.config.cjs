module.exports = {
  apps: [
    {
      name: 'mddb-vre',
      port: '3001',
      //exec_mode: 'cluster',
      //instances: 'max',
      instances: 1,
      env: {
	      NODE_ENV: 'production'
      },
      script: './.output/server/index.mjs'
    }
  ]
}