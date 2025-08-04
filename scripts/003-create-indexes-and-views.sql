-- Create additional indexes for better performance
CREATE INDEX IF NOT EXISTS idx_messages_timestamp_desc ON node_messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_connections_status ON node_connections(status);
CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);
CREATE INDEX IF NOT EXISTS idx_domains_status ON ros_domains(agent_status);

-- Create useful views for common queries
CREATE OR REPLACE VIEW active_nodes_with_domains AS
SELECT 
    n.*,
    d.name as domain_name,
    d.agent_status as domain_status
FROM nodes n
JOIN ros_domains d ON n.domain_id = d.id
WHERE n.status = 'active' AND d.agent_status = 'active';

CREATE OR REPLACE VIEW connection_summary AS
SELECT 
    nc.*,
    sn.name as source_node_name,
    tn.name as target_node_name,
    sd.name as source_domain_name,
    td.name as target_domain_name,
    sn.node_type as source_node_type,
    tn.node_type as target_node_type
FROM node_connections nc
JOIN nodes sn ON nc.source_node_id = sn.id
JOIN nodes tn ON nc.target_node_id = tn.id
JOIN ros_domains sd ON sn.domain_id = sd.id
JOIN ros_domains td ON tn.domain_id = td.id;

CREATE OR REPLACE VIEW recent_messages AS
SELECT 
    nm.*,
    nc.source_node_id,
    nc.target_node_id,
    sn.name as source_node_name,
    tn.name as target_node_name
FROM node_messages nm
JOIN node_connections nc ON nm.connection_id = nc.id
JOIN nodes sn ON nc.source_node_id = sn.id
JOIN nodes tn ON nc.target_node_id = tn.id
WHERE nm.timestamp > NOW() - INTERVAL '1 hour'
ORDER BY nm.timestamp DESC;

-- Create a function to get domain statistics
CREATE OR REPLACE FUNCTION get_domain_stats(domain_id_param INTEGER)
RETURNS TABLE(
    total_nodes INTEGER,
    active_nodes INTEGER,
    total_connections INTEGER,
    active_connections INTEGER,
    recent_messages INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*)::INTEGER FROM nodes WHERE domain_id = domain_id_param),
        (SELECT COUNT(*)::INTEGER FROM nodes WHERE domain_id = domain_id_param AND status = 'active'),
        (SELECT COUNT(*)::INTEGER FROM node_connections nc 
         JOIN nodes sn ON nc.source_node_id = sn.id 
         WHERE sn.domain_id = domain_id_param),
        (SELECT COUNT(*)::INTEGER FROM node_connections nc 
         JOIN nodes sn ON nc.source_node_id = sn.id 
         WHERE sn.domain_id = domain_id_param AND nc.status = 'active'),
        (SELECT COUNT(*)::INTEGER FROM node_messages nm
         JOIN node_connections nc ON nm.connection_id = nc.id
         JOIN nodes sn ON nc.source_node_id = sn.id
         WHERE sn.domain_id = domain_id_param AND nm.timestamp > NOW() - INTERVAL '1 hour');
END;
$$ LANGUAGE plpgsql;
