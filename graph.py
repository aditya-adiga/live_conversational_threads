def draw_graph(output_file):
    import json
    import networkx as nx
    import matplotlib.pyplot as plt

    class Node:
        def __init__(self, node_name, node_type, predecessor, successor, related_nodes, relationship_strength, summary):
            self.node_name = node_name
            self.node_type = node_type  
            self.predecessor = predecessor
            self.successor = successor
            self.related_nodes = related_nodes
            self.relationship_strength = relationship_strength
            self.summary = summary
        
        def __repr__(self):
            return f"Node({self.node_name}, {self.node_type}, {self.predecessor}, {self.successor}, {self.related_nodes}, {self.relationship_strength}, {self.summary})"

    with open(output_file, 'r') as llm_output:
        data = json.load(llm_output)

    for node in data:
        if "type" in node:
            node["node_type"] = node.pop("type")


    nodes = [Node(**node) for node in data]

    #for node in nodes:
    #    print(node)

    G = nx.DiGraph()


    for node in nodes:
        G.add_node(node.node_name, node_type=node.node_type)

    strength_to_color = {
        'bookmark': 'purple',
        'weak': 'green',
        'moderate': 'yellow',
        'strong': 'red'
    }

    for node in nodes:
        if node.successor:
            G.add_edge(node.node_name, node.successor, color='black')

    for node in nodes:
        for related_node in node.related_nodes:
            strength = node.relationship_strength.get(related_node)  
            G.add_edge(node.node_name, related_node, color=strength_to_color.get(strength))

    edge_colors = [G[u][v]['color'] for u, v in G.edges()]

    node_color_map = {'conversational_thread': 'black', 'bookmark': 'red'}
    node_colors = [node_color_map.get(G.nodes[node]['node_type']) for node in G.nodes()]

    def offset_labels(pos, x_shift=0.05, y_shift=0.05):
        pos_labels = {}
        for key, (x, y) in pos.items():
            pos_labels[key] = (x + x_shift, y + y_shift)
        return pos_labels


    pos = nx.spring_layout(G, k=1.0)
    pos_labels = offset_labels(pos, x_shift=0.1, y_shift=0.1) 

    plt.figure(figsize=(12, 12))
    nx.draw(G, pos, node_color=node_colors, edge_color=edge_colors, with_labels=False, node_size=500, arrows=True)
    nx.draw_networkx_labels(G, pos_labels, font_color='black', font_weight='bold')

    plt.savefig("graph.svg", format="svg")

    #plt.show()