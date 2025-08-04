-- Create ROS Domains table
CREATE TABLE IF NOT EXISTS ros_domains (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    agent_status VARCHAR(50) DEFAULT 'inactive',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Nodes table
CREATE TABLE IF NOT EXISTS nodes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain_id INTEGER REFERENCES ros_domains(id) ON DELETE CASCADE,
    node_type VARCHAR(50) NOT NULL, -- 'topic', 'service', 'action'
    status VARCHAR(50) DEFAULT 'inactive',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, domain_id)
);

-- Create Node Connections table
CREATE TABLE IF NOT EXISTS node_connections (
    id SERIAL PRIMARY KEY,
    source_node_id INTEGER REFERENCES nodes(id) ON DELETE CASCADE,
    target_node_id INTEGER REFERENCES nodes(id) ON DELETE CASCADE,
    connection_type VARCHAR(50) NOT NULL, -- 'publisher', 'subscriber', 'client', 'server'
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_node_id, target_node_id, connection_type)
);

-- Create Messages table for message logging
CREATE TABLE IF NOT EXISTS node_messages (
    id SERIAL PRIMARY KEY,
    connection_id INTEGER REFERENCES node_connections(id) ON DELETE CASCADE,
    message_type VARCHAR(100),
    payload JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_nodes_domain_id ON nodes(domain_id);
CREATE INDEX IF NOT EXISTS idx_connections_source ON node_connections(source_node_id);
CREATE INDEX IF NOT EXISTS idx_connections_target ON node_connections(target_node_id);
CREATE INDEX IF NOT EXISTS idx_messages_connection ON node_messages(connection_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON node_messages(timestamp);
