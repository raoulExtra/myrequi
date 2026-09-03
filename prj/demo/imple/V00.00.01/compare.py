def init_db(db_path):
    return 'initialized db'

def load_graph(db_path, graph_file):
    if graph_file:
        return 'loaded graph'
    else:
        return 'missing graph'

def export_graph(db_path, graph_id, out_file):
    return 'exported graph'

def compare_graph(db_path, graph_id, json_file):
    return 'comparison result'

def run_algorithm(db_path, graph_id, algo, start, goal):
    return 'path result'

def list_graphs(db_path, graph_id):
    return 'graph list'

def parse_cli(argv):
    return 'parsed cli'

def main(argv):
    if argv:
        print('graph tool')
    else:
        return 0
